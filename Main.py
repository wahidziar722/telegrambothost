# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import yt_dlp
import os
import re
import requests
from datetime import datetime
import threading
from flask import Flask

# ==================== CONFIG ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"
BOT_CREATOR = "@Kingwahidafg"

# Bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Flask app for health check (keeps Render alive)
app = Flask(__name__)

# Storage
user_languages = {}
user_contacts = {}
user_phones = {}
online_users = set()

# ==================== WELCOME MESSAGES ====================
WELCOME_TEXTS = {
    'english': {
        'welcome': "🔥 *WAHIDX DOWNLOADER* 🔥\n\n✨ *Welcome* {name}! ✨\n└ 👤 Username: @{username}\n└ 📞 Phone: {phone}\n└ 🤖 Bot Creator: {creator}\n\n💫 *I can download videos from:*\n📌 YouTube | Instagram | TikTok\n📌 Twitter/X | Facebook | Reddit\n📌 And 1000+ more!\n\n⚡ *Just send me any video link!*",
        'instruction': "\n\n📥 *How to use:* Send any video link\n🎯 *Max size:* 50MB\n👥 *Users:* {total}",
        'error': "❌ *Invalid URL!*\n\nPlease send a valid video link.",
        'downloading': "🔄 *Downloading...* Please wait!",
        'uploading': "📤 *Uploading video...*",
        'success': "✅ *Video Downloaded Successfully!*",
        'failed': "❌ *Download failed!*\n\nContact {creator}",
        'large': "❌ *File too large!*\n\nSize: {size}MB\nTelegram limit: 50MB"
    },
    'pashto': {
        'welcome': "🔥 *واهدکس ډاونلوډر* 🔥\n\n✨ *ښه راغلاست* {name}! ✨\n└ 👤 یوزرنیم: @{username}\n└ 📞 شمیره: {phone}\n└ 🤖 بوټ جوړونکی: {creator}\n\n💫 *زه کولای شم د دې پلیټفارمونو څخه ویډیوګانې ډاونلوډ کړم:*\n📌 یوټیوب | انسټاګرام | ټیکټاک\n📌 تویټر/X | فیسبوک | ریډیټ\n📌 او ۱۰۰۰+ نور!\n\n⚡ *یوازې ما ته د ویډیو لینک راولیږئ!*",
        'instruction': "\n\n📥 *د کارولو طریقه:* ویډیو لینک رالیږئ\n🎯 *اعظمي اندازه:* 50MB\n👥 *کارونکي:* {total}",
        'error': "❌ *غلط لینک!*\n\nمهرباني وکړئ یو سم ویډیو لینک راولیږئ.",
        'downloading': "🔄 *ډاونلوډ کوم...* مهرباني وکړئ انتظار وکړئ!",
        'uploading': "📤 *ویډیو اپلوډ کوم...*",
        'success': "✅ *ویډیو په بریالیتوب سره ډاونلوډ شوه!*",
        'failed': "❌ *ډاونلوډ ناکام شو!*\n\nاړیکه {creator}",
        'large': "❌ *فایل ډیر لوی دی!*\n\nاندازه: {size}MB\nد ټیلیګرام حد: 50MB"
    },
    'farsi': {
        'welcome': "🔥 *واهدکس دانلودر* 🔥\n\n✨ *خوش آمدید* {name}! ✨\n└ 👤 نام کاربری: @{username}\n└ 📞 شماره: {phone}\n└ 🤖 سازنده بات: {creator}\n\n💫 *من می‌توانم ویدیوها را از این پلتفرم‌ها دانلود کنم:*\n📌 یوتیوب | اینستاگرام | تیک‌تاک\n📌 توییتر/X | فیسبوک | ردیت\n📌 و بیش از ۱۰۰۰ پلتفرم دیگر!\n\n⚡ *فقط لینک ویدیو را برای من بفرستید!*",
        'instruction': "\n\n📥 *نحوه استفاده:* لینک ویدیو را بفرستید\n🎯 *حداکثر حجم:* 50MB\n👥 *کاربران:* {total}",
        'error': "❌ *لینک نامعتبر!*\n\nلطفاً یک لینک معتبر ویدیو بفرستید.",
        'downloading': "🔄 *در حال دانلود...* لطفاً صبر کنید!",
        'uploading': "📤 *در حال آپلود ویدیو...*",
        'success': "✅ *ویدیو با موفقیت دانلود شد!*",
        'failed': "❌ *دانلود ناموفق!*\n\nتماس با {creator}",
        'large': "❌ *فایل خیلی بزرگ است!*\n\nحجم: {size}MB\nمحدودیت تلگرام: 50MB"
    }
}

# ==================== YT-DLP OPTIONS ====================
YDL_OPTIONS = {
    'format': 'best[height<=720]/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'ignoreerrors': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# ==================== FUNCTIONS ====================
def get_user_lang(user_id):
    return user_languages.get(user_id, 'english')

def get_text(user_id, key):
    lang = get_user_lang(user_id)
    return WELCOME_TEXTS[lang].get(key, WELCOME_TEXTS['english'][key])

def download_video(url):
    os.makedirs('downloads', exist_ok=True)
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if not os.path.exists(filename):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test = filename.rsplit('.', 1)[0] + ext
                    if os.path.exists(test):
                        filename = test
                        break
            
            duration = info.get('duration', 0)
            title = info.get('title', 'Video')
            return filename, title, duration
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

# ==================== BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "User"
    username = message.from_user.username or "unknown"
    
    # Phone number request keyboard
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("📞 Share My Phone Number", request_contact=True))
    
    welcome = f"🌟 *WAHIDX DOWNLOADER V4.0* 🌟\n\n👤 *Welcome {name}!*\n\n📢 *Please share your phone number* to continue.\n\n👇 *Click the button below:*"
    bot.send_message(user_id, welcome, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    user_id = message.from_user.id
    contact = message.contact
    
    if contact:
        user_phones[user_id] = contact.phone_number
        online_users.add(user_id)
        
        # Language selection keyboard
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_english"),
            InlineKeyboardButton("🇦🇫 پښتو", callback_data="lang_pashto"),
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_farsi")
        )
        
        text = f"✅ *Phone number received!*\n\n📞 `{contact.phone_number}`\n\n🌐 *Choose your language:*"
        bot.send_message(user_id, text, parse_mode='Markdown', reply_markup=keyboard)
        
        # Remove phone keyboard
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("/start"))
        bot.send_message(user_id, "✨ *Main menu ready!* ✨\n\nSend any video link to download!", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def language_callback(call):
    user_id = call.from_user.id
    lang = call.data.split('_')[1]
    user_languages[user_id] = lang
    
    name = call.from_user.first_name or "User"
    username = call.from_user.username or "unknown"
    phone = user_phones.get(user_id, "Not shared")
    total = len(user_phones)
    
    text = get_text(user_id, 'welcome').format(
        name=name,
        username=username,
        phone=phone,
        creator=BOT_CREATOR
    )
    text += get_text(user_id, 'instruction').format(total=total)
    
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode='Markdown')
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check if user has selected language
    if user_id not in user_languages:
        bot.reply_to(message, "❌ Please send /start first and share your phone number!")
        return
    
    # Extract URL
    urls = re.findall(r'https?://[^\s]+', text)
    if not urls:
        bot.reply_to(message, get_text(user_id, 'error'), parse_mode='Markdown')
        return
    
    url = urls[0]
    msg = bot.reply_to(message, get_text(user_id, 'downloading'), parse_mode='Markdown')
    
    video_path, title, duration = download_video(url)
    
    if video_path and os.path.exists(video_path):
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        
        if file_size > 50:
            os.remove(video_path)
            bot.edit_message_text(get_text(user_id, 'large').format(size=f"{file_size:.1f}"), user_id, msg.message_id, parse_mode='Markdown')
            return
        
        bot.edit_message_text(get_text(user_id, 'uploading'), user_id, msg.message_id, parse_mode='Markdown')
        
        minutes = duration // 60
        seconds = duration % 60
        caption = f"🎬 *{title[:50]}*\n⏱️ {minutes}:{seconds:02d}\n\n{get_text(user_id, 'success')}"
        
        try:
            with open(video_path, 'rb') as f:
                bot.send_video(user_id, f, caption=caption, parse_mode='Markdown', timeout=120)
            bot.delete_message(user_id, msg.message_id)
            os.remove(video_path)
        except Exception as e:
            bot.edit_message_text(f"❌ Upload error: {str(e)[:80]}", user_id, msg.message_id)
    else:
        bot.edit_message_text(get_text(user_id, 'failed').format(creator=BOT_CREATOR), user_id, msg.message_id, parse_mode='Markdown')

# ==================== FLASK HEALTH CHECK ====================
@app.route('/')
def home():
    return f"WAHIDX DOWNLOADER is running! Total users: {len(user_phones)}"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ==================== MAIN ====================
if __name__ == "__main__":
    os.makedirs('downloads', exist_ok=True)
    
    # Start Flask in background
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start bot
    print("=" * 50)
    print("🤖 WAHIDX DOWNLOADER V4.0")
    print(f"👤 Creator: {BOT_CREATOR}")
    print("💪 Bot is running...")
    print("=" * 50)
    
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
