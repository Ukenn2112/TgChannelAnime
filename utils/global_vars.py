import asyncio
import json

from telebot.async_telebot import AsyncTeleBot
from telethon import TelegramClient

from utils.sqlite_orm import SQLite

with open("data/config.json", "r", encoding="utf-8") as f:
    config: dict = json.load(f)

queue = asyncio.Queue()

sql = SQLite()

bot = AsyncTeleBot(config["bot_token"])

client = TelegramClient("data/channel_downloader", config["api_id"], config["api_hash"])