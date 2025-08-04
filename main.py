import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("yt-dlp-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def clean_url(url: str) -> str:
    # Convert embed to watch URL if needed
    embed_match = re.search(r"youtube\.com/embed/([a-zA-Z0-9_-]+)", url)
    if embed_match:
        video_id = embed_match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def download_video(url: str, file_path: str) -> str:
    ydl_opts = {
        'format': 'bv*+ba/best',
        'outtmpl': file_path,
        'merge_output_format': 'mkv',
        'noplaylist': True,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mkv',
        }],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return file_path

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text("Send me a YouTube URL (even embed one), and I’ll send back the MKV video.")

@app.on_message(filters.text & filters.private)
async def download_handler(client, message: Message):
    url = clean_url(message.text.strip())
    await message.reply("🔄 Downloading... please wait.")

    try:
        file_name = "downloaded.mkv"
        download_video(url, file_name)
        await message.reply_video(file_name, caption="✅ Done!", supports_streaming=True)
        os.remove(file_name)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

app.run()
