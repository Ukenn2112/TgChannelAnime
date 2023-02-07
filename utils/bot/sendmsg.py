import asyncio
import time

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.global_vars import config, sql


async def async_send_messsge(bot, bgm_id, video_name):
    """发送更新提醒"""
    # 发送更新提醒 (用户)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('退订通知', url=f"tg://resolve?domain={config['bot_username']}&start=unsubscribe-{bgm_id}"))
    subscribe_list = sql.inquiry_subscribe_alluser(bgm_id)
    if subscribe_list:
        for i, user in enumerate(subscribe_list):
            await bot.send_message(user, f"[#更新提醒] {video_name} 更新咯～", reply_markup=markup)
            if (i + 1) % 30 == 0:
                await asyncio.sleep(1)
    # 发送更新提醒 (频道)
    markupp = InlineKeyboardMarkup()
    markupp.add(
        InlineKeyboardButton('查看详情', url=f"tg://resolve?domain=BangumiBot&start={bgm_id}"),
        InlineKeyboardButton("订阅通知", url=f"tg://resolve?domain={config['bot_username']}&start=subscribe-{bgm_id}")
        )
    await bot.send_message(config["notice_chat"], f"\\[#更新提醒] `{bgm_id}`\n - 已上传: `{video_name}`", parse_mode="Markdown", reply_markup=markupp)


def send_messsge(bot, bgm_id, video_name):
    """发送更新提醒"""
    # 发送更新提醒 (用户)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('退订通知', url=f"tg://resolve?domain={config['bot_username']}&start=unsubscribe-{bgm_id}"))
    subscribe_list = sql.inquiry_subscribe_alluser(bgm_id)
    if subscribe_list:
        for i, user in enumerate(subscribe_list):
            bot.send_message(user, f"[#更新提醒] {video_name} 更新咯～", reply_markup=markup)
            if (i + 1) % 30 == 0:
                time.sleep(1)
    # 发送更新提醒 (频道)
    markupp = InlineKeyboardMarkup()
    markupp.add(
        InlineKeyboardButton('查看详情', url=f"tg://resolve?domain=BangumiBot&start={bgm_id}"),
        InlineKeyboardButton("订阅通知", url=f"tg://resolve?domain={config['bot_username']}&start=subscribe-{bgm_id}")
        )
    bot.send_message(config["notice_chat"], f"\\[#更新提醒] `{bgm_id}`\n - 已上传: `{video_name}`", parse_mode="Markdown", reply_markup=markupp)