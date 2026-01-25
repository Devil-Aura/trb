import os
import time
import shutil

def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + dic_powerN[n] + 'B'

def cleanup_files(file_paths):
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error removing {path}: {e}")

def get_readable_lang(lang_code):
    # Simple map, can be expanded or use a library
    langs = {
        'eng': 'English', 'hin': 'Hindi', 'tam': 'Tamil', 
        'jpn': 'Japanese', 'spa': 'Spanish', 'fre': 'French',
        'ger': 'German', 'rus': 'Russian', 'ita': 'Italian',
        'chi': 'Chinese', 'kor': 'Korean', 'ara': 'Arabic',
        'und': 'Undefined'
    }
    return langs.get(lang_code, lang_code)
