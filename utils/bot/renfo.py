import asyncio
import os
import re
import shutil
import json

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from utils.bgm_nfo import save_nfo, subject_name, subject_nfo, episode_nfo
from utils.global_vars import config


async def re_subject_nfo(message: Message, bot: AsyncTeleBot):
    data = message.text.split(" ")
    if len(data) <= 1:
        return await bot.reply_to(message, "参数错误")
    elif not data[1].isdecimal():
        return await bot.reply_to(message, "参数错误")
    bgm_id = data[1]
    tmdb_id, tmdb_type = None, None
    if len(data) > 3:
        tmdb_id = data[2]
        tmdb_type = data[3]
    msg = await bot.reply_to(message, "收到重新生成 NFO 请求，开始处理...")
    up_folder_name = subject_name(bgm_id)
    season = re.search(r"Season(.*)", up_folder_name)
    if season: up_folder_name = up_folder_name.replace(season.group(0), "").strip()
    worker_path = f"{config['save_path']}{up_folder_name}_nfo"
    if not os.path.exists(worker_path): os.mkdir(worker_path)
    # 生成 Season NFO
    if tmdb_id and tmdb_type:
        try:
            subject_data = subject_nfo(bgm_id, tmdb_type + '/' + tmdb_id)
            save_nfo(worker_path, subject_data=subject_data)
        except Exception as e:
            return await bot.reply_to(message, f"获取生成 Season NFO 数据失败:\n\n{e}")
        await bot.edit_message_text("已生成 Season NFO 文件，正在开始生成 Episode NFO...", message.chat.id, msg.message_id)
    try:
        proc = await asyncio.create_subprocess_exec(
            "rclone", "lsjson", f"{config['rclone_config_name']}:NC-Raws/{up_folder_name}",
            stdout=asyncio.subprocess.PIPE)
        output = await proc.communicate()
        dirs_list = [i['Name'] for i in json.loads(output[0].decode("utf-8")) if 'video' in i['MimeType']]
    except:
        return await bot.reply_to(message, f"获取文件列表失败: 未找到文件夹 {up_folder_name}")
    if dirs_list:
        for video in dirs_list:
            try:
                episode_data = episode_nfo(bgm_id, int(video.split(' - ')[1].split('E')[1]))
                save_nfo(worker_path, episode_data=episode_data, video_name=video.split('.')[0])
            except Exception as e:
                return await bot.reply_to(message, f"读取文件列表失败: 获取生成 Episode NFO 数据出错或命名错误\n\n{e}")
        await bot.edit_message_text(f"已生成 Episode NFO 文件，正在开始上传...", message.chat.id, msg.message_id)
    else:
        return await bot.reply_to(message, f"获取文件列表失败: 未找到 {up_folder_name} 文件夹下的视频文件")
    try:
        proc = await asyncio.create_subprocess_exec(
            "rclone", "move", worker_path,
            f"{config['rclone_config_name']}:NC-Raws/{up_folder_name}/",
            "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
        await proc.wait()
        if proc.returncode == 0:
             await bot.edit_message_text(f"已生成并上传成功", message.chat.id, msg.message_id)
    except Exception as e:
        await bot.reply_to(message, f"上传失败: {e}")
    finally:
        shutil.rmtree(worker_path)