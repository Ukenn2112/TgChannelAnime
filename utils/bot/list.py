import json

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from utils.global_vars import config


async def add_white(message: Message, bot: AsyncTeleBot):
    data = message.text.split(" ")
    if len(data) < 3:
        return await bot.reply_to(message, "参数错误")
    elif message.text.startswith("/baha"):
        if data[1] == "add":
            for a in data[2].split("#"):
                config["Baha_blacklist"].append(a)
        elif data[1] == "del":
            for d in data[2].split("#"):
                config["Baha_blacklist"].remove(d)
    elif message.text.startswith("/b_global"):
        if data[1] == "add":
            for a in data[2].split("#"):
                config["B_Global_whitelist"].append(a)
        elif data[1] == "del":
            for d in data[2].split("#"):
                config["B_Global_whitelist"].remove(d)
    elif message.text.startswith("/bilibili"):
        if data[1] == "add":
            for a in data[2].split("#"):
                d = a.split("/")
                if len(d) < 2:
                    return await bot.reply_to(message, "参数错误")
                config["Bilibili_whitelist"].append({"tagname": d[0], "bgmid": d[1]})
        elif data[1] == "del":
            for d in data[2].split("#"):
                for i in config["Bilibili_whitelist"]:
                    if i["tagname"] == d:
                        config["Bilibili_whitelist"].remove(i)
    elif message.text.startswith("/cr"):
        if data[1] == "add":
            for a in data[2].split("#"):
                config["CR_whitelist"].append(a)
        elif data[1] == "del":
            for d in data[2].split("#"):
                config["CR_whitelist"].remove(d)
    elif message.text.startswith("/sentai"):
        if data[1] == "add":
            for a in data[2].split("#"):
                config["Sentai_whitelist"].append(a)
        elif data[1] == "del":
            for d in data[2].split("#"):
                config["Sentai_whitelist"].remove(d)
    elif message.text.startswith("/admin"):
        if data[1] == "add":
            for d in data[2].split("#"):
                config["admin_list"].append(int(d))
        elif data[1] == "del":
            for d in data[2].split("#"):
                config["admin_list"].remove(int(d))
    elif message.text.startswith("/bgmcom"):
        if data[1] == "add":
            for a in data[2].split("#"):
                d = a.split("/")
                if len(d) < 2:
                    return await bot.reply_to(message, "参数错误")
                config["bgm_compare"].append({"tagname": d[0], "bgmid": d[1]})
        elif data[1] == "del":
            for d in data[2].split("#"):
                for i in config["bgm_compare"]:
                    if i["tagname"] == d:
                        config["bgm_compare"].remove(i)
    with open("data/config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    await bot.reply_to(message, (
        "*修改成功 现在名单状况*\n\n"
        "*Baha 黑名单*: \n\n `" + '\n '.join(config['Baha_blacklist']) + "`\n\n"
        "*B-Global 白名单*: \n\n `" + '\n '.join(config['B_Global_whitelist']) + "`\n\n"
        "*Bilibili 白名单*: \n\n `" + '\n '.join([n['tagname'] for n in config['Bilibili_whitelist']]) + "`\n\n"
        "*CR 白名单*: \n\n `" + '\n '.join(config['CR_whitelist']) + "`\n\n"
        "*Sentai 白名单*: \n\n `" + '\n '.join(config['CR_whitelist']) + "`\n\n"
        "*BGM 对照*: \n\n `" + '\n '.join([n['tagname']+'/'+n['bgmid'] for n in config['bgm_compare']]) + "`\n\n"
        "*admin-list*: \n\n `" + '\n '.join([str(x) for x in config['admin_list']]) + "`\n\n"
        ), parse_mode="Markdown")


async def now_white(message: Message, bot: AsyncTeleBot):
    if message.from_user.id not in config["admin_list"]:
        return
    await bot.reply_to(message, (
        "*Baha 黑名单*: \n\n `" + '\n '.join(config['Baha_blacklist']) + "`\n\n"
        "*B-Global 白名单*: \n\n `" + '\n '.join(config['B_Global_whitelist']) + "`\n\n"
        "*Bilibili 白名单*: \n\n `" + '\n '.join([n['tagname'] for n in config['Bilibili_whitelist']]) + "`\n\n"
        "*CR 白名单*: \n\n `" + '\n '.join(config['CR_whitelist']) + "`\n\n"
        "*Sentai 白名单*: \n\n `" + '\n '.join(config['CR_whitelist']) + "`\n\n"
        "*BGM 对照*: \n\n `" + '\n '.join([n['tagname']+'/'+n['bgmid'] for n in config['bgm_compare']]) + "`\n\n"
        "*admin-list*: \n\n `" + '\n '.join([str(x) for x in config['admin_list']]) + "`\n\n"
        ), parse_mode="Markdown") 