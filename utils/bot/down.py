import base64
import re
import urllib.parse

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from utils.abema import abema_worker
from utils.global_vars import config, queue
from utils.num_format import volume_format


async def url_down(message: Message, bot: AsyncTeleBot):
    data = message.text.split(" ")
    if len(data) < 2:
        return await bot.reply_to(message, "参数错误")
    elif not data[1].isdecimal():
        return await bot.reply_to(message, "参数错误")
    bgm_id = data[1]
    if len(data) > 3:
        tmdb_d = data[2]
        _url = data[3]
        if tmdb_d.isdecimal(): return await bot.reply_to(message, "参数错误")
    else: tmdb_d, _url = None, data[2]
    if re.search(r"(resources\.ani\.rip)", _url):
        url = urllib.parse.unquote(_url, encoding='utf-8')
        file_name = url.split("/")[-1]
        file_type = file_name.split(".")[-1].replace("?d=true", "")
        data = re.search(r"\[ANi\] (.+) - (.+) \[.+\]\[(.+)\]\[.+\]\[.+\]\[.+\]\..+", file_name)
        season_name = data.group(1).replace("（僅限港澳台地區）", "")
        volume = await volume_format(data.group(2))
        platform = data.group(3)
        url = urllib.parse.quote(url, safe=":/?&=")
    elif re.search(r"(abema\.tv\/video\/episode\/)", _url):
        await bot.reply_to(message, "已加入队列")
        return await abema_worker(_url.split("/")[-1].split("_s")[0], bgm_id, tmdb_d, _url.split("/")[-1])
    else:
        return await bot.reply_to(message, "错误的链接")
    await bot.reply_to(message, "已加入队列")
    await queue.put((url, season_name, file_type, volume, platform, bgm_id, tmdb_d))


async def nc_msg_down(message: Message, bot: AsyncTeleBot):
    if not message.forward_from_chat and message.forward_from_chat.id != -1001328150145:
        return
    entities_url = [i.url for i in message.caption_entities if i.type == "text_link"]
    url, bgm_id, tmdb_d = None, None, None
    for u in entities_url:
        if "raws.dev" in u:
            url = u.split("/")
        elif "bgm.tv" in u:
            bgm_id = u.split("/")[-1]
        elif "themoviedb.org" in u:
            tmdb_d = u.split("org/")[-1]
    if not url or not bgm_id: return await bot.reply_to(message, "无法解析此信息")

    url = "https://" + url[2] + base64.b64decode(url[-1].replace("_", "/").replace("-", "+")).decode("utf-8")
    file_name = url.split("/")[-1]
    file_type = file_name.split(".")[-1]
    data = re.search(r"\[.+\] (.+) - (.+) \((.+) ([0-9]+x[0-9]+).+\)", file_name)
    if not data: return await bot.reply_to(message, f"无法解析此信息 {file_name}")
    season_name = data.group(1)
    volume = await volume_format(data.group(2))
    platform = data.group(3)
    url = urllib.parse.quote(url, safe=":/?&=").replace("mkv", "zip").replace("mp4", "zip")
    tag_name = re.search(r"#(.+?)\n\n", message.html_caption).group(1)
    for bid in config["bgm_compare"]:
        if bid["tagname"] == tag_name:
            bgm_id = bid["bgmid"]
            break
    await bot.reply_to(message, "已加入队列")
    await queue.put((url, season_name, file_type, volume, platform, bgm_id, tmdb_d, message.forward_from_message_id))