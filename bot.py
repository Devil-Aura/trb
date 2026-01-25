import os
import asyncio
from pyrogram import Client
from config import Config

# Ensure download directory exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

class TrackRemoverBot(Client):
    def __init__(self):
        super().__init__(
            "TrackRemoverBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=4
        )
        self.task_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_TASKS)
        self.active_tasks = {} # Map user_id to task info

    async def start(self):
        Config.load_config()
        await super().start()
        print("Bot Started!")

    async def stop(self, *args):
        await super().stop()
        print("Bot Stopped!")
