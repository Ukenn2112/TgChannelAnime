import base64
import logging
import re
import urllib.parse

from telethon import events

from utils.global_vars import config, queue


@events.register(events.NewMessage(chats=config["nc_chat_id"]))
async def nc_chat_detecting(update):
    message = update.message
    if message.file and "video" in message.file.mime_type:
        url = re.search(r"https?:\/\/nc\.raws\.dev\/[0-9]+:video\/(.+?)\)", message.text)
        bgm_id = re.search(r"https?:\/\/bgm\.tv\/subject\/([0-9]+)", message.text)
        if not url or not bgm_id: return logging.error(f"[message_id: {message.id}] - 无法解析的消息")

        url = "https://nc.raws.dev" + base64.b64decode(url.group(1).split("/")[-1].replace("_", "/").replace("-", "+")).decode("utf-8")
        bgm_id = bgm_id.group(1)
        tmdb_d = re.search(r"https?:\/\/www\.themoviedb\.org\/((tv|movie)\/[0-9]+)", message.text)
        if tmdb_d: tmdb_d = tmdb_d.group(1)
        file_name = url.split("/")[-1]
        file_type = file_name.split(".")[-1]
        data = re.search(r"\[.+\] (.+) - (.+) \((.+) ([0-9]+x[0-9]+).+\)", file_name)
        season_name = data.group(1)
        volume = data.group(2)
        platform = data.group(3)

        tag_name = re.search(r"\n\n#(.+)\n\n", message.text).group(1)
        for bid in config["bgm_compare"]:
            if bid["tagname"] == tag_name:
                bgm_id = bid["bgmid"]
                break
        if platform == "Baha":
            if tag_name in config["Baha_blacklist"]:
                return
        elif platform == "B-Global Donghua" or platform == "B-Global":
            if tag_name not in config["B_Global_whitelist"]:
                return
        elif platform == "CR":
            if tag_name not in config["CR_whitelist"]:
                return
        elif platform == "Sentai":
            if tag_name not in config["Sentai_whitelist"]:
                return
        else:
            return logging.error(f"[file_name: {file_name}] - 未知平台: {platform}")
        url = urllib.parse.quote(url, safe=":/?&=").replace("mkv", "zip").replace("mp4", "zip")
        await queue.put((url, season_name, file_type, volume, platform, bgm_id, tmdb_d))


@events.register(events.NewMessage(chats=config["ani_chat_id"]))
async def ani_chat_detecting(update):
    message = update.message
    if message.file and "video" in message.file.mime_type:
        url = re.search(r"(https?:\/\/resources\.ani\.rip\/.+?)\)", message.text)
        if not url: return logging.error(f"[message_id: {message.id}] - 无法解析的消息")

        file_name = re.search(r"【番名】: (.+?)\n", message.text).group(1)
        file_type = file_name.split(".")[-1]
        data = re.search(r"\[ANi\] (.+) - (.+) \[.+\]\[(.+)\]\[.+\]\[.+\]\[.+\]\..+", file_name)
        season_name = data.group(1).replace("（僅限港澳台地區）", "")
        volume = data.group(2)
        platform = data.group(3)

        tag_name = re.search(r"#新番更新  #(.+?)\n", message.text).group(1)
        bgm_id = None
        if platform != "Bilibili": return
        for w in config["Bilibili_whitelist"]:
            if w['tagname'] == tag_name:
                bgm_id = w['bgmid']
                break
        if not bgm_id: return
        await queue.put((url.group(1), season_name, file_type, volume, platform, bgm_id))