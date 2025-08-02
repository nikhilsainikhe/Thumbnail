import os
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("forward_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

media_groups = {}

@bot.on_message(filters.forwarded & filters.video)
async def handle_forwarded_video(bot, message: Message):
    if message.media_group_id:
        media_groups.setdefault(message.media_group_id, []).append(message)
    else:
        await process_video(bot, message)

@bot.on_message(filters.forwarded & filters.media_group)
async def handle_forwarded_album(bot, message: Message):
    media_groups.setdefault(message.media_group_id, []).append(message)

@bot.on_message(filters.text)
async def flush_media_groups(bot, message: Message):
    for group_id, messages in list(media_groups.items()):
        for msg in sorted(messages, key=lambda m: m.message_id):
            if msg.video:
                await process_video(bot, msg)
        del media_groups[group_id]

async def process_video(bot, message: Message):
    video = message.video
    if not video:
        return

    file_path = await bot.download_media(message)
    thumb_path = f"{file_path}_thumb.jpg"

    subprocess.run([
        "ffmpeg", "-ss", "00:00:10", "-i", file_path,
        "-vframes", "1", "-q:v", "2", "-y", thumb_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    sent_msg = await bot.send_video(
        chat_id=message.chat.id,
        video=file_path,
        caption=message.caption,
        thumb=thumb_path if os.path.exists(thumb_path) else None,
        supports_streaming=True,
        parse_mode="html"
    )

    try:
        await message.delete()
    except:
        pass

    os.remove(file_path)
    if os.path.exists(thumb_path):
        os.remove(thumb_path)

bot.run()
                                    
