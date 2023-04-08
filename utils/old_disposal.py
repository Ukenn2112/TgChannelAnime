import asyncio
import logging
from datetime import datetime, timedelta

from .global_vars import config, sql


async def old_anime_disposal():
    """过时番剧处理"""
    data = sql.inquiry_all_season()
    now_time = datetime.now() - timedelta(weeks=7) // 1000
    for i in data:
        if now_time > i[3]:
            logging.info(f"检测到过时番剧 {i[0]}，开始处理...")
            try:
                proc = await asyncio.create_subprocess_exec(
                    "rclone", "move", f"{config['rclone_config_name']}:NC-Raws/{i[2]}",
                   f"{config['rclone_config_name']}:Old-Anime/{i[2]}",
                    "-r", stdout=asyncio.subprocess.DEVNULL)
                await proc.wait()
                if proc.returncode == 0:
                    logging.info(f"[video_name: {i[2]}] - 过时番剧处理成功")
                    sql.delete_season_data(i[0])
            except Exception as e:
                logging.error(f"[video_name: {i[2]}] - 过时番剧处理失败: {e}")