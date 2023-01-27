from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from utils.global_vars import config
from utils.sqlite_orm import SQLite

sql = SQLite()

async def subscribe(message: Message, bot: AsyncTeleBot):
    tg_id = message.from_user.id
    msg_data = message.text.split(" ")
    if len(msg_data) != 2:
        return
    msg_data = msg_data[1].split("-")
    if len(msg_data) > 1 and msg_data[0].startswith("subscribe"):
        if sql.inquiry_subscribe_user(msg_data[1], tg_id):
            return await bot.reply_to(message, "你已经订阅过了")
        sql.insert_subscribe(msg_data[1], tg_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("取消订阅", url=f"tg://resolve?domain={config['bot_username']}&start=unsubscribe-{msg_data[1]}"))
        return await bot.reply_to(message, f"订阅成功 {msg_data[1]}", reply_markup=markup)
    elif len(msg_data) > 1 and msg_data[0].startswith("unsubscribe"):
        if not sql.inquiry_subscribe_user(msg_data[1], tg_id):
            return await bot.reply_to(message, "未找到该订阅")
        sql.delete_subscribe(msg_data[1], tg_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("恢复订阅", url=f"tg://resolve?domain={config['bot_username']}&start=subscribe-{msg_data[1]}"))
        return await bot.reply_to(message, f"取消订阅成功 {msg_data[1]}", reply_markup=markup)