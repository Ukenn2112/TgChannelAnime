import asyncio
import json
import re
import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.types import ForceReply, Message

from utils.bgm_nfo import subject_name
from utils.global_vars import config

wait_reply = list()

async def file_sub(message: Message, bot: AsyncTeleBot):
    file_name = message.document.file_name
    if 'srt' not in file_name:
        return
    file = await bot.get_file(message.document.file_id)
    markup = ForceReply(selective=True, input_field_placeholder="请告诉我BGM ID 和 集数")
    msg = await bot.reply_to(message, f"好的，已收到字幕\n\n`{file_name}`\n\n请回复此消息告诉我 BGM ID 和 集数 中间用*空格*隔开（不满两位数需补0）\n\n", reply_markup=markup, parse_mode="Markdown")
    wait_reply.append((msg.message_id, file.file_path, file_name))


async def send_sub(message: Message, bot: AsyncTeleBot):
    msg_data = message.text.split(" ")
    sub_data, sub_type, sub_len = None, None, "default"
    for i in wait_reply:
        if i[0] == message.reply_to_message.message_id:
            try:
                sub_data = await bot.download_file(i[1])
                if "CHS" in i[2] or "zh-Hans" in i[2] or "zh_Hans" in i[2]:
                    sub_len = "CHS"
                elif "CHT" in i[2] or "zh-Hant" in i[2] or "zh_Hant" in i[2]:
                    sub_len = "CHT"
                sub_type = i[2].split(".")[-1]
            except:
                return await bot.reply_to(message, "获取文件失败, 可能消息已过期, 请从头开始")
            finally:
                wait_reply.remove(i)
            break
    if sub_data is None:
        return await bot.reply_to(message, "未找到可获取文件, 请从头开始")
    msg = await bot.reply_to(message, "正在处理, 请稍后...")
    logging.info(f"[Bot] 收到来自 {message.from_user.id} 的字幕处理请求 BGM ID: {msg_data[0]}, 集数: {msg_data[1]}")
    try:
        folder_name = subject_name(msg_data[0])
        season = re.search(r"Season(.*)", folder_name)
        if season:
            folder_name = folder_name.replace(season.group(0), "").strip()
        proc = await asyncio.create_subprocess_exec(
            "rclone", "lsjson", f"{config['rclone_config_name']}:NC-Raws/{folder_name}",
            stdout=asyncio.subprocess.PIPE)
        output = await proc.communicate()
        dirs_list = json.loads(output[0].decode("utf-8"))
        video_list = [v["Name"] for v in dirs_list if "video" in v["MimeType"]]
        for video in video_list:
            if f'S01E{msg_data[1]}' in video:
                sub_file = f"{video.split('.')[0]}.{sub_len}.{sub_type}"
                with open(sub_file, "wb") as f:
                    f.write(sub_data)
                    f.close()
                proc = await asyncio.create_subprocess_exec(
                    "rclone", "move", f"{config['save_path']}{sub_file}",
                    f"{config['rclone_config_name']}:NC-Raws/{folder_name}/",
                    "--transfers", "12", stdout=asyncio.subprocess.DEVNULL)
                await proc.wait()
                if proc.returncode == 0:
                    return await bot.edit_message_text(f"处理完成", msg.chat.id, msg.message_id)
                else:
                    return await bot.edit_message_text(f"处理失败", msg.chat.id, msg.message_id)
        return await bot.edit_message_text(f"未找到目标集", msg.chat.id, msg.message_id)
    except Exception as e:
        return await bot.edit_message_text(f"未找到文件夹或处理失败 {e}", msg.chat.id, msg.message_id)