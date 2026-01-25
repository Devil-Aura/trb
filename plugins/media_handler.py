import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from config import Config
from helpers.ffmpeg_tools import get_media_info, process_video
from helpers.keyboards import get_track_selection_keyboard
from helpers.utils import cleanup_files

@Client.on_message(filters.command([
    "tk", "trackkiller", 
    "remaudio", "remallaudio", 
    "remsubtitles", "remallsubtitles", 
    "remall", "h", "he"
]) & filters.reply)
async def track_killer_handler(client: Client, message: Message):
    cmd = message.command[0]
    
    # 1. Permission Check
    if Config.BOT_MODE == "private" and message.from_user.id not in Config.ADMINS:
        return await message.reply_text("❌ Bot is in Private Mode.")
        
    # 2. Media Check
    reply = message.reply_to_message
    if not reply.video and not reply.document:
        return await message.reply_text("❌ Please reply to a Video or Document file.")
        
    media = reply.video or reply.document
    if reply.document and "video" not in reply.document.mime_type:
        return await message.reply_text("❌ Document is not a video file.")

    # 3. Task Limit Check
    if client.task_semaphore.locked():
        return await message.reply_text("⚠️ Bot is busy with 4 parallel tasks. Please wait.")
        
    # 4. Start Task
    status_msg = await message.reply_text("⬇️ Downloading media to detect tracks...")
    
    try:
        await client.task_semaphore.acquire()
        
        task_id = f"{message.from_user.id}_{message.id}"
        dl_path = f"downloads/{task_id}_{media.file_name or 'video.mp4'}"
        
        file_path = await reply.download(file_name=dl_path)
        if not file_path:
            client.task_semaphore.release()
            return await status_msg.edit("❌ Download failed.")
            
        await status_msg.edit("🕵️ Detecting tracks...")
        
        info = await get_media_info(file_path)
        if not info:
            client.task_semaphore.release()
            cleanup_files([file_path])
            return await status_msg.edit("❌ Failed to detect media info.")
            
        # --- Handle Quick Commands (/h and /he) ---
        if cmd in ["h", "he"]:
            await status_msg.edit("⚙️ Quick processing... Please wait.")
            
            # Identify tracks to KEEP
            # /h: Hindi audio only, English/Songs subs only
            # /he: Hindi & English audio, English/Songs subs only
            keep_audio = []
            for s in info['audio']:
                lang = s['lang'].lower()
                if 'hin' in lang:
                    keep_audio.append(s['index'])
                elif cmd == "he" and 'eng' in lang:
                    keep_audio.append(s['index'])
            
            keep_subs = []
            for s in info['subtitle']:
                lang = s['lang'].lower()
                title = s['title'].lower()
                if 'eng' in lang or 'sign' in title or 'song' in title:
                    keep_subs.append(s['index'])
            
            output_path = f"downloads/processed_{task_id}.mkv"
            success = await process_video(file_path, output_path, keep_audio, keep_subs, info['audio'], info['subtitle'])
            
            if success:
                await status_msg.edit("⬆️ Uploading quick processed file...")
                if Config.DEFAULT_UPLOAD_MODE == "video":
                    await client.send_video(chat_id=message.chat.id, video=output_path, caption=f"✅ Quick processed (/{cmd})")
                else:
                    await client.send_document(chat_id=message.chat.id, document=output_path, caption=f"✅ Quick processed (/{cmd})")
                await status_msg.delete()
            else:
                await status_msg.edit("❌ Quick processing failed.")
            
            cleanup_files([file_path, output_path])
            client.task_semaphore.release()
            return

        # --- Normal Flow ---
        selected_audio = set()
        selected_subs = set()
        
        if cmd == "remallaudio" or cmd == "remall":
            selected_audio = {s['index'] for s in info['audio']}
        if cmd == "remallsubtitles" or cmd == "remall":
            selected_subs = {s['index'] for s in info['subtitle']}
            
        current_view = "audio"
        if cmd in ["remsubtitles", "remallsubtitles"]:
            current_view = "sub"
            
        client.active_tasks[message.from_user.id] = {
            "task_id": task_id, "input_path": file_path, "info": info,
            "selected_audio": selected_audio, "selected_subs": selected_subs,
            "status_msg": status_msg, "current_view": current_view, "page": 0
        }
        
        if current_view == "audio":
            if not info['audio']:
                if info['subtitle']:
                    client.active_tasks[message.from_user.id]["current_view"] = "sub"
                    keyboard = get_track_selection_keyboard(info['subtitle'], selected_subs, 0, is_audio=False)
                    await status_msg.edit("📝 Select Subtitle Tracks to REMOVE:", reply_markup=keyboard)
                else:
                    client.task_semaphore.release()
                    cleanup_files([file_path])
                    return await status_msg.edit("❌ No tracks found.")
            else:
                keyboard = get_track_selection_keyboard(info['audio'], selected_audio, 0, is_audio=True)
                await status_msg.edit("🔊 Select Audio Tracks to REMOVE:", reply_markup=keyboard)
        else:
            if not info['subtitle']:
                client.task_semaphore.release()
                cleanup_files([file_path])
                return await status_msg.edit("❌ No Subtitle tracks found.")
            else:
                keyboard = get_track_selection_keyboard(info['subtitle'], selected_subs, 0, is_audio=False)
                await status_msg.edit("📝 Select Subtitle Tracks to REMOVE:", reply_markup=keyboard)

    except Exception as e:
        if client.task_semaphore.locked():
             client.task_semaphore.release()
        cleanup_files([dl_path] if 'dl_path' in locals() else [])
        print(f"Error: {e}")
        await status_msg.edit(f"❌ Error occurred: {str(e)}")
