import asyncio
import base64
import json
import re
import shutil
import os
import urllib.parse

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

import utils.global_vars as global_vars
from utils.bgm_nfo import subject_nfo, subject_name

queue: asyncio.Queue = global_vars.queue


async def add_white(message: Message, bot: AsyncTeleBot):
    if message.from_user.id not in global_vars.config["admin_list"]:
        return
    data = message.text.split(" ")
    if len(data) < 3:
        return await bot.reply_to(message, "参数错误")
    elif message.text.startswith("/baha"):
        if data[1] == "add":
            for a in data[2].split("#"):
                global_vars.config["Baha_blacklist"].append(a)
        elif data[1] == "del":
            for d in data[2].split("#"):
                global_vars.config["Baha_blacklist"].remove(d)
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
                d = a.split("/")
                if len(d) < 2:
                    return await bot.reply_to(message, "参数错误")
                global_vars.config["Bilibili_whitelist"].append({"tagname": d[0], "bgmid": d[1]})
        elif data[1] == "del":
            for d in data[2].split("#"):
                for i in global_vars.config["Bilibili_whitelist"]:
                    if i["tagname"] == d:
                        global_vars.config["Bilibili_whitelist"].remove(i)
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
    elif message.text.startswith("/bgmcom"):
        if data[1] == "add":
            for a in data[2].split("#"):
                d = a.split("/")
                if len(d) < 2:
                    return await bot.reply_to(message, "参数错误")
                global_vars.config["bgm_compare"].append({"tagname": d[0], "bgmid": d[1]})
        elif data[1] == "del":
            for d in data[2].split("#"):
                for i in global_vars.config["bgm_compare"]:
                    if i["tagname"] == d:
                        global_vars.config["bgm_compare"].remove(i)
    with open("data/config.json", "w", encoding="utf-8") as f: json.dump(global_vars.config, f, indent=4, ensure_ascii=False)
    await bot.reply_to(message, (
        "*修改成功 现在名单状况*\n\n"
        "*Baha 黑名单*: \n\n `" + '\n '.join(global_vars.config['Baha_blacklist']) + "`\n\n"
        "*B-Global 白名单*: \n\n `" + '\n '.join(global_vars.config['B_Global_whitelist']) + "`\n\n"
        "*Bilibili 白名单*: \n\n `" + '\n '.join([n['tagname'] for n in global_vars.config['Bilibili_whitelist']]) + "`\n\n"
        "*CR 白名单*: \n\n `" + '\n '.join(global_vars.config['CR_whitelist']) + "`\n\n"
        "*Sentai 白名单*: \n\n `" + '\n '.join(global_vars.config['CR_whitelist']) + "`\n\n"
        "*BGM 对照*: \n\n `" + '\n '.join([n['tagname']+'/'+n['bgmid'] for n in global_vars.config['bgm_compare']]) + "`\n\n"
        "*admin-list*: \n\n `" + '\n '.join([str(x) for x in global_vars.config['admin_list']]) + "`\n\n"
        ), parse_mode="Markdown")


async def now_white(message: Message, bot: AsyncTeleBot):
    if message.from_user.id not in global_vars.config["admin_list"]:
        return
    await bot.reply_to(message, (
        "*Baha 黑名单*: \n\n `" + '\n '.join(global_vars.config['Baha_blacklist']) + "`\n\n"
        "*B-Global 白名单*: \n\n `" + '\n '.join(global_vars.config['B_Global_whitelist']) + "`\n\n"
        "*Bilibili 白名单*: \n\n `" + '\n '.join([n['tagname'] for n in global_vars.config['Bilibili_whitelist']]) + "`\n\n"
        "*CR 白名单*: \n\n `" + '\n '.join(global_vars.config['CR_whitelist']) + "`\n\n"
        "*Sentai 白名单*: \n\n `" + '\n '.join(global_vars.config['CR_whitelist']) + "`\n\n"
        "*BGM 对照*: \n\n `" + '\n '.join([n['tagname']+'/'+n['bgmid'] for n in global_vars.config['bgm_compare']]) + "`\n\n"
        "*admin-list*: \n\n `" + '\n '.join([str(x) for x in global_vars.config['admin_list']]) + "`\n\n"
        ), parse_mode="Markdown") 


async def url_down(message: Message, bot: AsyncTeleBot):
    if message.from_user.id not in global_vars.config["admin_list"]:
        return
    data = message.text.split(" ")
    if len(data) < 4:
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
    if message.from_user.id not in global_vars.config["admin_list"]:
        return
    elif not message.forward_from_chat and message.forward_from_chat.id != -1001328150145:
        return
    url = re.search(r'(https?:\/\/nc\.raws\.dev\/0\:video\/.*)">线上观看', message.html_caption)
    bgm_id = re.search(r'https?:\/\/bgm\.tv\/subject\/([0-9]+)', message.html_caption)
    if not url and not bgm_id: return await bot.reply_to(message, "无法解析此信息")

    url = "https://nc.raws.dev" + base64.b64decode(url.group(1).split("/")[-1].replace("_", "/").replace("-", "+")).decode("utf-8")
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
    tag_name = re.search(r"\n\n#(.+)\n\n", message.html_caption).group(1)
    for bid in global_vars.config["bgm_compare"]:
        if bid["tagname"] == tag_name:
            bgm_id = bid["bgmid"]
            break
    await bot.reply_to(message, "已加入队列")
    await queue.put((url, season_name, file_type, volume, platform, bgm_id, tmdb_d))

async def re_subject_nfo(message: Message, bot: AsyncTeleBot):
    if message.from_user.id not in global_vars.config["admin_list"]:
        return
    data = message.text.split(" ")
    if len(data) < 4:
        return await bot.reply_to(message, "参数错误")
    elif not data[1].isdecimal():
        return await bot.reply_to(message, "参数错误")
    bgm_id = data[1]
    tmdb_id = data[2]
    tmdb_type = data[3]

    folder_name = subject_name(bgm_id)
    season = re.search(r"Season(.*)", folder_name)
    if season: folder_name = folder_name.replace(season.group(0), "").strip()
    if not os.path.exists(f"{folder_name}_nfo"): os.mkdir(f"{folder_name}_nfo")

    subject_data = subject_nfo(bgm_id, tmdb_type + '/' + tmdb_id)
    with open(f"{global_vars.config['save_path']}/{folder_name}_nfo/tvshow.nfo", "w", encoding="utf-8") as t:
        t.write(subject_data['tvshowNfo'])
        t.close()
    with open(f"{global_vars.config['save_path']}/{folder_name}_nfo/season.nfo", "w", encoding="utf-8") as s:
        s.write(subject_data['seasonNfo'])
        s.close()
    with open(f"{global_vars.config['save_path']}/{folder_name}_nfo/poster.{subject_data['posterImg'][1]}", "wb") as f:
        f.write(subject_data['posterImg'][0])
        f.close()
    with open(f"{global_vars.config['save_path']}/{folder_name}_nfo/fanart.{subject_data['fanartImg'][1]}", "wb") as f:
        f.write(subject_data['fanartImg'][0])
        f.close()
    if subject_data['clearlogoImg']:
        with open(f"{global_vars.config['save_path']}/{folder_name}_nfo/clearlogo.{subject_data['clearlogoImg'][1]}", "wb") as f:
            f.write(subject_data['clearlogoImg'][0])
            f.close()
    try:
        proc = await asyncio.create_subprocess_exec(
            "rclone", "move", f"{global_vars.config['save_path']}/{folder_name}_nfo/",
            f"{global_vars.config['rclone_config_name']}:NC-Raws/{folder_name}/",
            "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
        await proc.wait()
        if proc.returncode == 0:
             await bot.reply_to(message, "已重新生成并上传")
    except Exception as e:
        await bot.reply_to(message, f"上传失败: {e}")
    finally:
        shutil.rmtree(f"{global_vars.config['save_path']}/{folder_name}_nfo")

async def help_message(message: Message, bot: AsyncTeleBot):
    if message.from_user.id not in global_vars.config["admin_list"]:
        return
    await bot.reply_to(message, (
        "命令列表:\n\n"
        "`/baha [add/del] [黑名单]` 添加或删除黑名单 多个以#隔开\n\n"
        "`/b_global [add/del] [白名单]` 添加或删除白名单 多个以#隔开\n\n"
        "`/bilibili [add/del] [白名单/BGM ID]` 添加需要 BGM ID 使用 如 `大雪海的卡納/366250`\n\n"
        "`/cr [add/del] [白名单]` 解释同上\n\n"
        "`/sentai [add/del] [白名单]` 解释同上\n\n"
        "`/bgmcom [add/del] [白名单/BGM ID]` BGM ID 对照表\n\n"
        "`/add_admin [add/del] [白名单]` 解释同上\n\n"
        "`/now_white` 获取现在的白名单\n\n"
        "`/url <bgmid> <url>` url Ani 的下载链接\n\n"
        "下载 NC-Raws 的视频直接转发频道消息即可\n\n"
        "`/re_nfo <bgmid> <tmdbid> [tv/movie]` 重新生成剧集 NFO\n\n"
        "`/help 本帮助`\n\n"
        ), parse_mode="Markdown")

def bot_register(bot: AsyncTeleBot):
    """Bot register function."""
    bot.register_message_handler(nc_msg_down, chat_types=["private"], content_types=['video'], pass_bot=True)
    bot.register_message_handler(add_white, commands=["baha", "b_global", "bilibili", "cr", "sentai", "admin", "bgmcom"], chat_types=["private"], pass_bot=True)
    bot.register_message_handler(now_white, commands=["now_white"], chat_types=["private"], pass_bot=True)
    bot.register_message_handler(url_down, commands=["url"], chat_types=["private"], pass_bot=True)
    bot.register_message_handler(help_message, commands=["help"], chat_types=["private"], pass_bot=True)
    bot.register_message_handler(re_subject_nfo, commands=["re_nfo"], chat_types=["private"], pass_bot=True)