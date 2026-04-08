# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import re
import json
import threading
from flask import Flask, request

# ==================== CONFIG ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"

# Required channels
REQUIRED_CHANNELS = [
    {"username": "@SQFORCEZONE", "url": "https://t.me/SQFORCEZONE", "name": "SQ FORCE ZONE"},
    {"username": "@WahidModeX", "url": "https://t.me/WahidModeX", "name": "Wahid Mode X"}
]

# Bot creators
CREATORS = ["@Kingwahid", "@XFPro43"]

# Bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Store verified users
verified_users = set()
total_users = set()
users_file = "users.json"

# Flask app for health check
app = Flask(__name__)

def save_users():
    try:
        with open(users_file, "w") as f:
            json.dump(list(total_users), f)
    except:
        pass

def load_users():
    global total_users
    try:
        with open(users_file, "r") as f:
            data = json.load(f)
            total_users = set(data)
    except:
        total_users = set()

def update_user(user_id):
    total_users.add(str(user_id))
    save_users()

def is_user_member(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(ch["username"], user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

def get_join_buttons():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in REQUIRED_CHANNELS:
        keyboard.add(InlineKeyboardButton(f"Join {ch['username']}", url=ch['url']))
    keyboard.add(InlineKeyboardButton("✅ I have joined", callback_data="check"))
    return keyboard

# ==================== ENHANCED DOWNLOAD FUNCTION ====================
def download_video(url):
    os.makedirs("downloads", exist_ok=True)
    
    # Use cookies file
    cookies_file = "cookies.txt"
    if not os.path.exists(cookies_file):
        with open(cookies_file, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
    
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'best[height<=720]',
        'quiet': False,
        'no_warnings': False,
        'cookiefile': cookies_file,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'geo_bypass': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Fix extension if needed
            if not os.path.exists(filename):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test = filename.rsplit('.', 1)[0] + ext
                    if os.path.exists(test):
                        filename = test
                        break
            
            # Extract video info for caption
            duration = info.get('duration', 0)
            minutes = duration // 60
            seconds = duration % 60
            stats = {
                'title': info.get('title', 'Unknown'),
                'channel': info.get('uploader', 'Unknown'),
                'duration': f"{minutes}:{seconds:02d}",
                'views': f"{info.get('view_count', 0):,}",
                'likes': f"{info.get('like_count', 0):,}",
                'comments': f"{info.get('comment_count', 0):,}"
            }
            return filename, stats
    except Exception as e:
        print(f"Download error: {e}")
        return None, None

# ==================== BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    update_user(user_id)
    total = len(total_users)
    
    if user_id in verified_users:
        bot.reply_to(message, f"🎬 Welcome back! Total users: {total}. Send me a video link (YouTube, Instagram, TikTok, etc.) and I'll download it for you!")
        return
    
    text = f"📢 **You must join these channels first:**\n"
    for ch in REQUIRED_CHANNELS:
        text += f"• {ch['username']}\n"
    text += f"\n👥 **Total Users:** {total}+\n\nAfter joining, click the button below."
    bot.send_message(user_id, text, parse_mode='Markdown', reply_markup=get_join_buttons())

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_callback(call):
    user_id = call.from_user.id
    if is_user_member(user_id):
        verified_users.add(user_id)
        bot.edit_message_text("✅ **Verification successful!** Now send me a video link.", user_id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "You haven't joined both channels yet!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if user_id not in verified_users and not is_user_member(user_id):
        bot.reply_to(message, "❌ Please send /start and join the channels first.")
        return

    text = message.text
    url_match = re.search(r'https?://[^\s]+', text)
    if not url_match:
        bot.reply_to(message, "❌ Please send a valid video link.")
        return
    
    url = url_match.group(0)
    msg = bot.reply_to(message, "⏬ Downloading... This may take a few moments depending on the video size and server load.")
    
    video_path, stats = download_video(url)
    if video_path and os.path.exists(video_path):
        try:
            caption = f"✅ **{stats['title']}**\n\n⏱️ Duration: {stats['duration']}\n❤️ Likes: {stats['likes']} | 💬 Comments: {stats['comments']}\n👁️ Views: {stats['views']}\n\n🎬 Enjoy your video!"
            with open(video_path, 'rb') as v:
                bot.send_video(message.chat.id, v, caption=caption, parse_mode='Markdown', timeout=180)
            bot.delete_message(message.chat.id, msg.message_id)
            os.remove(video_path)
        except Exception as e:
            bot.edit_message_text(f"❌ Upload failed: {str(e)[:100]}", message.chat.id, msg.message_id)
    else:
        bot.edit_message_text("❌ Download failed. Please check the link and try again. The video might be private, age-restricted, or from an unsupported source.", message.chat.id, msg.message_id)

# ==================== FLASK HEALTH CHECK ====================
@app.route('/')
def home():
    return f"Bot is running! Total users: {len(total_users)}"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    load_users()
    os.makedirs("downloads", exist_ok=True)
    
    # Remove webhook and start polling
    bot.remove_webhook()
    
    # Start bot polling in a background thread
    def poll_bot():
        print("Bot polling started...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
    bot_thread = threading.Thread(target=poll_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    print("Flask server running on port 8080...")
    run_flask()
