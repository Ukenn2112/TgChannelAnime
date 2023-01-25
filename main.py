# !/usr/bin/env python3
import asyncio
import asyncio.subprocess
import base64
import json
import logging
import re
import os
import shutil
import urllib.parse

from telebot.async_telebot import AsyncTeleBot
from telethon import TelegramClient, events

import utils.global_vars as global_vars
from bot import bot_register
from utils.download import download
from utils.bgm_nfo import subject_nfo, episode_nfo, subject_name

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(
    format="[%(levelname)s]%(asctime)s: %(message)s",
    handlers=[
        logging.FileHandler("data/run.log", encoding="UTF-8"),
        logging.StreamHandler(),
    ],
)

queue: asyncio.Queue = global_vars.queue

chi_to_num = {
    "一": "01",
    "二": "02",
    "三": "03",
    "四": "04",
    "五": "05",
    "六": "06",
    "七": "07",
    "八": "08",
    "九": "09",
    "十": "10",
}

async def worker(name):
    while True:
        queue_item = await queue.get()
        url = queue_item[0]

        season_name: str = queue_item[1]
        file_type = queue_item[2]
        volume = queue_item[3]
        platform = queue_item[4]
        bgm_id = queue_item[5]
        tmdb_d = None
        if len(queue_item) == 7:
            tmdb_d = queue_item[6]

        season = re.search(r"第(.*)季", season_name)
        if season:
            season_name = season_name.replace(season.group(0), "").strip()
        file_name = f"{season_name} - S01E{volume} - {platform}"
        if not os.path.exists(file_name): os.mkdir(file_name)

        folder_name = subject_name(bgm_id)
        season = re.search(r"Season(.*)", season_name)
        if season:
            folder_name = folder_name.replace(season.group(0), "").strip()

        episode_data = episode_nfo(bgm_id, volume)
        if episode_data:
            with open(f"{global_vars.config['save_path']}/{file_name}/{file_name}.nfo", "w", encoding="utf-8") as f:
                f.write(episode_data)
                f.close()
        try:
            proc = await asyncio.create_subprocess_exec(
                "rclone", "lsjson", f"{global_vars.config['rclone_config_name']}:NC-Raws", "--dirs-only",
                stdout=asyncio.subprocess.PIPE)
            output = await proc.communicate()
            dirs_list = json.loads(output[0].decode("utf-8"))
            dirs = [dirs["Name"] for dirs in dirs_list if folder_name in dirs["Name"]]
            if not dirs:
                subject_data = subject_nfo(bgm_id, tmdb_d)
                with open(f"{global_vars.config['save_path']}/{file_name}/tvshow.nfo", "w", encoding="utf-8") as t:
                    t.write(subject_data['tvshowNfo'])
                    t.close()
                with open(f"{global_vars.config['save_path']}/{file_name}/season.nfo", "w", encoding="utf-8") as s:
                    s.write(subject_data['seasonNfo'])
                    s.close()
                with open(f"{global_vars.config['save_path']}/{file_name}/poster.{subject_data['posterImg'][1]}", "wb") as f:
                    f.write(subject_data['posterImg'][0])
                    f.close()
                with open(f"{global_vars.config['save_path']}/{file_name}/fanart.{subject_data['fanartImg'][1]}", "wb") as f:
                    f.write(subject_data['fanartImg'][0])
                    f.close()
                if subject_data['clearlogoImg']:
                    with open(f"{global_vars.config['save_path']}/{file_name}/clearlogo.{subject_data['clearlogoImg'][1]}", "wb") as f:
                        f.write(subject_data['clearlogoImg'][0])
                        f.close()
        except Exception as e:
            pass
        try:
            logging.info(f"[file_name: {file_name}] - 开始下载")
            download(url, f"{global_vars.config['save_path']}/{file_name}/{file_name}.{file_type}")

            logging.info(f"[file_name: {file_name}] - 开始上传")
            proc = await asyncio.create_subprocess_exec(
                "rclone", "move", f"{global_vars.config['save_path']}/{file_name}/",
               f"{global_vars.config['rclone_config_name']}:NC-Raws/{folder_name}/",
                "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
            await proc.wait()
            if proc.returncode == 0:
                await bot.send_message(global_vars.config["notice_chat"], f"[#更新提醒]\n - 已上传: {file_name}")
                logging.info(f"[file_name: {file_name}] - 已下载并上传成功")
        except Exception as e:
            logging.error(f"[file_name: {file_name}] - 下载或上传失败: {e}")
        finally:
            shutil.rmtree(f"{global_vars.config['save_path']}/{file_name}")
            queue.task_done()


@events.register(events.NewMessage(chats=global_vars.config["nc_chat_id"]))
async def nc_chat_detecting(update):
    message = update.message
    if message.file and "video" in message.file.mime_type:
        url = re.search(r"\[线上观看&下载\]\((https?:\/\/[^)]+)\)", message.text)
        bgm_id = re.search(r"\[\*\*bangumi\.tv\]\(https?:\/\/bgm\.tv\/subject\/([0-9]+)\)", message.text)
        if not url and not bgm_id: return logging.error(f"[message_id: {message.id}] - 无法解析的消息")

        url = "https://nc.raws.dev" + base64.b64decode(url.group(1).split("/")[-1].replace("_", "/").replace("-", "+")).decode("utf-8")
        bgm_id = bgm_id.group(1)
        tmdb_d = re.search(r"https?:\/\/www\.themoviedb\.org\/((tv|movie)\/[0-9]+)", message.text)
        if tmdb_d: tmdb_d = tmdb_d.group(1)
        file_name = url.split("/")[-1]
        file_type = file_name.split(".")[-1]
        data = re.search(r"\[NC-Raws\] (.+) - (.+) \((.+) ([0-9]+x[0-9]+).+\)", file_name)
        season_name = data.group(1)
        volume = data.group(2)
        platform = data.group(3)

        tag_name = re.search(r"\n\n#(.+)\n\n", message.text).group(1)
        for bid in global_vars.config["bgm_compare"]:
            if bid["tagname"] == tag_name:
                bgm_id = bid["bgmid"]
                break
        if platform == "Baha":
            if tag_name in global_vars.config["Baha_blacklist"]:
                return
        elif platform == "B-Global Donghua" or platform == "B-Global":
            if tag_name not in global_vars.config["B_Global_whitelist"]:
                return
        elif platform == "CR":
            if tag_name not in global_vars.config["CR_whitelist"]:
                return
        elif platform == "Sentai":
            if tag_name not in global_vars.config["Sentai_whitelist"]:
                return
        else:
            return logging.error(f"[file_name: {file_name}] - 未知平台: {platform}")
        url = urllib.parse.quote(url, safe=":/?&=").replace("mkv", "zip").replace("mp4", "zip")
        await queue.put((url, season_name, file_type, volume, platform, bgm_id, tmdb_d))


@events.register(events.NewMessage(chats=global_vars.config["ani_chat_id"]))
async def ani_chat_detecting(update):
    message = update.message
    if message.file and "video" in message.file.mime_type:
        url = re.search(r"【下載連結】: \[按我\]\((https?:\/\/[^)]+)\)", message.text)
        if not url: return logging.error(f"[message_id: {message.id}] - 无法解析的消息")

        url = url.group(1)
        file_name = re.search(r"【番名】: (.*)", message.text).group(1)
        file_type = file_name.split(".")[-1].replace("?d=true", "")
        data = re.search(r"\[ANi\] (.+) - (.+) \[.+\]\[(.+)\]\[.+\]\[.+\]\[.+\]\..+", file_name)
        season_name = data.group(1).replace("（僅限港澳台地區）", "")
        volume = data.group(2)
        platform = data.group(3)

        tag_name = re.search(r"#新番更新  #(.*)", message.text).group(1)
        bgm_id = None
        if platform != "Bilibili": return
        for w in global_vars.config["Bilibili_whitelist"]:
            if w['tagname'] == tag_name:
                bgm_id = w['bgmid']
                break
        if not bgm_id: return
        url = urllib.parse.quote(url, safe=":/?&=").replace("mkv", "zip").replace("mp4", "zip")
        await queue.put((url, season_name, file_type, volume, platform, bgm_id))


if __name__ == "__main__":
    bot = AsyncTeleBot(global_vars.config["bot_token"])
    bot_register(bot)
    client = TelegramClient("data/channel_downloader", global_vars.config["api_id"], global_vars.config["api_hash"]).start()
    client.add_event_handler(nc_chat_detecting)
    client.add_event_handler(ani_chat_detecting)
    tasks = []
    try:
        loop = asyncio.get_event_loop()
        task = loop.create_task(bot.polling(non_stop=True))
        tasks.append(task)
        for i in range(global_vars.config["max_num"]):
            loop = asyncio.get_event_loop()
            task = loop.create_task(worker(f"worker-{i}"))
            tasks.append(task)
        print("已启动 (按 Ctrl+C 停止)")
        client.run_until_disconnected()
    finally:
        for task in tasks:
            task.cancel()
        client.disconnect()
        print("已停止")