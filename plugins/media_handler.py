import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from helpers.ffmpeg_tools import get_media_info, process_video
from helpers.keyboards import get_track_selection_keyboard
from helpers.utils import cleanup_files

# ================= QUEUE INIT =================
if not hasattr(Client, "task_queue"):
    Client.task_queue = asyncio.Queue()

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

    # 3. QUEUE (no rejection)
    await Client.task_queue.put(1)
    await message.reply_text("📥 Added to queue. Please wait…")

    status_msg = await message.reply_text("⬇️ Downloading media to detect tracks...")

    try:
        await client.task_semaphore.acquire()
        Client.task_queue.get_nowait()
        Client.task_queue.task_done()

        task_id = f"{message.from_user.id}_{message.id}"
        filename = media.file_name or "video.mp4"
        dl_path = f"downloads/{task_id}_{filename}"

        file_path = await reply.download(file_name=dl_path)
        if not file_path:
            client.task_semaphore.release()
            return await status_msg.edit("❌ Download failed.")

        await status_msg.edit("🕵️ Detecting tracks...")
        info = await get_media_info(file_path)

        if not info:
            cleanup_files([file_path])
            client.task_semaphore.release()
            return await status_msg.edit("❌ Failed to detect media info.")

        # -------- QUICK COMMANDS --------
        if cmd in ["h", "he"]:
            await status_msg.edit("⚙️ Quick processing...")

            keep_audio = []
            for s in info['audio']:
                lang = (s.get('lang') or "").lower()
                if 'hin' in lang or (cmd == "he" and 'eng' in lang):
                    keep_audio.append(s['index'])

            keep_subs = []
            for s in info['subtitle']:
                lang = (s.get('lang') or "").lower()
                title = (s.get('title') or "").lower()
                if 'eng' in lang or ('hin' in lang and 'sign' in title):
                    keep_subs.append(s['index'])
                elif not lang or lang == 'und':
                    if any(x in title for x in ['sign', 'song']):
                        keep_subs.append(s['index'])

            output_path = f"downloads/processed_{task_id}.mkv"
            success = await process_video(
                file_path, output_path,
                keep_audio, keep_subs,
                info['audio'], info['subtitle']
            )

            if success:
                await status_msg.edit("⬆️ Uploading...")
                caption = f"✅ **Quick processed (/{cmd})**\n\n📄 `{filename}`"
                if Config.DEFAULT_UPLOAD_MODE == "video":
                    await client.send_video(message.chat.id, output_path, caption=caption)
                else:
                    await client.send_document(message.chat.id, output_path, caption=caption)
                await status_msg.delete()
            else:
                await status_msg.edit("❌ Processing failed.")

            cleanup_files([file_path, output_path])
            client.task_semaphore.release()
            return

        # -------- NORMAL FLOW --------
        selected_audio = set()
        selected_subs = set()

        if cmd in ["remallaudio", "remall"]:
            selected_audio = {s['index'] for s in info['audio']}
        if cmd in ["remallsubtitles", "remall"]:
            selected_subs = {s['index'] for s in info['subtitle']}

        current_view = "audio"
        if cmd in ["remsubtitles", "remallsubtitles"]:
            current_view = "sub"

        client.active_tasks[message.from_user.id] = {
            "task_id": task_id,
            "input_path": file_path,
            "info": info,
            "selected_audio": selected_audio,
            "selected_subs": selected_subs,
            "status_msg": status_msg,
            "current_view": current_view,
            "page": 0,
            "filename": filename
        }

        if current_view == "audio":
            keyboard = get_track_selection_keyboard(info['audio'], selected_audio, 0, True)
            await status_msg.edit("🔊 Select Audio Tracks to REMOVE:", reply_markup=keyboard)
        else:
            keyboard = get_track_selection_keyboard(info['subtitle'], selected_subs, 0, False)
            await status_msg.edit("📝 Select Subtitle Tracks to REMOVE:", reply_markup=keyboard)

    except Exception as e:
        cleanup_files([file_path]) if 'file_path' in locals() else None
        client.task_semaphore.release()
        await status_msg.edit(f"❌ Error: {e}")
