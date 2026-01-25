from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

@Client.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "👋 **Welcome to Track Remover Bot!**\n\n"
        "I can help you remove Audio and Subtitle tracks from videos.\n"
        "Just reply to a video with `/tk` to start.\n\n"
        "**Features:**\n"
        "• Remove specific Audio/Subtitle tracks\n"
        "• Smart default selection rules\n"
        "• High speed processing\n\n"
        "Use `/help` for commands."
    )

@Client.on_message(filters.command("help"))
async def help_handler(client: Client, message: Message):
    text = (
        "**📚 Help Menu**\n\n"
        "**/tk** - Reply to a video to start removing tracks\n"
        "**/h** - Quick keep Hindi audio + English subtitles\n"
        "**/he** - Quick keep Hindi/English audio + English subtitles\n"
        "**/mode** - Switch between Private/Public mode (Owner only)\n"
        "**/config** - Configure auto-remove settings\n"
        "**/media** - Toggle output format (Video/Document)\n"
        "**/cancel** - Cancel current task\n\n"
        "**Admin Commands:**\n"
        "**/addadmin** - Add a new admin\n"
        "**/remadmin** - Remove an admin\n"
        "**/admins** - List admins"
    )
    await message.reply_text(text)

@Client.on_message(filters.command("mode"))
async def mode_handler(client: Client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        return await message.reply_text("❌ Only Owner can use this command.")
    
    # Toggle Mode
    if Config.BOT_MODE == "private":
        Config.BOT_MODE = "public"
    else:
        Config.BOT_MODE = "private"
        
    Config.save_config()
    await message.reply_text(f"✅ Bot mode changed to: **{Config.BOT_MODE.title()}**")

@Client.on_message(filters.command("media"))
async def media_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS:
        return await message.reply_text("❌ Only Admins can use this command.")
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Video " + ("✅" if Config.DEFAULT_UPLOAD_MODE == "video" else ""), callback_data="set_upload_video"),
            InlineKeyboardButton("Document " + ("✅" if Config.DEFAULT_UPLOAD_MODE == "document" else ""), callback_data="set_upload_document")
        ]
    ])
    await message.reply_text("Select Output Upload Type:", reply_markup=keyboard)

@Client.on_message(filters.command("config"))
async def config_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS:
        return await message.reply_text("❌ Only Admins can use this command.")
        
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Default Template", callback_data="config_default")],
        [InlineKeyboardButton("Manual Mode", callback_data="config_manual")],
        [InlineKeyboardButton("Hindi + English", callback_data="config_hin_eng")]
    ])
    await message.reply_text("**⚙️ Configuration Settings**\nChoose a preset:", reply_markup=keyboard)
