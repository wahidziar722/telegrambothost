# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import re
import json
import threading
import time
from datetime import datetime
from flask import Flask, request

# ==================== CONFIG ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"
ADMIN_ID = "8518408753"

# Required channels
REQUIRED_CHANNELS = [
    {"username": "@SQFORCEZONE", "url": "https://t.me/SQFORCEZONE", "name": "SQ FORCE ZONE"},
    {"username": "@WahidModeX", "url": "https://t.me/WahidModeX", "name": "Wahid Mode X"}
]

# Bot creators
CREATORS = ["@Kingwahid", "@XFPro43"]

# Flask app
app = Flask(__name__)

# Bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Data storage
user_verified = {}
total_users = set()
users_file = "users.json"

# ==================== DATA FUNCTIONS ====================
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

# ==================== CHECK MEMBERSHIP (using bot API) ====================
def is_user_member(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            chat_member = bot.get_chat_member(channel["username"], user_id)
            if chat_member.status in ['left', 'kicked']:
                return False
        return True
    except Exception as e:
        print(f"Check error: {e}")
        return False

def get_not_joined_channels(user_id):
    not_joined = []
    for channel in REQUIRED_CHANNELS:
        try:
            chat_member = bot.get_chat_member(channel["username"], user_id)
            if chat_member.status in ['left', 'kicked']:
                not_joined.append(channel)
        except:
            not_joined.append(channel)
    return not_joined

# ==================== DOWNLOAD VIDEO ====================
def download_video(url, user_id):
    # Create a cookies file to avoid bot detection (optional but recommended)
    cookies_file = "cookies.txt"
    if not os.path.exists(cookies_file):
        with open(cookies_file, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
    
    download_path = f"downloads/{user_id}"
    os.makedirs(download_path, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
        'format': 'best[height<=720]',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookies_file,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Fix extension
            if not os.path.exists(filename):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_file = filename.rsplit('.', 1)[0] + ext
                    if os.path.exists(test_file):
                        filename = test_file
                        break
            
            # Extract stats
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

# ==================== BUTTONS ====================
def get_join_buttons():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in REQUIRED_CHANNELS:
        btn = InlineKeyboardButton(f"📢 Join {ch['name']}", url=ch['url'])
        keyboard.add(btn)
    verify_btn = InlineKeyboardButton("✅ I Have Joined - Verify", callback_data="verify")
    keyboard.add(verify_btn)
    return keyboard

def get_fail_buttons(not_joined):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in not_joined:
        btn = InlineKeyboardButton(f"📢 Join {ch['name']}", url=ch['url'])
        keyboard.add(btn)
    retry_btn = InlineKeyboardButton("🔄 Try Again", callback_data="verify")
    keyboard.add(retry_btn)
    return keyboard

def get_main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("📥 Download Video", callback_data="download")
    btn2 = InlineKeyboardButton("👨‍💻 Creators", callback_data="creators")
    btn3 = InlineKeyboardButton("📊 Stats", callback_data="stats")
    btn4 = InlineKeyboardButton("🎨 Sticker", callback_data="sticker")
    keyboard.add(btn1, btn2, btn3, btn4)
    return keyboard

# ==================== HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    update_user(user_id)
    total = len(total_users)
    
    welcome = f"""🚀 **Video Downloader Bot**

👥 **Total Users:** {total}+

📢 **You must join both channels to use this bot:**
{chr(10).join([f"• {ch['name']}" for ch in REQUIRED_CHANNELS])}

✅ After joining, click the button below."""
    
    bot.send_message(user_id, welcome, parse_mode='Markdown', reply_markup=get_join_buttons())

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_callback(call):
    user_id = call.from_user.id
    if is_user_member(user_id):
        user_verified[user_id] = True
        bot.edit_message_text("✅ **Verification Successful!**\n\nNow you can download videos.", user_id, call.message.message_id)
        bot.send_message(user_id, "📎 **Send me a video link:**", reply_markup=get_main_menu())
    else:
        not_joined = get_not_joined_channels(user_id)
        channels_text = "\n".join([f"❌ {ch['name']}" for ch in not_joined])
        bot.answer_callback_query(call.id, "Join all channels first!", show_alert=True)
        bot.edit_message_text(f"❌ **Not joined:**\n{channels_text}\n\nPlease join and verify again.", user_id, call.message.message_id, reply_markup=get_fail_buttons(not_joined))

@bot.callback_query_handler(func=lambda call: call.data == "download")
def download_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, "📎 **Send me the video link:**")

@bot.callback_query_handler(func=lambda call: call.data == "creators")
def creators_callback(call):
    text = f"👨‍💻 **Bot Creators:**\n{chr(10).join(CREATORS)}\n\n📢 **Channels:**\n@SQFORCEZONE\n@WahidModeX"
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats_callback(call):
    total = len(total_users)
    verified = len(user_verified)
    text = f"📊 **Stats**\n\n👥 Total Users: {total}\n✅ Verified: {verified}\n🟢 Status: Active"
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "sticker")
def sticker_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, "🎨 **Stickers coming soon!** Stay tuned @WahidModeX", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text
    
    # Check verification
    if not user_verified.get(user_id, False):
        if not is_user_member(user_id):
            not_joined = get_not_joined_channels(user_id)
            channels_text = "\n".join([f"❌ {ch['name']}" for ch in not_joined])
            bot.send_message(user_id, f"❌ **Access Denied!**\n\nJoin these channels:\n{channels_text}", reply_markup=get_fail_buttons(not_joined))
            return
        else:
            user_verified[user_id] = True
    
    # Extract URL
    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(text)
    if not urls:
        bot.send_message(user_id, "📎 **Send a valid video link** (YouTube, Instagram, TikTok, Facebook, Twitter)", reply_markup=get_main_menu())
        return
    
    url = urls[0]
    msg = bot.send_message(user_id, "📊 **Getting video info & downloading...**\nThis may take up to 30 seconds.")
    
    # Download
    video_path, stats = download_video(url, user_id)
    
    if video_path and os.path.exists(video_path):
        bot.edit_message_text("📤 **Uploading video...**", user_id, msg.message_id)
        caption = f"""✅ **Download Complete!**

📌 **Title:** {stats['title']}
👤 **Channel:** {stats['channel']}
⏱️ **Duration:** {stats['duration']}
❤️ **Likes:** {stats['likes']}
💬 **Comments:** {stats['comments']}
👁️ **Views:** {stats['views']}

🎬 Enjoy!"""
        try:
            with open(video_path, 'rb') as f:
                bot.send_video(user_id, f, caption=caption, parse_mode='Markdown', timeout=120)
            bot.delete_message(user_id, msg.message_id)
            # Cleanup
            os.remove(video_path)
            os.rmdir(f"downloads/{user_id}")
        except Exception as e:
            bot.edit_message_text(f"❌ **Upload error:** {str(e)[:100]}", user_id, msg.message_id)
    else:
        bot.edit_message_text("❌ **Download failed!**\n\nPossible reasons:\n• Invalid link\n• Private video\n• Unsupported platform\n• YouTube blocked (try another link)", user_id, msg.message_id)

# ==================== FLASK WEBHOOK (for Render) ====================
@app.route('/')
def home():
    return f"Bot running. Total users: {len(total_users)}"

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400

def set_webhook():
    # Use Render's public URL - you need to replace with your actual Render URL
    render_url = "https://your-bot-name.onrender.com"  # CHANGE THIS
    webhook_url = f"{render_url}/webhook/{BOT_TOKEN}"
    result = bot.set_webhook(url=webhook_url)
    print(f"Webhook set: {result}")

# ==================== MAIN ====================
if __name__ == "__main__":
    load_users()
    os.makedirs("downloads", exist_ok=True)
    
    # Remove webhook and start polling (simpler for Render)
    bot.remove_webhook()
    
    # Start bot polling in a separate thread
    def poll_bot():
        print("Bot polling started...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
    bot_thread = threading.Thread(target=poll_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server for health checks
    print("Flask server running on port 8080...")
    app.run(host='0.0.0.0', port=8080)
