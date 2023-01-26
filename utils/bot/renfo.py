import asyncio
import os
import re
import shutil

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from utils.bgm_nfo import subject_name, subject_nfo
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

    folder_name = subject_name(bgm_id)
    season = re.search(r"Season(.*)", folder_name)
    if season: folder_name = folder_name.replace(season.group(0), "").strip()
    if not os.path.exists(f"{folder_name}_nfo"): os.mkdir(f"{folder_name}_nfo")

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
    try:
        proc = await asyncio.create_subprocess_exec(
            "rclone", "move", f"{config['save_path']}/{folder_name}_nfo/",
            f"{config['rclone_config_name']}:NC-Raws/{folder_name}/",
            "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
        await proc.wait()
        if proc.returncode == 0:
             await bot.reply_to(message, "已重新生成并上传")
    except Exception as e:
        await bot.reply_to(message, f"上传失败: {e}")
    finally:
        shutil.rmtree(f"{config['save_path']}/{folder_name}_nfo")