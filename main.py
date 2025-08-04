# main.py

import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL

API_ID = int(os.getenv("API_ID", 123456))  # Replace in .env or Heroku config
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

bot = Client("yt-dl-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def clean_url(url):
    if "youtube.com/embed/" in url:
        return url.replace("embed/", "watch?v=")
    return url


def download_video(url, output_path="downloads/video.%(ext)s"):
    ydl_opts = {
        "format": "best[ext=mp4][vcodec^=avc1]/best",
        "outtmpl": output_path,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


@bot.on_message(filters.command("start"))
async def start_cmd(_, m: Message):
    await m.reply("👋 Send me a YouTube video link to download (even embed URLs supported).")


@bot.on_message(filters.text & filters.private)
async def download_handler(_, m: Message):
    url = m.text.strip()

    if not re.match(r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/", url):
        await m.reply("❌ Invalid YouTube link.")
        return

    await m.reply("🔄 Processing your video...")

    try:
        real_url = clean_url(url)
        path = download_video(real_url)
        await m.reply_video(video=path, caption="✅ Here's your video", supports_streaming=True)
    except Exception as e:
        await m.reply(f"❌ Failed to download: `{e}`")


if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.mkdir("downloads")
    bot.run()
