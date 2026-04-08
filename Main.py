# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import re
from flask import Flask
import threading

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"
ADMIN_ID = "8518408753"

# Required channels
REQUIRED_CHANNELS = [
    {"username": "@SQFORCEZONE", "url": "https://t.me/SQFORCEZONE", "name": "SQ FORCE ZONE"},
    {"username": "@WahidModeX", "url": "https://t.me/WahidModeX", "name": "Wahid Mode X"}
]

# Bot creators
CREATORS = ["@Kingwahid", "@XFPro43"]

# Bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Store verified users (in memory, but will reset on restart)
verified_users = set()

# Flask app for health check
app = Flask(__name__)

# ==================== CHECK MEMBERSHIP ====================
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

# ==================== ADVANCED DOWNLOAD FUNCTION ====================
def download_video(url):
    """
    This function uses yt-dlp with advanced options to ensure maximum
    compatibility and success in downloading videos from various platforms.
    """
    os.makedirs("downloads", exist_ok=True)

    # yt-dlp advanced configuration for maximum compatibility
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'nooverwrites': True,
        'continuedl': True,
        'cookiefile': 'cookies.txt',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'geo_bypass': True,
    }

    try:
        # Attempt to download with the advanced configuration
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # Check if the file was created, handle different extensions
            if not os.path.exists(filename):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test = filename.rsplit('.', 1)[0] + ext
                    if os.path.exists(test):
                        filename = test
                        break

            # Extract video information for the user
            video_info = {
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration', 0),
                'likes': info.get('like_count', 0),
                'dislikes': info.get('dislike_count', 0),
                'view_count': info.get('view_count', 0),
            }
            return filename, video_info

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None

# ==================== BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in verified_users:
        bot.reply_to(message, "🎬 Welcome back! Send me a video link from YouTube, Instagram, TikTok, Facebook, Twitter, and more. I'll download it for you!")
        return

    text = "📢 **You must join these channels first:**\n"
    for ch in REQUIRED_CHANNELS:
        text += f"• {ch['username']}\n"
    text += "\nAfter joining, click the button below."
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

    video_path, info = download_video(url)
    if video_path and os.path.exists(video_path):
        try:
            # Prepare a detailed caption
            duration = info['duration']
            minutes = duration // 60
            seconds = duration % 60
            caption = (
                f"✅ **{info['title']}**\n\n"
                f"⏱️ Duration: {minutes}:{seconds:02d}\n"
                f"❤️ Likes: {info['likes']:,} | 👎 Dislikes: {info['dislikes']:,}\n"
                f"👁️ Views: {info['view_count']:,}\n\n"
                f"🎬 Enjoy your video!"
            )
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
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot started...")
    bot.infinity_polling()
