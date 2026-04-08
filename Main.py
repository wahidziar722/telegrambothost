# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import re
import threading
from flask import Flask

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"

# Channel membership required? (set to False if you don't want it)
REQUIRE_JOIN = True
CHANNELS = [
    {"username": "@SQFORCEZONE", "url": "https://t.me/SQFORCEZONE"},
    {"username": "@WahidModeX", "url": "https://t.me/WahidModeX"}
]

# Bot creators
CREATORS = ["@Kingwahid", "@XFPro43"]

# Initialize bot and Flask
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Store verified users
verified_users = set()

# ==================== MEMBERSHIP CHECK ====================
def is_member(user_id):
    if not REQUIRE_JOIN:
        return True
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch["username"], user_id).status
            if status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

def join_buttons():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        keyboard.add(InlineKeyboardButton(f"Join {ch['username']}", url=ch['url']))
    keyboard.add(InlineKeyboardButton("✅ I have joined", callback_data="check"))
    return keyboard

# ==================== POWERFUL DOWNLOAD FUNCTION ====================
def download_video(url):
    os.makedirs("downloads", exist_ok=True)
    
    # Quality levels from best to worst
    quality_levels = [
        'best[height<=720]',
        'best[height<=480]',
        'best[height<=360]',
        'worst'
    ]
    
    for quality in quality_levels:
        try:
            ydl_opts = {
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'format': quality,
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'merge_output_format': 'mp4',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Check if file exists, try different extensions
                if not os.path.exists(filename):
                    for ext in ['.mp4', '.webm', '.mkv']:
                        test = filename.rsplit('.', 1)[0] + ext
                        if os.path.exists(test):
                            filename = test
                            break
                
                # Skip if file > 48MB (Telegram limit is 50MB)
                if os.path.getsize(filename) > 48 * 1024 * 1024:
                    os.remove(filename)
                    continue
                
                # Extract video stats
                duration = info.get('duration', 0)
                minutes = duration // 60
                seconds = duration % 60
                stats = {
                    'title': info.get('title', 'Unknown'),
                    'duration': f"{minutes}:{seconds:02d}",
                    'likes': f"{info.get('like_count', 0):,}",
                    'views': f"{info.get('view_count', 0):,}"
                }
                return filename, stats
        except Exception as e:
            print(f"Quality {quality} failed: {e}")
            continue
    
    return None, None

# ==================== TELEGRAM HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    if REQUIRE_JOIN and not is_member(user_id):
        bot.send_message(user_id, "📢 **Please join our channels first:**", reply_markup=join_buttons())
        return
    
    verified_users.add(user_id)
    bot.reply_to(message, "🎬 **Send me any video link!**\n\nSupported:\nYouTube • Instagram • TikTok • Facebook • Twitter • Reddit • Twitch • Vimeo • Dailymotion")

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_callback(call):
    user_id = call.from_user.id
    if is_member(user_id):
        verified_users.add(user_id)
        bot.edit_message_text("✅ **Verification successful!** Now send me a video link.", user_id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "You haven't joined both channels yet!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    if REQUIRE_JOIN and user_id not in verified_users and not is_member(user_id):
        bot.send_message(user_id, "❌ Please send /start and join the channels first.")
        return
    
    # Extract URL from message
    urls = re.findall(r'https?://[^\s]+', message.text)
    if not urls:
        bot.reply_to(message, "❌ Please send a valid video link.")
        return
    
    url = urls[0]
    msg = bot.reply_to(message, "⏬ **Downloading...**\nThis may take up to 30 seconds.")
    
    video_path, stats = download_video(url)
    
    if video_path and os.path.exists(video_path):
        try:
            caption = f"✅ **{stats['title']}**\n⏱️ Duration: {stats['duration']}\n❤️ Likes: {stats['likes']}\n👁️ Views: {stats['views']}\n\n🎬 Enjoy!"
            with open(video_path, 'rb') as v:
                bot.send_video(user_id, v, caption=caption, timeout=180)
            bot.delete_message(user_id, msg.message_id)
            os.remove(video_path)
        except Exception as e:
            bot.edit_message_text(f"❌ Upload failed: {str(e)[:100]}", user_id, msg.message_id)
    else:
        bot.edit_message_text("❌ **Download failed!**\n\nPossible reasons:\n• Invalid link\n• Private video\n• Video too long (over 50MB)\n• Unsupported platform\n\nContact @Kingwahid for help.", user_id, msg.message_id)

# ==================== FLASK HEALTH CHECK (keeps Render alive) ====================
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ==================== MAIN ====================
if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    # Start Flask in background thread
    threading.Thread(target=run_flask, daemon=True).start()
    # Start bot polling
    print("Bot started successfully!")
    bot.infinity_polling()
