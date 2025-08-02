import os
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("forward_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Handle single video or media group (album) forwarded messages
@bot.on_message(filters.forwarded & filters.video)
async def handle_forwarded_video(bot, message: Message):
    await process_video(bot, message)

@bot.on_message(filters.forwarded & filters.media_group)
async def handle_forwarded_album(bot, message: Message):
    # Media group: collect all parts
    media_group_id = message.media_group_id
    album = [message]
    async for msg in bot.search_messages(chat_id=message.chat.id, filter=filters.media_group, limit=20):
        if msg.media_group_id == media_group_id and msg.message_id != message.message_id:
            album.append(msg)
    for msg in sorted(album, key=lambda m: m.message_id):
        if msg.video:
            await process_video(bot, msg)

async def process_video(bot, message: Message):
    video = message.video
    if not video:
        return

    file_path = await bot.download_media(message)
    thumb_path = f"{file_path}_thumb.jpg"

    # Generate thumbnail at 10 seconds
    subprocess.run([
        "ffmpeg", "-ss", "00:00:10", "-i", file_path,
        "-vframes", "1", "-q:v", "2", thumb_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Repost the video with same caption and generated thumbnail
    await bot.send_video(
        chat_id=message.chat.id,
        video=file_path,
        caption=message.caption,
        thumb=thumb_path if os.path.exists(thumb_path) else None,
        supports_streaming=True
    )

    os.remove(file_path)
    if os.path.exists(thumb_path):
        os.remove(thumb_path)

bot.run()
