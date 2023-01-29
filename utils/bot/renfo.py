import asyncio
import os
import re
import shutil
import json

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from utils.bgm_nfo import subject_name, subject_nfo, episode_nfo
from utils.global_vars import config


async def re_subject_nfo(message: Message, bot: AsyncTeleBot):
    data = message.text.split(" ")
    if len(data) < 4:
        return await bot.reply_to(message, "参数错误")
    elif not data[1].isdecimal():
        return await bot.reply_to(message, "参数错误")
    bgm_id = data[1]
    tmdb_id = data[2]
    tmdb_type = data[3]
    msg = await bot.reply_to(message, "收到重新生成 NFO 请求，开始处理...")
    folder_name = subject_name(bgm_id)
    season = re.search(r"Season(.*)", folder_name)
    if season: folder_name = folder_name.replace(season.group(0), "").strip()
    if not os.path.exists(f"{folder_name}_nfo"): os.mkdir(f"{folder_name}_nfo")
    # 生成 Season NFO
    subject_data = subject_nfo(bgm_id, tmdb_type + '/' + tmdb_id)
    with open(f"{config['save_path']}/{folder_name}_nfo/tvshow.nfo", "w", encoding="utf-8") as t:
        t.write(subject_data['tvshowNfo'])
        t.close()
    with open(f"{config['save_path']}/{folder_name}_nfo/season.nfo", "w", encoding="utf-8") as s:
        s.write(subject_data['seasonNfo'])
        s.close()
    with open(f"{config['save_path']}/{folder_name}_nfo/poster.{subject_data['posterImg'][1]}", "wb") as f:
        f.write(subject_data['posterImg'][0])
        f.close()
    with open(f"{config['save_path']}/{folder_name}_nfo/fanart.{subject_data['fanartImg'][1]}", "wb") as f:
        f.write(subject_data['fanartImg'][0])
        f.close()
    if subject_data['clearlogoImg']:
        with open(f"{config['save_path']}/{folder_name}_nfo/clearlogo.{subject_data['clearlogoImg'][1]}", "wb") as f:
            f.write(subject_data['clearlogoImg'][0])
            f.close()
    await bot.edit_message_text("已生成 Season NFO 文件，正在开始生成 Episode NFO...", message.chat.id, msg.message_id)
    try:
        proc = await asyncio.create_subprocess_exec(
            "rclone", "lsjson", f"{config['rclone_config_name']}:NC-Raws/{folder_name}",
            stdout=asyncio.subprocess.PIPE)
        output = await proc.communicate()
        dirs_list = [i['Name'] for i in json.loads(output[0].decode("utf-8")) if 'video' in i['MimeType']]
    except:
        return await bot.reply_to(message, f"获取文件列表失败: 未找到文件夹 {folder_name}")
    if dirs_list:
        for video in dirs_list:
            episode_data = episode_nfo(bgm_id, video.split(' - ')[1].split('E')[1])
            with open(f"{config['save_path']}/{folder_name}_nfo/{video.split('.')[0]}.nfo", "w", encoding="utf-8") as e:
                e.write(episode_data)
                e.close()
        await bot.edit_message_text(f"已生成 Episode NFO 文件，正在开始上传...", message.chat.id, msg.message_id)
    else:
        return await bot.reply_to(message, f"获取文件列表失败: 未找到 {folder_name} 文件夹下的视频文件")
    try:
        proc = await asyncio.create_subprocess_exec(
            "rclone", "move", f"{config['save_path']}/{folder_name}_nfo/",
            f"{config['rclone_config_name']}:NC-Raws/{folder_name}/",
            "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
        await proc.wait()
        if proc.returncode == 0:
             await bot.edit_message_text(f"已生成并上传成功", message.chat.id, msg.message_id)
    except Exception as e:
        await bot.reply_to(message, f"上传失败: {e}")
    finally:
        shutil.rmtree(f"{config['save_path']}/{folder_name}_nfo")