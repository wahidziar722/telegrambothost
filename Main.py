# -*- coding: utf-8 -*-
import asyncio
import os
import re
import json
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageMediaDocument
import yt_dlp
from flask import Flask, request
import threading

# ==================== CONFIG ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"
ADMIN_ID = 8518408753

# Required channels (must join)
REQUIRED_CHANNELS = [
    {"username": "SQFORCEZONE", "url": "https://t.me/SQFORCEZONE", "name": "SQ FORCE ZONE"},
    {"username": "WahidModeX", "url": "https://t.me/WahidModeX", "name": "Wahid Mode X"}
]

# Bot creators
CREATORS = ["@Kingwahid", "@XFPro43"]

# Create client
bot = TelegramClient('bot', api_id=6, api_hash='eb06d4abfb49dc3eeb1aeb98ae0f581e').start(bot_token=BOT_TOKEN)

# Flask app for health check
app = Flask(__name__)

# Data storage
user_verified = {}
total_users = set()

# ==================== DATA SAVE/LOAD ====================
def save_users():
    try:
        with open("users.json", "w") as f:
            json.dump(list(total_users), f)
    except:
        pass

def load_users():
    global total_users
    try:
        with open("users.json", "r") as f:
            data = json.load(f)
            total_users = set(data)
    except:
        total_users = set()

def update_user(user_id):
    total_users.add(str(user_id))
    save_users()

# ==================== CHECK MEMBERSHIP ====================
async def is_user_member(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            entity = await bot.get_entity(channel["username"])
            try:
                participant = await bot.get_participants(entity, limit=1)
                # Check if user is in channel
                async for p in bot.get_participants(entity):
                    if p.id == user_id:
                        break
                else:
                    return False
            except:
                return False
        return True
    except Exception as e:
        print(f"Check error: {e}")
        return False

# ==================== DOWNLOAD VIDEO WITH COOKIES ====================
def download_video(url, user_id):
    # Create cookies file if not exists (you can add your own cookies.txt)
    cookies_file = "cookies.txt"
    if not os.path.exists(cookies_file):
        # Create empty cookies file (may work for some sites)
        with open(cookies_file, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
    
    download_path = f"downloads/{user_id}"
    os.makedirs(download_path, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
        'format': 'best[height<=720]',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookies_file,  # Use cookies to avoid bot detection
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Fix extension if needed
            if not os.path.exists(filename):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_file = filename.rsplit('.', 1)[0] + ext
                    if os.path.exists(test_file):
                        filename = test_file
                        break
            
            # Get video stats
            stats = {
                'title': info.get('title', 'Unknown'),
                'channel': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'views': info.get('view_count', 0),
                'likes': info.get('like_count', 0),
                'comments': info.get('comment_count', 0),
            }
            return filename, stats
    except Exception as e:
        print(f"Download error: {e}")
        return None, None

# ==================== BOT HANDLERS ====================
@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    update_user(user_id)
    total = len(total_users)
    
    welcome_text = f"""🚀 **Welcome to Video Downloader Bot!**

📌 **Features:**
• Download videos from YouTube, Instagram, TikTok, Facebook, Twitter
• Shows likes, comments, views
• Fast and High Quality

👥 **Total Users:** {total}+

📢 **Please join both channels to use this bot:**
{chr(10).join([f"• {ch['name']}: {ch['url']}" for ch in REQUIRED_CHANNELS])}

✅ After joining, click the button below to verify."""

    buttons = [
        [Button.url(f"Join {ch['name']}", ch['url']) for ch in REQUIRED_CHANNELS],
        [Button.inline("✅ I Have Joined - Verify", b"verify")]
    ]
    await event.respond(welcome_text, buttons=buttons, link_preview=False)

@bot.on(events.CallbackQuery(data=b"verify"))
async def verify_handler(event):
    user_id = event.sender_id
    if await is_user_member(user_id):
        user_verified[user_id] = True
        await event.edit("✅ **Verification Successful!**\n\nYou can now use the bot.")
        buttons = [
            [Button.inline("📥 Download Video", b"download")],
            [Button.inline("👨‍💻 Creators", b"creators"), Button.inline("📊 Stats", b"stats")],
            [Button.inline("🎨 Sticker", b"sticker")]
        ]
        await event.respond("📎 **Send me a video link to download!**\n\nSupported:\nYouTube • Instagram • TikTok • Facebook • Twitter", buttons=buttons)
    else:
        await event.answer("Please join all channels first!", alert=True)
        # Show only unjoined channels
        not_joined = []
        for ch in REQUIRED_CHANNELS:
            entity = await bot.get_entity(ch["username"])
            try:
                async for p in bot.get_participants(entity):
                    if p.id == user_id:
                        break
                else:
                    not_joined.append(ch)
            except:
                not_joined.append(ch)
        fail_text = f"❌ **You haven't joined:**\n{chr(10).join([f'• {ch['name']}' for ch in not_joined])}\n\nPlease join and verify again."
        buttons = [[Button.url(f"Join {ch['name']}", ch['url'])] for ch in not_joined]
        buttons.append([Button.inline("🔄 Try Again", b"verify")])
        await event.edit(fail_text, buttons=buttons)

@bot.on(events.CallbackQuery(data=b"download"))
async def download_callback(event):
    await event.answer()
    await event.respond("📎 **Send me the video link:**")

@bot.on(events.CallbackQuery(data=b"creators"))
async def creators_callback(event):
    await event.answer()
    text = f"""👨‍💻 **Bot Creators:**\n{chr(10).join(CREATORS)}\n\n📢 **Our Channels:**\n@SQFORCEZONE\n@WahidModeX\n\n💡 For support: Contact creators"""
    await event.respond(text)

@bot.on(events.CallbackQuery(data=b"stats"))
async def stats_callback(event):
    await event.answer()
    total = len(total_users)
    verified = len(user_verified)
    text = f"""📊 **Bot Statistics**

👥 **Total Users:** {total}
✅ **Verified Users:** {verified}
🟢 **Bot Status:** Active
📅 **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
    await event.respond(text)

@bot.on(events.CallbackQuery(data=b"sticker"))
async def sticker_callback(event):
    await event.answer()
    text = "🎨 **Sticker Pack**\n\nComing soon! Stay tuned at @WahidModeX"
    await event.respond(text)

@bot.on(events.NewMessage(func=lambda e: e.is_private and not e.text.startswith('/')))
async def message_handler(event):
    user_id = event.sender_id
    text = event.text.strip()
    
    # Check verification
    if not user_verified.get(user_id, False):
        if not await is_user_member(user_id):
            await event.respond("❌ **Access Denied!** Please join channels first. Send /start")
            return
        else:
            user_verified[user_id] = True
    
    # Extract URL
    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(text)
    if not urls:
        await event.respond("📎 **Send a valid video link!**\n\nExamples:\n• https://youtube.com/watch?v=...\n• https://instagram.com/p/...")
        return
    
    url = urls[0]
    
    # Inform user
    msg = await event.respond("📊 **Getting video information...**")
    
    # Download
    video_path, stats = download_video(url, user_id)
    
    if video_path and os.path.exists(video_path):
        await msg.edit("📤 **Uploading video...**")
        
        # Prepare caption
        duration = stats.get('duration', 0)
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes}:{seconds:02d}"
        
        caption = f"""✅ **Download Complete!**

📌 **Title:** {stats.get('title', 'Unknown')}
👤 **Channel:** {stats.get('channel', 'Unknown')}
⏱️ **Duration:** {duration_str}
❤️ **Likes:** {stats.get('likes', 0):,}
💬 **Comments:** {stats.get('comments', 0):,}
👁️ **Views:** {stats.get('views', 0):,}

🎬 **Enjoy!**"""
        
        try:
            await event.client.send_file(
                user_id,
                video_path,
                caption=caption,
                supports_streaming=True
            )
            await msg.delete()
            # Cleanup
            os.remove(video_path)
            os.rmdir(f"downloads/{user_id}")
        except Exception as e:
            await msg.edit(f"❌ **Upload failed:** {str(e)[:100]}")
    else:
        await msg.edit("❌ **Download failed!**\n\nPossible reasons:\n• Link is invalid\n• Video is private\n• Unsupported platform\n• YouTube blocked (try another link)")

# ==================== FLASK HEALTH CHECK ====================
@app.route('/')
def home():
    return f"Bot is running! Total users: {len(total_users)}"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ==================== MAIN ====================
async def main():
    load_users()
    os.makedirs("downloads", exist_ok=True)
    
    # Create cookies file if not exists (you can replace with your actual cookies)
    if not os.path.exists("cookies.txt"):
        with open("cookies.txt", "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
    
    print("Bot started...")
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()

if __name__ == "__main__":
    # Start Flask in thread
    threading.Thread(target=run_flask, daemon=True).start()
    # Start bot
    asyncio.run(main())
