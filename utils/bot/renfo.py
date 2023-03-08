import asyncio
import json
import logging
import os
import re
import shutil

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from utils.bgm_nfo import episode_nfo, save_nfo, subject_name, subject_nfo
from utils.global_vars import config, sql
from utils.num_format import volume_format


async def re_subject_nfo(message: Message, bot: AsyncTeleBot):
    data = message.text.split(" ")
    todo_list = []
    if len(data) <= 1:
        return await bot.reply_to(message, "参数错误")
    elif data[1] == "all":
        todo_list = sql.inquiry_all_season()
    elif data[1].isdecimal():
        bgm_id = data[1]
        tmdb_d = f"{data[3]}/{data[2]}" if len(data) > 3 else None
        up_folder_name = subject_name(bgm_id)
        season = re.search(r"Season(.*)", up_folder_name)
        if season: up_folder_name = up_folder_name.replace(season.group(0), "").strip()
        todo_list.append((bgm_id, tmdb_d, up_folder_name))
    else:
        return await bot.reply_to(message, "参数错误")
    todo_num = len(todo_list)
    logging.info(f"[Bot] 收到来自 {message.from_user.id} 的重新生成 NFO 请求 共{todo_num}个")
    msg = await bot.reply_to(message, f"[{todo_num}] 收到重新生成 NFO 请求，开始处理...")
    for i, (bgm_id, tmdb_d, up_folder_name) in enumerate(todo_list):
        await bot.edit_message_text(f"[{i+1}/{todo_num}] 正在处理 {up_folder_name}...", message.chat.id, msg.message_id)
        worker_path = f"{config['save_path']}{up_folder_name}_nfo"
        if not os.path.exists(worker_path): os.mkdir(worker_path)
        # 生成 Season NFO
        if tmdb_d and tmdb_d != "None":
            try:
                subject_data = subject_nfo(bgm_id, tmdb_d)
                save_nfo(worker_path, subject_data=subject_data)
            except Exception as e:
                await bot.reply_to(message, f"[{i+1}/{todo_num}] {bgm_id}:{tmdb_d} 获取生成 Season NFO 数据失败:\n\n{e}")
                continue
            await bot.edit_message_text(f"[{i+1}/{todo_num}] 已生成 Season NFO 文件，正在开始生成 Episode NFO...", message.chat.id, msg.message_id)
        try:
            proc = await asyncio.create_subprocess_exec(
                "rclone", "lsjson", f"{config['rclone_config_name']}:NC-Raws/{up_folder_name}",
                stdout=asyncio.subprocess.PIPE)
            output = await proc.communicate()
            dirs_list = [i['Name'] for i in json.loads(output[0].decode("utf-8")) if 'video' in i['MimeType']]
        except:
            await bot.reply_to(message, f"[{i+1}/{todo_num}] {bgm_id}:{tmdb_d} 获取文件列表失败: 未找到文件夹 {up_folder_name}")
            continue
        if dirs_list:
            for video in dirs_list:
                try:
                    volume = await volume_format(video.split(' - ')[1].split('E')[1])
                    if isinstance(volume, int):
                        episode_type: int = 0
                    elif isinstance(volume, float):
                        episode_type: float = 1
                    episode_data = episode_nfo(bgm_id, volume, episode_type)
                    save_nfo(worker_path, episode_data=episode_data, video_name=video.split('.')[0])
                except Exception as e:
                    await bot.reply_to(message, f"[{i+1}/{todo_num}] {bgm_id}:{tmdb_d} 读取文件列表失败: 获取生成 Episode NFO 数据出错或命名错误\n\n{e}")
                    continue
            await bot.edit_message_text(f"[{i+1}/{todo_num}] 已生成 Episode NFO 文件，正在开始上传...", message.chat.id, msg.message_id)
        else:
            await bot.reply_to(message, f"[{i+1}/{todo_num}] {bgm_id}:{tmdb_d} 获取文件列表失败: 未找到 {up_folder_name} 文件夹下的视频文件")
            continue
        try:
            proc = await asyncio.create_subprocess_exec(
                "rclone", "move", worker_path,
                f"{config['rclone_config_name']}:NC-Raws/{up_folder_name}/",
                "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
            await proc.wait()
            if proc.returncode == 0:
                await bot.edit_message_text(f"[{i+1}/{todo_num}] 已生成并上传成功", message.chat.id, msg.message_id)
        except Exception as e:
            await bot.reply_to(message, f"[{i+1}/{todo_num}] {bgm_id}:{tmdb_d} 上传失败: {e}")
        finally:
            shutil.rmtree(worker_path)