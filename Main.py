# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import yt_dlp
import os
import re
import threading
from flask import Flask

# ==================== CONFIG ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"
BOT_CREATOR = "@Kingwahidafg"

# Bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Flask app for health check
app = Flask(__name__)

# Storage
user_langs = {}

# ==================== YT-DLP OPTIONS (Optimized for all platforms) ====================
def get_ydl_opts():
    return {
        'format': 'best[height<=720]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'extractor_args': {
            'youtube': {
                'skip': ['dash', 'hls'],
            },
            'tiktok': {
                'embed_url': ['https://www.tiktok.com/'],
            }
        }
    }

# ==================== LANGUAGE SETTINGS ====================
LANGUAGES = {
    'english': {
        'start': "🎬 *Universal Video Downloader*\n\nSend me any video link from:\n\n📌 YouTube\n📌 TikTok\n📌 Facebook\n📌 Instagram\n📌 Twitter/X\n📌 Reddit\n📌 And 1000+ more!\n\n⚡ *Just send the link!*",
        'error': "❌ *Invalid link!*\n\nPlease send a valid video link.",
        'downloading': "🔄 *Downloading video...*\n\nPlease wait!",
        'uploading': "📤 *Uploading video...*",
        'success': "✅ *Video downloaded successfully!*",
        'failed': "❌ *Download failed!*\n\nPossible reasons:\n• Invalid link\n• Private video\n• Video too long\n\nContact {creator}",
        'large': "❌ *File too large!*\n\nSize: {size}MB\nTelegram limit: 50MB",
        'no_url': "❌ *No valid link found!*\n\nPlease send a video link from YouTube, TikTok, Facebook, etc.",
        'help': "📚 *Help*\n\n1. Send any video link\n2. Wait for download\n3. Get your video\n\nSupported: YouTube, TikTok, Facebook, Instagram, Twitter, Reddit, Vimeo, Dailymotion, Twitch, and more!\n\n👨‍💻 Creator: {creator}",
        'choose_lang': "🌐 *Choose your language:*",
        'lang_selected': "✅ *Language changed to English!*\n\nSend any video link to download."
    },
    'pashto': {
        'start': "🎬 *عمومي ویډیو ډاونلوډر*\n\nما ته د دې پلیټفارمونو څخه د ویډیو لینک رالیږئ:\n\n📌 یوټیوب\n📌 تیک تاک\n📌 فیسبوک\n📌 انسټاګرام\n📌 تویټر/X\n📌 ریډیټ\n📌 او ۱۰۰۰+ نور!\n\n⚡ *یوازې لینک رالیږئ!*",
        'error': "❌ *غلط لینک!*\n\nمهرباني وکړئ یو سم ویډیو لینک رالیږئ.",
        'downloading': "🔄 *ویډیو ډاونلوډ کوم...*\n\nمهرباني وکړئ انتظار وکړئ!",
        'uploading': "📤 *ویډیو اپلوډ کوم...*",
        'success': "✅ *ویډیو په بریالیتوب سره ډاونلوډ شوه!*",
        'failed': "❌ *ډاونلوډ ناکام شو!*\n\nاحتمالي لاملونه:\n• غلط لینک\n• خصوصي ویډیو\n• ویډیو ډیره اوږده ده\n\nاړیکه {creator}",
        'large': "❌ *فایل ډیر لوی دی!*\n\nاندازه: {size}MB\nد ټیلیګرام حد: 50MB",
        'no_url': "❌ *سم لینک ونه موندل شو!*\n\nمهرباني وکړئ د یوټیوب، تیک تاک، فیسبوک یا بل پلیټفارم څخه ویډیو لینک رالیږئ.",
        'help': "📚 *مرسته*\n\n1. د ویډیو لینک رالیږئ\n2. د ډاونلوډ کیدو انتظار وکړئ\n3. خپله ویډیو ترلاسه کړئ\n\nملاتړ شوي: یوټیوب، تیک تاک، فیسبوک، انسټاګرام، تویټر، ریډیټ، ویمو، ډیلی موشن، تویچ، او نور!\n\n👨‍💻 جوړونکی: {creator}",
        'choose_lang': "🌐 *خپله ژبه غوره کړئ:*",
        'lang_selected': "✅ *ژبه پښتو ته بدله شوه!*\n\nویډیو ډاونلوډ لپاره کوم لینک رالیږئ."
    },
    'farsi': {
        'start': "🎬 *دانلودر جهانی ویدیو*\n\nلینک ویدیو را از این پلتفرم‌ها بفرستید:\n\n📌 یوتیوب\n📌 تیک‌تاک\n📌 فیسبوک\n📌 اینستاگرام\n📌 توییتر/X\n📌 ردیت\n📌 و بیش از ۱۰۰۰ پلتفرم دیگر!\n\n⚡ *فقط لینک را بفرستید!*",
        'error': "❌ *لینک نامعتبر!*\n\nلطفاً یک لینک معتبر ویدیو بفرستید.",
        'downloading': "🔄 *در حال دانلود ویدیو...*\n\nلطفاً صبر کنید!",
        'uploading': "📤 *در حال آپلود ویدیو...*",
        'success': "✅ *ویدیو با موفقیت دانلود شد!*",
        'failed': "❌ *دانلود ناموفق!*\n\nدلایل احتمالی:\n• لینک نامعتبر\n• ویدیو خصوصی است\n• ویدیو خیلی طولانی است\n\nتماس با {creator}",
        'large': "❌ *فایل خیلی بزرگ است!*\n\nحجم: {size}MB\nمحدودیت تلگرام: 50MB",
        'no_url': "❌ *لینک معتبر یافت نشد!*\n\nلطفاً لینک ویدیو را از یوتیوب، تیک‌تاک، فیسبوک یا پلتفرم دیگر بفرستید.",
        'help': "📚 *راهنما*\n\n1. لینک ویدیو را بفرستید\n2. منتظر دانلود بمانید\n3. ویدیوی خود را دریافت کنید\n\nپشتیبانی: یوتیوب، تیک‌تاک، فیسبوک، اینستاگرام، توییتر، ردیت، ویمو، دیلی موشن، توییچ و بیشتر!\n\n👨‍💻 سازنده: {creator}",
        'choose_lang': "🌐 *زبان خود را انتخاب کنید:*",
        'lang_selected': "✅ *زبان به فارسی تغییر کرد!*\n\nبرای دانلود ویدیو، لینک را بفرستید."
    }
}

def get_text(user_id, key):
    lang = user_langs.get(user_id, 'english')
    return LANGUAGES[lang].get(key, LANGUAGES['english'][key])

# ==================== DOWNLOAD FUNCTION ====================
def download_video(url):
    os.makedirs('downloads', exist_ok=True)
    
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Fix extension if needed
            if not os.path.exists(filename):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test = filename.rsplit('.', 1)[0] + ext
                    if os.path.exists(test):
                        filename = test
                        break
            
            # Get video info
            duration = info.get('duration', 0)
            minutes = duration // 60
            seconds = duration % 60
            title = info.get('title', 'Video')[:60]
            platform = info.get('extractor', 'Unknown')
            
            return filename, title, minutes, seconds, platform
    except Exception as e:
        print(f"Download error: {e}")
        return None, None, None, None, None

# ==================== BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    # Language selection keyboard
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_english"),
        InlineKeyboardButton("🇦🇫 پښتو", callback_data="lang_pashto"),
        InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_farsi")
    )
    
    bot.send_message(user_id, get_text(user_id, 'choose_lang'), parse_mode='Markdown', reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def language_callback(call):
    user_id = call.from_user.id
    lang = call.data.split('_')[1]
    user_langs[user_id] = lang
    
    bot.edit_message_text(
        LANGUAGES[lang]['lang_selected'], 
        user_id, 
        call.message.message_id, 
        parse_mode='Markdown'
    )
    
    # Send main menu
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📥 Download Video", callback_data="download"),
        InlineKeyboardButton("📚 Help", callback_data="help"),
        InlineKeyboardButton("🌐 Change Language", callback_data="language")
    )
    
    bot.send_message(
        user_id, 
        get_text(user_id, 'start'), 
        parse_mode='Markdown', 
        reply_markup=keyboard
    )
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "download")
def download_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, "📎 *Send me the video link:*", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_callback(call):
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)
    bot.send_message(user_id, get_text(user_id, 'help').format(creator=BOT_CREATOR), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "language")
def language_callback_menu(call):
    user_id = call.from_user.id
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_english"),
        InlineKeyboardButton("🇦🇫 پښتو", callback_data="lang_pashto"),
        InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_farsi")
    )
    bot.edit_message_text(get_text(user_id, 'choose_lang'), user_id, call.message.message_id, parse_mode='Markdown', reply_markup=keyboard)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check if user has selected language
    if user_id not in user_langs:
        start_command(message)
        return
    
    # Extract URL
    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(text)
    
    if not urls:
        bot.reply_to(message, get_text(user_id, 'no_url'), parse_mode='Markdown')
        return
    
    url = urls[0]
    msg = bot.reply_to(message, get_text(user_id, 'downloading'), parse_mode='Markdown')
    
    # Download video
    video_path, title, minutes, seconds, platform = download_video(url)
    
    if video_path and os.path.exists(video_path):
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        
        if file_size > 50:
            os.remove(video_path)
            bot.edit_message_text(get_text(user_id, 'large').format(size=f"{file_size:.1f}"), user_id, msg.message_id, parse_mode='Markdown')
            return
        
        bot.edit_message_text(get_text(user_id, 'uploading'), user_id, msg.message_id, parse_mode='Markdown')
        
        # Create caption
        duration_str = f"{minutes}:{seconds:02d}" if minutes or seconds else "Unknown"
        caption = f"🎬 *{title}*\n\n⏱️ Duration: {duration_str}\n📱 Platform: {platform.upper()}\n\n{get_text(user_id, 'success')}\n\n🤖 @WAHIDX_DOWNLOADER"
        
        try:
            with open(video_path, 'rb') as f:
                bot.send_video(user_id, f, caption=caption, parse_mode='Markdown', timeout=180)
            bot.delete_message(user_id, msg.message_id)
            os.remove(video_path)
        except Exception as e:
            bot.edit_message_text(f"❌ Upload error: {str(e)[:80]}", user_id, msg.message_id)
    else:
        bot.edit_message_text(get_text(user_id, 'failed').format(creator=BOT_CREATOR), user_id, msg.message_id, parse_mode='Markdown')

# ==================== FLASK HEALTH CHECK ====================
@app.route('/')
def home():
    return "WAHIDX DOWNLOADER is running! Ready to download videos from YouTube, TikTok, Facebook, and more!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ==================== MAIN ====================
if __name__ == "__main__":
    os.makedirs('downloads', exist_ok=True)
    
    # Start Flask in background
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start bot
    print("=" * 50)
    print("🤖 WAHIDX UNIVERSAL DOWNLOADER V4.0")
    print(f"👤 Creator: {BOT_CREATOR}")
    print("📥 Supported: YouTube, TikTok, Facebook, Instagram, Twitter, Reddit, and 1000+ more!")
    print("💪 Bot is running...")
    print("=" * 50)
    
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
