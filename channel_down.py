# !/usr/bin/env python3
import asyncio
import asyncio.subprocess
import base64
import logging
import re
import urllib.parse

from telebot.async_telebot import AsyncTeleBot
from telethon import TelegramClient, events

import managing_bot
import global_vars
from download import download

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(
    format="[%(levelname)s]%(asctime)s: %(message)s",
    handlers=[
        logging.FileHandler("run.log", encoding="UTF-8"),
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


        season = re.search(r"第(.*)季", season_name)
        if season:
            season_str = "Season " + str(int(chi_to_num.get(season.group(1), "01")))
            season_num = chi_to_num.get(season.group(1), "01")
            season_name = season_name.replace(season.group(0), "").strip()
        else:
            season_str = "Season 1"
            season_num = "01"
        
        file_name = f"{season_name} - S{season_num}E{volume} - {platform}.{file_type}"
        try:
            logging.info(f"[file_name: {file_name}] - 开始下载")
            download(url, f"{global_vars.config['save_path']}/{file_name}")
            if global_vars.config["upload_file_set"]:
                logging.info(f"[file_name: {file_name}] - 开始上传")
                proc = await asyncio.create_subprocess_exec("rclone", "move", f"{global_vars.config['save_path']}/{file_name}",
                                                           f"{global_vars.config['rclone_config_name']}:NC-Raws/{season_name}/{season_str}/",
                                                            "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
                await proc.wait()
                if proc.returncode == 0:
                    await bot.send_message(global_vars.config["notice_chat"], f"[#更新提醒]\n - 已上传: {file_name}")
                    logging.info(f"[file_name: {file_name}] - 已下载并上传成功")
        except Exception as e:
            logging.error(f"[file_name: {file_name}] - 下载或上传失败: {e}")
        finally:
            queue.task_done()


@events.register(events.NewMessage(chats=global_vars.config["nc_chat_id"]))
async def nc_chat_detecting(update):
    message = update.message
    if message.file and "video" in message.file.mime_type:
        url = re.search(r"\[线上观看&下载\]\((https?:\/\/[^)]+)\)", message.text)
        if not url: return logging.error(f"[message_id: {message.id}] - 无法解析的消息")

        url = "https://nc.raws.dev" + base64.b64decode(url.group(1).split("/")[-1].replace("_", "/").replace("-", "+")).decode("utf-8")
        file_name = url.split("/")[-1]
        file_type = file_name.split(".")[-1]
        data = re.search(r"\[NC-Raws\] (.+) - (.+) \((.+) ([0-9]+x[0-9]+).+\)", file_name)
        season_name = data.group(1)
        volume = data.group(2)
        platform = data.group(3)

        tag_name = re.search(r"\n\n#(.+)\n\n", message.text).group(1)
        if platform != "Baha":
            if platform == "B-Global Donghua" or platform == "B-Global":
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
        await queue.put((url, season_name, file_type, volume, platform))

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
        if platform == "Bilibili":
            if tag_name not in global_vars.config["Bilibili_whitelist"]:
                return
        url = urllib.parse.quote(url, safe=":/?&=").replace("mkv", "zip").replace("mp4", "zip")
        await queue.put((url, season_name, file_type, volume, platform))


if __name__ == "__main__":
    bot = AsyncTeleBot(global_vars.config["bot_token"])
    managing_bot.register(bot)
    client = TelegramClient("channel_downloader", global_vars.config["api_id"], global_vars.config["api_hash"]).start()
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