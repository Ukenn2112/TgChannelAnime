# !/usr/bin/env python3
import asyncio
import asyncio.subprocess
import json
import logging
import os
import re
import shutil
from typing import Union

from requests import post

from utils.abema import abema_download
from utils.bgm_nfo import episode_nfo, save_nfo, subject_name, subject_nfo
from utils.bot import async_send_messsge, bot_register
from utils.download import download
from utils.global_vars import bot, client, config, queue, sql
from utils.msg_events import ani_chat_detecting, nc_chat_detecting, nc_group_detecting
from utils.schedule_orm import run_schedule, set_schedule
from utils.queue_api import start_api, stop_api

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(
    format="[%(levelname)s]%(asctime)s: %(message)s",
    handlers=[
        logging.FileHandler("data/run.log", encoding="UTF-8"),
        logging.StreamHandler(),
    ],
)

async def down_worker(name):
    """
    0 -> url: 下载链接 (必须) str
    1 -> season_name: 番剧名称 (必须) str
    2 -> file_type: 文件类型后缀 (必须) str
    3 -> volume: 剧集集数 (必须) int
    4 -> platform: 平台名称 (必须) str
    5 -> bgm_id: BGM ID (必须) str
    6 -> tmdb_d: TMDB ID (可选) <tv|movie/id> str
    7 -> chat_msg_id: 视频频道消息 ID (可选) int"""
    while True:
        queue_item: list = await queue.get()
        url: str = queue_item[0]
        season_name: str = queue_item[1]
        file_type: str = queue_item[2]
        volume: Union[int, float] = queue_item[3]
        platform: str = queue_item[4]
        bgm_id: str = queue_item[5]
        # 如果没有获得到 TMDB，则为 None
        tmdb_d, chat_msg_id = None, None
        if len(queue_item) > 6:
            tmdb_d: str = queue_item[6]
        if len(queue_item) > 7:
            chat_msg_id: int = queue_item[7]
        if platform == "Abema":
            up_folder_name = season_name
        else: # 除 abema 其他平台
            # 处理获取到的剧集名称并去除季度信息
            season = re.search(r"第(.*)季", season_name)
            if season: season_name = season_name.replace(season.group(0), "").strip()
            # 使用 BGM ID 获取番剧日语名称将其设置为 GD 目的目录并去除季度信息
            up_folder_name = sql.inquiry_name_ja(bgm_id)
            if not up_folder_name:
                up_folder_name = subject_name(bgm_id)
                season = re.search(r"Season(.*)", up_folder_name)
                if season: up_folder_name = up_folder_name.replace(season.group(0), "").strip()
                sql.insert_data(bgm_id, tmdb_d, season_name, up_folder_name)
            else:
                sql.update_time(bgm_id)
        if isinstance(volume, int):
            _volume = f"{volume:02d}"
            episode_type: int = 0
        elif isinstance(volume, float):
            _volume = volume
            episode_type: int = 1
        # 拼接视频名称以及临时下载目录名称
        video_name = f"{season_name} - S01E{_volume} - {platform}"
        worker_path = f"{config['save_path']}{video_name}"
        # 创建临时下载目录
        if not os.path.exists(worker_path):
            os.mkdir(worker_path)
        # 创建 NFO 文件 先判断 GD 是否存在该目录 如果存在则不创建
        try:
            proc = await asyncio.create_subprocess_exec(
                "rclone", "lsjson", f"{config['rclone_config_name']}:NC-Raws", "--dirs-only",
                stdout=asyncio.subprocess.PIPE)
            output = await proc.communicate()
            dirs_list = json.loads(output[0].decode("utf-8"))
            dirs = [dirs["Name"] for dirs in dirs_list if up_folder_name in dirs["Name"]]
            # 生成 NFO 文件
            subject_data = subject_nfo(bgm_id, tmdb_d) if not dirs else None
            episode_data = episode_nfo(bgm_id, volume, episode_type)
            save_nfo(worker_path, video_name, subject_data, episode_data)
        except Exception as e:
            logging.error(f"[video_name: {video_name}] - 生成 NFO 数据出错: {e}")
            pass
        # 下载视频文件并上传到 GD
        try:
            logging.info(f"[video_name: {video_name}] - 开始下载")
            try:
                if platform == "Abema":
                    abema_download(url, bgm_id)
                else:
                    download(url, f"{worker_path}/{video_name}.{file_type}")
            except Exception as e:
                if chat_msg_id:
                    logging.warning(f"[video_name: {video_name}] - 下载失败，正在尝试从频道下载: {e}")
                    await bot.send_message(config["notice_chat"],
                        f"\\[#报告] `{bgm_id}`\n - {video_name}\n\nNC Drive 下载失败，正在尝试从频道下载", parse_mode="Markdown")
                    chat_msg = await client.get_messages(config["nc_chat_id"], ids=chat_msg_id)
                    loop = asyncio.get_event_loop()
                    task = loop.create_task(client.download_media(chat_msg, f"{video_name}/{video_name}.{file_type}"))
                    await asyncio.wait_for(task, timeout=3600)
                else: raise e
            logging.info(f"[video_name: {video_name}] - 开始上传")
            proc = await asyncio.create_subprocess_exec(
                "rclone", "move", worker_path,
               f"{config['rclone_config_name']}:NC-Raws/{up_folder_name}/",
                "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
            await proc.wait()
            if proc.returncode == 0:
                await async_send_messsge(bot, bgm_id, video_name)
                if config["finish_url"]:
                    post(config["finish_url"])
                logging.info(f"[video_name: {video_name}] - 已下载并上传成功")
        except Exception as e:
            logging.error(f"[video_name: {video_name}] - 下载或上传失败: {e}")
            await bot.send_message(config["notice_chat"],
                f"\\[#出错啦] `{bgm_id}`\n - {video_name} 下载或上传失败: \n\n`{e}`", parse_mode="Markdown")
        finally:
            shutil.rmtree(worker_path)
            queue.task_done()


if __name__ == "__main__":
    sql.create_season_db()
    sql.create_subscribe_db()
    sql.create_abema_db()
    set_schedule()
    bot_register(bot)
    client.start()
    client.add_event_handler(nc_chat_detecting)
    client.add_event_handler(ani_chat_detecting)
    client.add_event_handler(nc_group_detecting)
    tasks = []
    try:
        loop = asyncio.get_event_loop()
        tasks.append(loop.create_task(bot.polling(non_stop=True)))
        tasks.append(loop.create_task(run_schedule()))
        for i in range(config["max_num"]):
            tasks.append(loop.create_task(down_worker(f"down_worker-{i}")))
        start_api()
        print("已启动 (按 Ctrl+C 停止)")
        client.run_until_disconnected()
    finally:
        for task in tasks:
            task.cancel()
        client.disconnect()
        sql.close()
        stop_api()
        print("已停止")