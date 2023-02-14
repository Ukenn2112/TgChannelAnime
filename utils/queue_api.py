import asyncio
import json
import logging
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request
from telebot import TeleBot
from waitress import serve

from utils.bgm_nfo import episode_nfo, save_nfo, subject_name, subject_nfo
from utils.bot import send_messsge
from utils.global_vars import config, sql
from utils.num_format import volume_format

bot = TeleBot(config["bot_token"])
# 异步线程池
executor = ThreadPoolExecutor()

app = Flask(__name__)
app.config ['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

@app.route('/ping')
def health():
    return jsonify({'status': 'OK', 'msg': 'Pong'}), 200


@app.route('/send_nfo')
def set_queue():
    json: dict = request.get_json()
    season_name = json.get('season_name')
    volume = json.get('volume')
    bgm_id = json.get('bgm_id')
    tmdb_d = json.get('tmdb_d')
    if not season_name or not volume or not bgm_id:
        return jsonify({'status': 'ERROR', 'msg': '参数错误'}), 400
    executor.submit(send_nfo, season_name, str(volume), bgm_id, tmdb_d)
    return jsonify({'status': 'OK', 'msg': '已加入生成队列'}), 200


def send_nfo(season_name, volume, bgm_id, tmdb_d):
    asyncio.run(nfo_send(season_name, volume, bgm_id, tmdb_d))


async def nfo_send(season_name, volume: str, bgm_id, tmdb_d):
    volume = await volume_format(volume)
    try:
        up_folder_name = sql.inquiry_name_ja(bgm_id)
        if not up_folder_name:
            up_folder_name = subject_name(bgm_id)
            season = re.search(r"Season(.*)", up_folder_name)
            if season: up_folder_name = up_folder_name.replace(season.group(0), "").strip()
            sql.insert_data(bgm_id, tmdb_d, season_name, up_folder_name)
        video_name = f"{season_name} - S01E{volume:02d} - Others"
        worker_path = f"{config['save_path']}{video_name}_nfo"
        if not os.path.exists(worker_path):
            os.mkdir(worker_path)
        proc = await asyncio.create_subprocess_exec(
                    "rclone", "lsjson", f"{config['rclone_config_name']}:NC-Raws", "--dirs-only",
                    stdout=asyncio.subprocess.PIPE)
        output = await proc.communicate()
        dirs_list = json.loads(output[0].decode("utf-8"))
        dirs = [dirs["Name"] for dirs in dirs_list if up_folder_name in dirs["Name"]]
        subject_data = subject_nfo(bgm_id, tmdb_d) if not dirs else None
        episode_data = episode_nfo(bgm_id, volume)
        save_nfo(worker_path, video_name, subject_data, episode_data)
        logging.info(f"[video_name: {video_name}] - 开始上传")
        proc = await asyncio.create_subprocess_exec(
            "rclone", "move", worker_path,
            f"{config['rclone_config_name']}:NC-Raws/{up_folder_name}/",
            "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
        await proc.wait()
        if proc.returncode == 0:
            send_messsge(bot, bgm_id, video_name)
            logging.info(f"[video_name: {video_name}] - NFO 上传成功")
    except Exception as e:
        logging.error(f"[video_name: {video_name}] - NFO 下载或上传失败: {e}")
        bot.send_message(config["notice_chat"],
            f"\\[#出错啦] `{bgm_id}`\n - {video_name} NFO 下载或上传失败: \n\n`{e}`", parse_mode="Markdown")
    finally:
        shutil.rmtree(worker_path)


def start_flask():
    serve(app, port=1899)


def start_api():
    executor.submit(start_flask)


def stop_api():
    executor.shutdown(wait=False)