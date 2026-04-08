# -*- coding: utf-8 -*-
import telebot
import yt_dlp
import os
import re
from flask import Flask
import threading

# ==================== CONFIG ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"

# Bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Flask app for health check (to keep Render alive)
app = Flask(__name__)

# ==================== DOWNLOAD FUNCTION ====================
def download_video(url):
    os.makedirs("downloads", exist_ok=True)
    
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'best[height<=720]',  # Try 720p
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
            
            title = info.get('title', 'Video')
            return filename, title
    except Exception as e:
        print(f"Download error: {e}")
        return None, None

# ==================== BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎬 Send me any video link (YouTube, Instagram, TikTok, Facebook, Twitter, etc.) and I'll download it for you!")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text
    # Extract URL
    url_match = re.search(r'https?://[^\s]+', text)
    if not url_match:
        bot.reply_to(message, "❌ Please send a valid video link.")
        return
    
    url = url_match.group(0)
    msg = bot.reply_to(message, "⏬ Downloading... Please wait (up to 30 sec).")
    
    video_path, title = download_video(url)
    
    if video_path and os.path.exists(video_path):
        try:
            with open(video_path, 'rb') as v:
                bot.send_video(message.chat.id, v, caption=f"✅ {title}", timeout=120)
            bot.delete_message(message.chat.id, msg.message_id)
            os.remove(video_path)
        except Exception as e:
            bot.edit_message_text(f"❌ Upload failed: {str(e)[:100]}", message.chat.id, msg.message_id)
    else:
        bot.edit_message_text("❌ Download failed. Check link or try another.", message.chat.id, msg.message_id)

# ==================== FLASK HEALTH CHECK ====================
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ==================== MAIN ====================
if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    # Start Flask in background
    threading.Thread(target=run_flask, daemon=True).start()
    # Start bot
    print("Bot started...")
    bot.infinity_polling()
