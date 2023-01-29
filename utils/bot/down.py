import base64
import re
import urllib.parse

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from utils.global_vars import config, queue


async def ani_down(message: Message, bot: AsyncTeleBot):
    data = message.text.split(" ")
    if len(data) != 3:
        return await bot.reply_to(message, "参数错误")
    elif not data[1].isdecimal():
        return await bot.reply_to(message, "参数错误")
    bgm_id = data[1]
    if re.search(r"(resources\.ani\.rip)", data[2]):
        url = urllib.parse.unquote(data[2], encoding='utf-8')
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
    await queue.put((url, season_name, file_type, volume, platform, bgm_id))


async def nc_msg_down(message: Message, bot: AsyncTeleBot):
    if not message.forward_from_chat and message.forward_from_chat.id != -1001328150145:
        return
    url = re.search(r'https?:\/\/nc\.raws\.dev\/[0-9]+:video\/(.+?)"', message.html_caption)
    bgm_id = re.search(r'https?:\/\/bgm\.tv\/subject\/([0-9]+)', message.html_caption)
    if not url or not bgm_id: return await bot.reply_to(message, "无法解析此信息")

    url = "https://nc.raws.dev" + base64.b64decode(url.group(1).replace("_", "/").replace("-", "+")).decode("utf-8")
    bgm_id = bgm_id.group(1)
    tmdb_d = re.search(r'https?:\/\/www\.themoviedb\.org\/((tv|movie)\/[0-9]+)', message.html_caption)
    if tmdb_d: tmdb_d = tmdb_d.group(1)
    file_name = url.split("/")[-1]
    file_type = file_name.split(".")[-1]
    data = re.search(r"\[NC-Raws\] (.+) - (.+) \((.+) ([0-9]+x[0-9]+).+\)", file_name)
    season_name = data.group(1)
    volume = data.group(2)
    platform = data.group(3)
    url = urllib.parse.quote(url, safe=":/?&=").replace("mkv", "zip").replace("mp4", "zip")
    tag_name = re.search(r"#(.+?)\n\n", message.html_caption).group(1)
    for bid in config["bgm_compare"]:
        if bid["tagname"] == tag_name:
            bgm_id = bid["bgmid"]
            break
    await bot.reply_to(message, "已加入队列")
    await queue.put((url, season_name, file_type, volume, platform, bgm_id, tmdb_d))