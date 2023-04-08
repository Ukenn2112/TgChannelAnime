import asyncio
import logging

import schedule

from utils.abema import abema_worker
from utils.old_disposal import old_anime_disposal
from utils.global_vars import config


def set_schedule():
    """设置定时任务"""
    schedule.every().wednesday.at("08:00").do(async_function_old_anime_disposal)
    for ab in config["abema_list"]:
        if ab["week"] == "1":
            schedule.every().monday.at(ab["time"]).do(
                async_function, ab["sid"], ab["bgmid"])
        elif ab["week"] == "2":
            schedule.every().tuesday.at(ab["time"]).do(
                async_function, ab["sid"], ab["bgmid"])
        elif ab["week"] == "3":
            schedule.every().wednesday.at(ab["time"]).do(
                async_function, ab["sid"], ab["bgmid"])
        elif ab["week"] == "4":
            schedule.every().thursday.at(ab["time"]).do(
                async_function, ab["sid"], ab["bgmid"])
        elif ab["week"] == "5":
            schedule.every().friday.at(ab["time"]).do(
                async_function, ab["sid"], ab["bgmid"])
        elif ab["week"] == "6":
            schedule.every().saturday.at(ab["time"]).do(
                async_function, ab["sid"], ab["bgmid"])
        elif ab["week"] == "7":
            schedule.every().sunday.at(ab["time"]).do(
                async_function, ab["sid"], ab["bgmid"])


def async_function(sid, bgmid):
    loop = asyncio.get_event_loop()
    loop.create_task(abema_worker(sid, bgmid))


def async_function_old_anime_disposal():
    loop = asyncio.get_event_loop()
    loop.create_task(old_anime_disposal())


def clear_schedule():
    """清除定时任务"""
    logging.info("已清除定时任务")
    schedule.clear()


async def run_schedule():
    """定时任务"""
    logging.info("已设置定时任务")
    while True:
        schedule.run_pending()
        await asyncio.sleep(30)
