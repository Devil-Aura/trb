import os
import sys
from pyrogram import Client, filters
from config import Config

@Client.on_message(filters.command("restart") & filters.user(Config.ADMINS))
async def restart_bot(client, message):
    await message.reply_text("♻️ Restarting bot & cleaning temp files…")

    # cleanup downloads
    if os.path.exists("downloads"):
        for f in os.listdir("downloads"):
            try:
                os.remove(os.path.join("downloads", f))
            except:
                pass

    os.execv(sys.executable, [sys.executable] + sys.argv)
