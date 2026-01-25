from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from helpers.utils import cleanup_files

@Client.on_message(filters.command(["cancel", "cancelall"]))
async def cancel_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id in client.active_tasks:
        task = client.active_tasks[user_id]
        
        # Cleanup files
        cleanup_files([task['input_path']])
        
        # Remove from active tasks
        del client.active_tasks[user_id]
        
        # Release semaphore
        try:
            client.task_semaphore.release()
        except ValueError:
            pass # Already released?
            
        await message.reply_text("❌ Task Cancelled.")
    else:
        await message.reply_text("⚠️ No active task found.")
