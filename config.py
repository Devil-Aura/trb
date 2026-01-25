import os
import json

class Config:
    # Telegram API (Get these from https://my.telegram.org)
    API_ID = int(os.environ.get("API_ID", ""))  # Replace with actual
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # Owners and Admins
    OWNER_ID = int(os.environ.get("OWNER_ID", ""))
    ADMINS = set([OWNER_ID])
    
    # Bot Mode
    # 'private': Only owner & admins
    # 'public': Everyone
    BOT_MODE = "private" 
    
    # Concurrent Task Limit
    MAX_CONCURRENT_TASKS = 4
    
    # Default output format: 'document' or 'video'
    DEFAULT_UPLOAD_MODE = "document"
    
    # Configuration persistence
    CONFIG_FILE = "bot_config.json"

    @staticmethod
    def load_config():
        if os.path.exists(Config.CONFIG_FILE):
            try:
                with open(Config.CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    Config.BOT_MODE = data.get("mode", Config.BOT_MODE)
                    Config.DEFAULT_UPLOAD_MODE = data.get("upload_mode", Config.DEFAULT_UPLOAD_MODE)
                    Config.ADMINS = set(data.get("admins", [Config.OWNER_ID]))
            except Exception as e:
                print(f"Error loading config: {e}")

    @staticmethod
    def save_config():
        data = {
            "mode": Config.BOT_MODE,
            "upload_mode": Config.DEFAULT_UPLOAD_MODE,
            "admins": list(Config.ADMINS)
        }
        with open(Config.CONFIG_FILE, "w") as f:
            json.dump(data, f)
