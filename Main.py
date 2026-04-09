# -*- coding: utf-8 -*-
import telebot
import yt_dlp
import os
import re
import threading
from flask import Flask

# ==================== TOKEN ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Create downloads folder
os.makedirs('downloads', exist_ok=True)

# ==================== DOWNLOAD FUNCTION ====================
def download_video(url):
    """Download video from any platform"""
    
    opts = {
        'format': 'best[height<=480]/best',  # Best quality under 480p
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    # Use cookies if available
    if os.path.exists('cookies.txt'):
        opts['cookiefile'] = 'cookies.txt'
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Fix filename if needed
            if not os.path.exists(filename):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test = filename.rsplit('.', 1)[0] + ext
                    if os.path.exists(test):
                        filename = test
                        break
            
            # Get video info
            duration = info.get('duration', 0)
            title = info.get('title', 'Video')[:60]
            
            return filename, title, duration
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

# ==================== BOT COMMANDS ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(
        message, 
        "🎬 *Video Downloader Bot*\n\nSend me any video link from:\n✅ YouTube\n✅ TikTok\n✅ Facebook\n✅ Instagram\n✅ Twitter/X\n✅ Reddit\n\n⚡ Just send the link!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    url = message.text.strip()
    
    # Extract URL from text
    urls = re.findall(r'https?://[^\s]+', url)
    if not urls:
        bot.reply_to(message, "❌ Please send a valid video link.")
        return
    
    msg = bot.reply_to(message, "⏬ *Downloading...* Please wait.", parse_mode='Markdown')
    
    # Download video
    path, title, duration = download_video(urls[0])
    
    if path and os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        
        if size_mb > 50:
            os.remove(path)
            bot.edit_message_text(f"❌ File too large: {size_mb:.1f}MB (max 50MB)", message.chat.id, msg.message_id)
            return
        
        # Prepare caption
        mins = duration // 60
        secs = duration % 60
        caption = f"✅ *{title}*\n⏱️ {mins}:{secs:02d}\n\n🎬 Enjoy!"
        
        # Send video
        try:
            with open(path, 'rb') as f:
                bot.send_video(message.chat.id, f, caption=caption, parse_mode='Markdown', timeout=180)
            bot.delete_message(message.chat.id, msg.message_id)
            os.remove(path)
        except Exception as e:
            bot.edit_message_text(f"❌ Upload failed: {str(e)[:50]}", message.chat.id, msg.message_id)
    else:
        bot.edit_message_text("❌ *Download failed!*\n\nPossible reasons:\n• Invalid link\n• Private video\n• Video too long\n\nContact @Kingwahidafg", message.chat.id, msg.message_id, parse_mode='Markdown')

# ==================== HEALTH CHECK ====================
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ==================== MAIN ====================
if __name__ == "__main__":
    # Start Flask in background
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start bot
    print("=" * 50)
    print("🤖 VIDEO DOWNLOADER BOT")
    print("✅ Supported: YouTube, TikTok, Facebook, Instagram, Twitter")
    print("💪 Bot is running...")
    print("=" * 50)
    
    bot.infinity_polling(timeout=30)
