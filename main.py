# !/usr/bin/env python3
import asyncio
import asyncio.subprocess
import json
import logging
import os
import re
import shutil

from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from utils.bgm_nfo import episode_nfo, subject_name, subject_nfo
from utils.bot import bot_register
from utils.download import download
from utils.global_vars import config, queue
from utils.msg_events import ani_chat_detecting, nc_chat_detecting
from utils.sqlite_orm import SQLite

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(
    format="[%(levelname)s]%(asctime)s: %(message)s",
    handlers=[
        logging.FileHandler("data/run.log", encoding="UTF-8"),
        logging.StreamHandler(),
    ],
)

sql = SQLite()

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
        # 如果没有获得到 TMDB，则为 None
        tmdb_d, chat_msg_id = None, None
        if len(queue_item) > 6:
            tmdb_d = queue_item[6]
        if len(queue_item) > 7:
            chat_msg_id = queue_item[7]
        # 处理获取到的剧集名称并去除季度信息
        season = re.search(r"第(.*)季", season_name)
        if season:
            season_name = season_name.replace(season.group(0), "").strip()
        # 拼接视频文件名称并生成文件夹
        file_name = f"{season_name} - S01E{volume} - {platform}"
        if not os.path.exists(config['save_path'] + file_name):
            os.mkdir(config['save_path'] + file_name)
        # 使用 BGM ID 获取番剧日语名称将其设置为 GD 目的目录并去除季度信息
        up_folder_name = sql.inquiry_name_ja(bgm_id)
        if not up_folder_name:
            up_folder_name = subject_name(bgm_id)
            season = re.search(r"Season(.*)", up_folder_name)
            if season:
                up_folder_name = up_folder_name.replace(season.group(0), "").strip()
            sql.insert_data(bgm_id, tmdb_d, season_name, up_folder_name)
        # 创建 Episode NFO 文件
        episode_data = episode_nfo(bgm_id, volume)
        if episode_data:
            with open(f"{config['save_path']}/{file_name}/{file_name}.nfo", "w", encoding="utf-8") as f:
                f.write(episode_data)
                f.close()
        # 创建 Subject NFO 文件 先判断 GD 是否存在该文件夹 如果存在则不创建
        try:
            proc = await asyncio.create_subprocess_exec(
                "rclone", "lsjson", f"{config['rclone_config_name']}:NC-Raws", "--dirs-only",
                stdout=asyncio.subprocess.PIPE)
            output = await proc.communicate()
            dirs_list = json.loads(output[0].decode("utf-8"))
            dirs = [dirs["Name"] for dirs in dirs_list if up_folder_name in dirs["Name"]]
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
        # 下载视频文件并上传到 GD
        try:
            logging.info(f"[file_name: {file_name}] - 开始下载")
            try:
                download(url, f"{config['save_path']}/{file_name}/{file_name}.{file_type}")
            except Exception as e:
                if chat_msg_id:
                    await bot.send_message(config["notice_chat"], f"\\[#报告] `{bgm_id}`\n - {file_name} NC Drive 下载失败，正在尝试从频道下载", parse_mode="Markdown")
                    chat_msg = await client.get_messages(config["nc_chat_id"], ids=chat_msg_id)
                    loop = asyncio.get_event_loop()
                    task = loop.create_task(client.download_media(
                        chat_msg, f"{config['save_path']}/{file_name}/{file_name}.{file_type}"))
                    await asyncio.wait_for(task, timeout=3600)
                else: raise e
            logging.info(f"[file_name: {file_name}] - 开始上传")
            proc = await asyncio.create_subprocess_exec(
                "rclone", "move", f"{config['save_path']}/{file_name}/",
               f"{config['rclone_config_name']}:NC-Raws/{up_folder_name}/",
                "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
            await proc.wait()
            if proc.returncode == 0:
                # 发送更新提醒 (用户)
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('退订通知', url=f"tg://resolve?domain={config['bot_username']}&start=unsubscribe-{bgm_id}"))
                subscribe_list = sql.inquiry_subscribe_alluser(bgm_id)
                if subscribe_list:
                    for users in subscribe_list:
                        for user in users:
                            await bot.send_message(user, f"[#更新提醒] {file_name} 更新咯～", reply_markup=markup)
                        await asyncio.sleep(1)
                # 发送更新提醒 (频道)
                markupp = InlineKeyboardMarkup()
                markupp.add(
                    InlineKeyboardButton('查看详情', url=f"tg://resolve?domain=BangumiBot&start={bgm_id}"),
                    InlineKeyboardButton("订阅通知", url=f"tg://resolve?domain={config['bot_username']}&start=subscribe-{bgm_id}")
                    )
                await bot.send_message(config["notice_chat"], f"\\[#更新提醒] `{bgm_id}`\n - 已上传: `{file_name}`", parse_mode="Markdown", reply_markup=markupp)
                logging.info(f"[file_name: {file_name}] - 已下载并上传成功")
        except Exception as e:
            logging.error(f"[file_name: {file_name}] - 下载或上传失败: {e}")
            await bot.send_message(config["notice_chat"], f"\\[#出错啦] `{bgm_id}`\n - {file_name} 下载或上传失败: \n\n`{e}`", parse_mode="Markdown")
        finally:
            shutil.rmtree(f"{config['save_path']}/{file_name}")
            queue.task_done()


if __name__ == "__main__":
    sql.create_season_db()
    sql.create_subscribe_db()
    bot = AsyncTeleBot(config["bot_token"])
    bot_register(bot)
    client = TelegramClient("data/channel_downloader", config["api_id"], config["api_hash"]).start()
    client.add_event_handler(nc_chat_detecting)
    client.add_event_handler(ani_chat_detecting)
    tasks = []
    try:
        loop = asyncio.get_event_loop()
        tasks.append(loop.create_task(bot.polling(non_stop=True)))
        for i in range(config["max_num"]):
            tasks.append(loop.create_task(worker(f"worker-{i}")))
        print("已启动 (按 Ctrl+C 停止)")
        client.run_until_disconnected()
    finally:
        for task in tasks:
            task.cancel()
        client.disconnect()
        print("已停止")