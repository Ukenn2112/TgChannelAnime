import asyncio
import json
from telebot.async_telebot import AsyncTeleBot
from utils.sqlite_orm import SQLite

with open("data/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

queue = asyncio.Queue()

sql = SQLite()

bot = AsyncTeleBot(config["bot_token"])