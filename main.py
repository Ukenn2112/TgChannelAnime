# !/usr/bin/env python3
import asyncio
import asyncio.subprocess
import json
import logging
import os
import re
import shutil

from telebot.async_telebot import AsyncTeleBot
from telethon import TelegramClient

from utils.bgm_nfo import episode_nfo, subject_name, subject_nfo
from utils.bot import bot_register
from utils.download import download
from utils.global_vars import config, queue
from utils.msg_events import ani_chat_detecting, nc_chat_detecting

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(
    format="[%(levelname)s]%(asctime)s: %(message)s",
    handlers=[
        logging.FileHandler("data/run.log", encoding="UTF-8"),
        logging.StreamHandler(),
    ],
)

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
        if not os.path.exists(config['save_path'] + file_name):
            os.mkdir(config['save_path'] + file_name)

        folder_name = subject_name(bgm_id)
        season = re.search(r"Season(.*)", folder_name)
        if season:
            folder_name = folder_name.replace(season.group(0), "").strip()

        episode_data = episode_nfo(bgm_id, volume)
        if episode_data:
            with open(f"{config['save_path']}/{file_name}/{file_name}.nfo", "w", encoding="utf-8") as f:
                f.write(episode_data)
                f.close()
        try:
            proc = await asyncio.create_subprocess_exec(
                "rclone", "lsjson", f"{config['rclone_config_name']}:NC-Raws", "--dirs-only",
                stdout=asyncio.subprocess.PIPE)
            output = await proc.communicate()
            dirs_list = json.loads(output[0].decode("utf-8"))
            dirs = [dirs["Name"] for dirs in dirs_list if folder_name in dirs["Name"]]
            if not dirs:
                subject_data = subject_nfo(bgm_id, tmdb_d)
                with open(f"{config['save_path']}/{file_name}/tvshow.nfo", "w", encoding="utf-8") as t:
                    t.write(subject_data['tvshowNfo'])
                    t.close()
                with open(f"{config['save_path']}/{file_name}/season.nfo", "w", encoding="utf-8") as s:
                    s.write(subject_data['seasonNfo'])
                    s.close()
                with open(f"{config['save_path']}/{file_name}/poster.{subject_data['posterImg'][1]}", "wb") as f:
                    f.write(subject_data['posterImg'][0])
                    f.close()
                with open(f"{config['save_path']}/{file_name}/fanart.{subject_data['fanartImg'][1]}", "wb") as f:
                    f.write(subject_data['fanartImg'][0])
                    f.close()
                if subject_data['clearlogoImg']:
                    with open(f"{config['save_path']}/{file_name}/clearlogo.{subject_data['clearlogoImg'][1]}", "wb") as f:
                        f.write(subject_data['clearlogoImg'][0])
                        f.close()
        except Exception as e:
            logging.error(f"[file_name: {file_name}] - 生成 NFO 数据出错: {e}")
            pass
        try:
            logging.info(f"[file_name: {file_name}] - 开始下载")
            download(url, f"{config['save_path']}/{file_name}/{file_name}.{file_type}")
            logging.info(f"[file_name: {file_name}] - 开始上传")
            proc = await asyncio.create_subprocess_exec(
                "rclone", "move", f"{config['save_path']}/{file_name}/",
               f"{config['rclone_config_name']}:NC-Raws/{folder_name}/",
                "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
            await proc.wait()
            if proc.returncode == 0:
                await bot.send_message(config["notice_chat"], f"\\[#更新提醒] `{bgm_id}`\n - 已上传: `{file_name}`", parse_mode="Markdown")
                logging.info(f"[file_name: {file_name}] - 已下载并上传成功")
        except Exception as e:
            logging.error(f"[file_name: {file_name}] - 下载或上传失败: {e}")
        finally:
            shutil.rmtree(f"{config['save_path']}/{file_name}")
            queue.task_done()


if __name__ == "__main__":
    bot = AsyncTeleBot(config["bot_token"])
    bot_register(bot)
    client = TelegramClient("data/channel_downloader", config["api_id"], config["api_hash"]).start()
    client.add_event_handler(nc_chat_detecting)
    client.add_event_handler(ani_chat_detecting)
    tasks = []
    try:
        loop = asyncio.get_event_loop()
        task = loop.create_task(bot.polling(non_stop=True))
        tasks.append(task)
        for i in range(config["max_num"]):
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