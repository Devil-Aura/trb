import os
from pyrogram import Client
from pyrogram.types import CallbackQuery
from config import Config
from helpers.keyboards import get_track_selection_keyboard
from helpers.ffmpeg_tools import process_video
from helpers.utils import cleanup_files

@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    
    # --- Configuration Callbacks ---
    if data.startswith("set_upload_"):
        mode = data.split("_")[-1]
        Config.DEFAULT_UPLOAD_MODE = mode
        Config.save_config()
        await query.answer(f"Upload mode set to: {mode.title()}")
        await query.message.delete()
        return

    if data.startswith("config_"):
        # Just ack for now, maybe set a flag in Config if logic requires
        # User requested specific behavior for these buttons in /config menu
        await query.answer("Configuration updated (Mock).")
        return

    # --- Task Callbacks ---
    if user_id not in client.active_tasks:
        await query.answer("❌ Task expired or not found.", show_alert=True)
        return
        
    task = client.active_tasks[user_id]
    info = task['info']
    
    # Toggle Selection
    if data.startswith("toggle_"):
        _, idx, page, track_type = data.split("_")
        idx = int(idx)
        page = int(page)
        
        target_set = task['selected_audio'] if track_type == 'audio' else task['selected_subs']
        
        if idx in target_set:
            target_set.remove(idx)
        else:
            target_set.add(idx)
            
        # Refresh Keyboard
        tracks = info['audio'] if track_type == 'audio' else info['subtitle']
        keyboard = get_track_selection_keyboard(tracks, target_set, page, is_audio=(track_type=='audio'))
        try:
            await query.edit_message_reply_markup(reply_markup=keyboard)
        except:
            pass # Message not modified
        await query.answer()
        return

    # Pagination
    if data.startswith("page_"):
        _, page, track_type = data.split("_")
        page = int(page)
        task["page"] = int(page)
        
        tracks = info['audio'] if track_type == 'audio' else info['subtitle']
        target_set = task['selected_audio'] if track_type == 'audio' else task['selected_subs']
        
        keyboard = get_track_selection_keyboard(tracks, target_set, page, is_audio=(track_type=='audio'))
        await query.edit_message_text(
            f"Select {'Audio' if track_type=='audio' else 'Subtitle'} Tracks to REMOVE:",
            reply_markup=keyboard
        )
        return

    # Switch View
    if data == "switch_to_subs":
        if not info['subtitle']:
            await query.answer("❌ No Subtitles found.", show_alert=True)
            return
        task["current_view"] = "sub"
        task["page"] = 0
        keyboard = get_track_selection_keyboard(info['subtitle'], task['selected_subs'], 0, is_audio=False)
        await query.edit_message_text("📝 Select Subtitle Tracks to REMOVE:", reply_markup=keyboard)
        return

    if data == "switch_to_audio":
        if not info['audio']:
            await query.answer("❌ No Audio tracks found.", show_alert=True)
            return
        task["current_view"] = "audio"
        task["page"] = 0
        keyboard = get_track_selection_keyboard(info['audio'], task['selected_audio'], 0, is_audio=True)
        await query.edit_message_text("🔊 Select Audio Tracks to REMOVE:", reply_markup=keyboard)
        return

    # Done Processing
    if data == "process_done":
        await query.message.edit("⚙️ Processing video... Please wait.")
        
        # Determine tracks to KEEP
        # We KEEP indices NOT in selected sets
        keep_audio = [s['index'] for s in info['audio'] if s['index'] not in task['selected_audio']]
        keep_subs = [s['index'] for s in info['subtitle'] if s['index'] not in task['selected_subs']]
        
        # Prepare output path
        output_path = f"downloads/processed_{task['task_id']}.mkv"
        
        success = await process_video(
            task['input_path'], 
            output_path, 
            keep_audio, 
            keep_subs,
            info['audio'],
            info['subtitle']
        )
        
        if success:
            await query.message.edit("⬆️ Uploading processed file...")
            
            filename = task.get("filename", "video.mp4")
            caption = f"✅ **Processed with Track Remover Bot**\n\n📄 **Filename:** `{filename}`"
            
            try:
                if Config.DEFAULT_UPLOAD_MODE == "video":
                    await client.send_video(
                        chat_id=query.message.chat.id,
                        video=output_path,
                        caption=caption
                    )
                else:
                    await client.send_document(
                        chat_id=query.message.chat.id,
                        document=output_path,
                        caption=caption
                    )
                await query.message.delete()
            except Exception as e:
                await query.message.edit(f"❌ Upload failed: {e}")
        else:
            await query.message.edit("❌ Processing failed.")
            
        # Cleanup
        cleanup_files([task['input_path'], output_path])
        del client.active_tasks[user_id]
        client.task_semaphore.release()
