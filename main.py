import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("yt_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def convert_embed_to_watch(url: str) -> str:
    if "youtube.com/embed/" in url:
        video_id = url.split("/embed/")[-1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url


@app.on_message(filters.command("yt") & filters.private)
async def download_youtube(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("📥 YouTube link do: `/yt <link>`", quote=True)

    url = convert_embed_to_watch(message.command[1])
    msg = await message.reply("⏳ Downloading & processing...")

    try:
        subprocess.run(
            [
                "yt-dlp",
                "-f", "bv*+ba[ext=mp4]/b[ext=mp4]",
                "--merge-output-format", "mp4",
                "-o", "video.%(ext)s",
                url
            ],
            check=True
        )

        await msg.edit("📤 Uploading to Telegram...")
        await message.reply_video("video.mp4", supports_streaming=True, caption="🎬 Streamable video without cookies!")
        os.remove("video.mp4")

    except subprocess.CalledProcessError:
        await msg.edit("❌ Video download failed. Shayad age restriction ho.")
    except Exception as e:
        await msg.edit(f"⚠️ Error: `{e}`")


app.run()
