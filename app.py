import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("yt_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

download_dir = "downloads"
os.makedirs(download_dir, exist_ok=True)


def get_formats(url):
    ydl_opts = {"quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])
        quality_buttons = []

        for fmt in formats:
            vcodec = fmt.get("vcodec", "")
            acodec = fmt.get("acodec", "")
            ext = fmt.get("ext", "")
            if (
                vcodec.startswith("avc1")
                and acodec.startswith("mp4a")
                and ext in ["mp4", "mkv"]
                and fmt.get("filesize", 0) < 49 * 1024 * 1024  # under 50MB for bots
            ):
                label = f'{fmt["format_id"]} - {fmt.get("format_note") or fmt.get("height", "NA")}p'
                quality_buttons.append((label, fmt["format_id"]))
        return info["title"], quality_buttons


async def download_video(url, format_id):
    ydl_opts = {
        "format": format_id,
        "outtmpl": os.path.join(download_dir, "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


@app.on_message(filters.private & filters.text & ~filters.command(["start"]))
async def get_link(client, message):
    url = message.text.strip()

    if "youtube.com" not in url and "youtu.be" not in url:
        await message.reply("❌ Invalid YouTube URL.")
        return

    msg = await message.reply("🔍 Fetching available formats...")

    try:
        title, formats = get_formats(url)
    except Exception as e:
        await msg.edit(f"❌ Failed to fetch formats:\n`{e}`")
        return

    if not formats:
        await msg.edit("❌ No streamable formats found under 50MB.")
        return

    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"dl|{url}|{fid}")]
        for text, fid in formats[:15]
    ]
    await msg.edit(
        f"🎬 **{title}**\nSelect a quality to download:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


@app.on_callback_query(filters.regex(r"dl\|"))
async def format_selected(client, callback_query):
    _, url, format_id = callback_query.data.split("|")
    await callback_query.answer("📥 Downloading...")

    msg = await callback_query.message.edit("⏬ Downloading video...")

    try:
        await asyncio.to_thread(download_video, url, format_id)
    except Exception as e:
        await msg.edit(f"❌ Download failed:\n`{e}`")
        return

    for file in os.listdir(download_dir):
        if file.endswith((".mp4", ".mkv")):
            path = os.path.join(download_dir, file)
            try:
                await callback_query.message.reply_video(
                    video=path, caption="✅ Download complete.", supports_streaming=True
                )
            except Exception as e:
                await callback_query.message.reply_text(f"⚠️ Failed to send video:\n`{e}`")
            os.remove(path)

    await msg.delete()


app.run()
