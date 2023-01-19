import base64
import json
import re
import urllib.parse
import asyncio

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

import global_vars

queue: asyncio.Queue = global_vars.queue


async def add_white(message: Message, bot: AsyncTeleBot):
    if message.from_user.id not in global_vars.config["admin_list"]:
        return
    data = message.text.split(" ")
    if len(data) < 3:
        return await bot.reply_to(message, "参数错误")
    elif message.text.startswith("/b_global"):
        if data[1] == "add":
            for a in data[2].split("#"):
                global_vars.config["B_Global_whitelist"].append(a)
        elif data[1] == "del":
            for d in data[2].split("#"):
                global_vars.config["B_Global_whitelist"].remove(d)
    elif message.text.startswith("/bilibili"):
        if data[1] == "add":
            for a in data[2].split("#"):
                global_vars.config["Bilibili_whitelist"].append(a)
        elif data[1] == "del":
            for d in data[2].split("#"):
                global_vars.config["Bilibili_whitelist"].remove(d)
    elif message.text.startswith("/cr"):
        if data[1] == "add":
            for a in data[2].split("#"):
                global_vars.config["CR_whitelist"].append(a)
        elif data[1] == "del":
            for d in data[2].split("#"):
                global_vars.config["CR_whitelist"].remove(d)
    elif message.text.startswith("/sentai"):
        if data[1] == "add":
            for a in data[2].split("#"):
                global_vars.config["Sentai_whitelist"].append(a)
        elif data[1] == "del":
            for d in data[2].split("#"):
                global_vars.config["Sentai_whitelist"].remove(d)
    elif message.text.startswith("/admin"):
        if data[1] == "add":
            for d in data[2].split("#"):
                global_vars.config["admin_list"].append(int(d))
        elif data[1] == "del":
            for d in data[2].split("#"):
                global_vars.config["admin_list"].remove(int(d))
    with open("config.json", "w", encoding="utf-8") as f: json.dump(global_vars.config, f, indent=4, ensure_ascii=False)
    await bot.reply_to(message, (
        "*修改成功 现在白名单状况*\n\n"
        "*B-Global 白名单*: \n\n `" + '\n '.join(global_vars.config['B_Global_whitelist']) + "`\n\n"
        "*Bilibili 白名单*: \n\n `" + '\n '.join(global_vars.config['Bilibili_whitelist']) + "`\n\n"
        "*CR 白名单*: \n\n `" + '\n '.join(global_vars.config['CR_whitelist']) + "`\n\n"
        "*Sentai 白名单*: \n\n `" + '\n '.join(global_vars.config['CR_whitelist']) + "`\n\n"
        "*admin-list*: \n\n `" + '\n '.join([str(x) for x in global_vars.config['admin_list']]) + "`\n\n"
        ), parse_mode="Markdown")


async def now_white(message: Message, bot: AsyncTeleBot):
    if message.from_user.id not in global_vars.config["admin_list"]:
        return
    await bot.reply_to(message, (
        "*B-Global 白名单*: \n\n `" + '\n '.join(global_vars.config['B_Global_whitelist']) + "`\n\n"
        "*Bilibili 白名单*: \n\n `" + '\n '.join(global_vars.config['Bilibili_whitelist']) + "`\n\n"
        "*CR 白名单*: \n\n `" + '\n '.join(global_vars.config['CR_whitelist']) + "`\n\n"
        "*Sentai 白名单*: \n\n `" + '\n '.join(global_vars.config['CR_whitelist']) + "`\n\n"
        "*admin-list*: \n\n `" + '\n '.join([str(x) for x in global_vars.config['admin_list']]) + "`\n\n"
        ), parse_mode="Markdown") 


async def url_down(message: Message, bot: AsyncTeleBot):
    if message.from_user.id not in global_vars.config["admin_list"]:
        return
    data = message.text.split(" ")
    if len(data) <= 1:
        return await bot.reply_to(message, "参数错误")
    if re.search(r"(nc\.raws\.dev)", data[1]):
        try:
            url = "https://nc.raws.dev" + base64.b64decode(data[1].split("/")[-1].replace("_", "/").replace("-", "+")).decode("utf-8")
        except:
            return await bot.reply_to(message, "错误的链接")
        file_name = url.split("/")[-1]
        file_type = file_name.split(".")[-1]
        data = re.search(r"\[NC-Raws\] (.+) - (.+) \((.+) ([0-9]+x[0-9]+).+\)", file_name)
        season_name = data.group(1)
        volume = data.group(2)
        platform = data.group(3)
        url = urllib.parse.quote(url, safe=":/?&=").replace("mkv", "zip").replace("mp4", "zip")
    elif re.search(r"(resources\.ani\.rip)", data[1]):
        url = urllib.parse.unquote(data[1], encoding='utf-8')
        file_name = url.split("/")[-1]
        file_type = file_name.split(".")[-1].replace("?d=true", "")
        data = re.search(r"\[ANi\] (.+) - (.+) \[.+\]\[(.+)\]\[.+\]\[.+\]\[.+\]\..+", file_name)
        season_name = data.group(1).replace("（僅限港澳台地區）", "")
        volume = data.group(2)
        platform = data.group(3)
        url = urllib.parse.quote(url, safe=":/?&=")
    else:
        return await bot.reply_to(message, "错误的链接")
    await bot.reply_to(message, "已加入队列")
    await queue.put((url, season_name, file_type, volume, platform))


async def help_message(message: Message, bot: AsyncTeleBot):
    if message.from_user.id not in global_vars.config["admin_list"]:
        return
    await bot.reply_to(message, (
        "命令列表:\n\n"
        "`/b_global [add/del] [白名单]` 添加或删除白名单 多个以#隔开\n\n"
        "`/bilibili [add/del] [白名单]` 解释同上\n\n"
        "`/cr [add/del] [白名单]` 解释同上\n\n"
        "`/sentai [add/del] [白名单]` 解释同上\n\n"
        "`/add_admin [add/del] [白名单]` 解释同上\n\n"
        "`/now_white` 获取现在的白名单\n\n"
        "`/url <url>` url 为 NC-Raws 频道的在线播放链接 或 Ani 的下载链接\n\n"
        "`/help 本帮助`\n\n"
        ), parse_mode="Markdown")

def register(bot: AsyncTeleBot):
    bot.register_message_handler(add_white, commands=["b_global", "bilibili", "cr", "sentai", "admin"], chat_types=["private"], pass_bot=True)
    bot.register_message_handler(now_white, commands=["now_white"], chat_types=["private"], pass_bot=True)
    bot.register_message_handler(url_down, commands=["url"], chat_types=["private"], pass_bot=True)
    bot.register_message_handler(help_message, commands=["help"], chat_types=["private"], pass_bot=True)