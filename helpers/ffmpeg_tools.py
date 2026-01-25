import json
import asyncio
import os
from .utils import get_readable_lang

async def get_media_info(file_path):
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", file_path
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        return None
    
    data = json.loads(stdout)
    streams = data.get("streams", [])
    
    info = {
        "video": [],
        "audio": [],
        "subtitle": []
    }
    
    for i, stream in enumerate(streams):
        stream_type = stream.get("codec_type")
        lang = stream.get("tags", {}).get("language", "und")
        title = stream.get("tags", {}).get("title", "")
        codec = stream.get("codec_name", "")
        index = stream.get("index")
        
        s_info = {
            "index": index,
            "lang": lang,
            "title": title,
            "codec": codec,
            "label": f"{get_readable_lang(lang)} ({title})" if title else get_readable_lang(lang)
        }
        
        if stream_type == "video":
            info["video"].append(s_info)
        elif stream_type == "audio":
            info["audio"].append(s_info)
        elif stream_type == "subtitle":
            info["subtitle"].append(s_info)
            
    return info

async def process_video(input_path, output_path, keep_audio_indices, keep_subtitle_indices, audio_streams, subtitle_streams):
    # Logic to reorder streams based on requirements
    # 1. Hindi audio first & default
    # 2. English subtitles first but NOT default
    
    # Filter streams to keep
    audio_to_map = [s for s in audio_streams if s['index'] in keep_audio_indices]
    subs_to_map = [s for s in subtitle_streams if s['index'] in keep_subtitle_indices]
    
    # Sort Audio: Hindi first, then English, then others
    def audio_sort_key(s):
        lang = s['lang'].lower()
        if 'hin' in lang: return 0
        if 'eng' in lang: return 1
        return 2
    
    audio_to_map.sort(key=audio_sort_key)
    
    # Sort Subtitles: English first, then others
    def sub_sort_key(s):
        lang = s['lang'].lower()
        if 'eng' in lang: return 0
        return 1
        
    subs_to_map.sort(key=sub_sort_key)
    
    # Build FFmpeg command
    cmd = ["ffmpeg", "-i", input_path, "-map", "0:v:0"] # Map first video stream always
    
    # Map Audio
    for s in audio_to_map:
        cmd.extend(["-map", f"0:{s['index']}"])
        
    # Map Subtitles
    for s in subs_to_map:
        cmd.extend(["-map", f"0:{s['index']}"])
        
    # Set Dispositions (Default flags)
    cmd.extend(["-c", "copy"]) # Copy codecs to avoid re-encoding
    
    # Audio Dispositions
    if audio_to_map:
        # First audio (Hindi) is default
        cmd.extend([f"-disposition:a:0", "default"])
        # Remove default from others
        for i in range(1, len(audio_to_map)):
            cmd.extend([f"-disposition:a:{i}", "0"])
            
    # Subtitle Dispositions
    if subs_to_map:
        # English subtitles first (sorted 0) but NOT default
        for i in range(len(subs_to_map)):
            cmd.extend([f"-disposition:s:{i}", "0"])

    cmd.append(output_path)
    
    print(f"Running FFmpeg: {' '.join(cmd)}")
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # We can capture stderr for progress parsing if needed
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        print(f"FFmpeg Error: {stderr.decode()}")
        return False
        
    return True
