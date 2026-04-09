# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import re
import threading
from flask import Flask

# ==================== CONFIG ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"
BOT_CREATOR = "@Kingwahidafg"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# User language storage
user_lang = {}

# Check for cookies file
cookies_file = "cookies.txt"
has_cookies = os.path.exists(cookies_file)

# Create downloads folder
os.makedirs('downloads', exist_ok=True)

# ==================== LANGUAGE TEXTS ====================
TEXTS = {
    'english': {
        'start': "🎬 *Universal Video Downloader*\n\nSend me any video link from:\n📌 YouTube\n📌 TikTok\n📌 Facebook\n📌 Instagram\n📌 Twitter/X\n📌 Reddit\n\n⚡ Just send the link!",
        'downloading': "⏬ *Downloading video...*\nPlease wait...",
        'uploading': "📤 *Uploading video...*",
        'success': "✅ *Video downloaded successfully!*",
        'failed': "❌ *Download failed!*\n\nContact {creator}",
        'large': "❌ *File too large!* (max 50MB)",
        'no_url': "❌ *No valid link found!*",
        'choose': "🌐 *Choose your language:*",
        'lang_set': "✅ Language set! Send me a video link."
    },
    'pashto': {
        'start': "🎬 *عمومي ویډیو ډاونلوډر*\n\nما ته د ویډیو لینک رالیږئ:\n📌 یوټیوب\n📌 تیک تاک\n📌 فیسبوک\n📌 انسټاګرام\n📌 تویټر/X\n📌 ریډیټ\n\n⚡ یوازې لینک رالیږئ!",
        'downloading': "⏬ *ویډیو ډاونلوډ کوم...*\nمهرباني وکړئ انتظار وکړئ...",
        'uploading': "📤 *ویډیو اپلوډ کوم...*",
        'success': "✅ *ویډیو په بریالیتوب سره ډاونلوډ شوه!*",
        'failed': "❌ *ډاونلوډ ناکام شو!*\n\nاړیکه {creator}",
        'large': "❌ *فایل ډیر لوی دی!* (حد 50MB)",
        'no_url': "❌ *سم لینک ونه موندل شو!*",
        'choose': "🌐 *خپله ژبه غوره کړئ:*",
        'lang_set': "✅ ژبه وټاکل شوه! ما ته د ویډیو لینک رالیږئ."
    },
    'farsi': {
        'start': "🎬 *دانلودر جهانی ویدیو*\n\nلینک ویدیو را بفرستید:\n📌 یوتیوب\n📌 تیک‌تاک\n📌 فیسبوک\n📌 اینستاگرام\n📌 توییتر/X\n📌 ردیت\n\n⚡ فقط لینک را بفرستید!",
        'downloading': "⏬ *در حال دانلود ویدیو...*\nلطفاً صبر کنید...",
        'uploading': "📤 *در حال آپلود ویدیو...*",
        'success': "✅ *ویدیو با موفقیت دانلود شد!*",
        'failed': "❌ *دانلود ناموفق!*\n\nتماس با {creator}",
        'large': "❌ *فایل خیلی بزرگ است!* (حداکثر 50MB)",
        'no_url': "❌ *لینک معتبر یافت نشد!*",
        'choose': "🌐 *زبان خود را انتخاب کنید:*",
        'lang_set': "✅ زبان انتخاب شد! لینک ویدیو را بفرستید."
    }
}

def get_text(user_id, key):
    lang = user_lang.get(user_id, 'english')
    return TEXTS[lang].get(key, TEXTS['english'][key])

# ==================== DOWNLOAD FUNCTION ====================
def download_video(url):
    opts = {
        'format': 'best[height<=480]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    # Add cookies if available
    if has_cookies:
        opts['cookiefile'] = cookies_file
    
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
            
            duration = info.get('duration', 0)
            title = info.get('title', 'Video')[:50]
            return filename, title, duration
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

# ==================== BOT COMMANDS ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_english"),
        InlineKeyboardButton("🇦🇫 پښتو", callback_data="lang_pashto"),
        InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_farsi")
    )
    
    bot.send_message(user_id, get_text(user_id, 'choose'), reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def lang_callback(call):
    user_id = call.from_user.id
    lang = call.data.split('_')[1]
    user_lang[user_id] = lang
    
    bot.edit_message_text(
        get_text(user_id, 'lang_set'), 
        user_id, 
        call.message.message_id,
        parse_mode='Markdown'
    )
    
    bot.send_message(user_id, get_text(user_id, 'start'), parse_mode='Markdown')
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check if user has selected language
    if user_id not in user_lang:
        start_cmd(message)
        return
    
    # Extract URL
    urls = re.findall(r'https?://[^\s]+', text)
    if not urls:
        bot.reply_to(message, get_text(user_id, 'no_url'), parse_mode='Markdown')
        return
    
    msg = bot.reply_to(message, get_text(user_id, 'downloading'), parse_mode='Markdown')
    
    # Download video
    path, title, duration = download_video(urls[0])
    
    if path and os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        
        if size_mb > 50:
            os.remove(path)
            bot.edit_message_text(get_text(user_id, 'large'), user_id, msg.message_id, parse_mode='Markdown')
            return
        
        bot.edit_message_text(get_text(user_id, 'uploading'), user_id, msg.message_id, parse_mode='Markdown')
        
        mins = duration // 60
        secs = duration % 60
        caption = f"✅ *{title}*\n⏱️ {mins}:{secs:02d}\n\n{get_text(user_id, 'success')}"
        
        try:
            with open(path, 'rb') as f:
                bot.send_video(user_id, f, caption=caption, parse_mode='Markdown', timeout=180)
            bot.delete_message(user_id, msg.message_id)
            os.remove(path)
        except Exception as e:
            bot.edit_message_text(get_text(user_id, 'failed').format(creator=BOT_CREATOR), user_id, msg.message_id, parse_mode='Markdown')
    else:
        bot.edit_message_text(get_text(user_id, 'failed').format(creator=BOT_CREATOR), user_id, msg.message_id, parse_mode='Markdown')

# ==================== HEALTH CHECK ====================
@app.route('/')
def home():
    return "WAHIDX DOWNLOADER is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ==================== MAIN ====================
if __name__ == "__main__":
    # Start Flask in background
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Print status
    print("=" * 50)
    print("🤖 WAHIDX VIDEO DOWNLOADER")
    print(f"👤 Creator: {BOT_CREATOR}")
    print(f"🍪 Cookies: {'✅ Found' if has_cookies else '❌ Not found'}")
    print("📥 Supported: YouTube, TikTok, Facebook, Instagram, Twitter")
    print("💪 Bot is running...")
    print("=" * 50)
    
    # Start bot
    bot.infinity_polling(timeout=30)
