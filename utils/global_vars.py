import asyncio
import json

with open("data/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

queue = asyncio.Queue()