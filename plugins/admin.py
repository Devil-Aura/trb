from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config

@Client.on_message(filters.command("addadmin"))
async def add_admin_handler(client: Client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        return await message.reply_text("❌ Only Owner can add admins.")
        
    if len(message.command) < 2:
        return await message.reply_text("⚠️ Usage: `/addadmin <user_id>`")
        
    try:
        new_admin = int(message.command[1])
        Config.ADMINS.add(new_admin)
        Config.save_config()
        await message.reply_text(f"✅ Added {new_admin} to admins.")
    except ValueError:
        await message.reply_text("❌ Invalid User ID.")

@Client.on_message(filters.command("remadmin"))
async def rem_admin_handler(client: Client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        return await message.reply_text("❌ Only Owner can remove admins.")
        
    if len(message.command) < 2:
        return await message.reply_text("⚠️ Usage: `/remadmin <user_id>`")
        
    try:
        rem_id = int(message.command[1])
        if rem_id == Config.OWNER_ID:
            return await message.reply_text("❌ Cannot remove Owner.")
            
        if rem_id in Config.ADMINS:
            Config.ADMINS.remove(rem_id)
            Config.save_config()
            await message.reply_text(f"✅ Removed {rem_id} from admins.")
        else:
            await message.reply_text("❌ User is not an admin.")
    except ValueError:
        await message.reply_text("❌ Invalid User ID.")

@Client.on_message(filters.command("admins"))
async def list_admins_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS:
        return await message.reply_text("❌ Access Denied.")
        
    text = "**👮‍♂️ Admin List:**\n"
    for admin in Config.ADMINS:
        text += f"`{admin}`\n"
    await message.reply_text(text)
