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

user_langs = {}

# ==================== YT-DLP OPTIONS ====================
def download_video(url):
    os.makedirs('downloads', exist_ok=True)
    
    ydl_opts = {
        'format': 'best[height<=480]/best',  # Lower quality for smaller file
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Check actual file
            if not os.path.exists(filename):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test = filename.rsplit('.', 1)[0] + ext
                    if os.path.exists(test):
                        filename = test
                        break
            
            # Get file size
            size_mb = os.path.getsize(filename) / (1024 * 1024)
            
            # If file > 45MB, try lower quality
            if size_mb > 45:
                os.remove(filename)
                ydl_opts['format'] = 'best[height<=360]/best'
                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    info2 = ydl2.extract_info(url, download=True)
                    filename = ydl2.prepare_filename(info2)
                    if not os.path.exists(filename):
                        for ext in ['.mp4', '.webm', '.mkv']:
                            test = filename.rsplit('.', 1)[0] + ext
                            if os.path.exists(test):
                                filename = test
                                break
                    size_mb = os.path.getsize(filename) / (1024 * 1024)
            
            duration = info.get('duration', 0)
            title = info.get('title', 'Video')[:50]
            
            return filename, title, duration, size_mb
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None, None

# ==================== LANGUAGE TEXTS ====================
TEXTS = {
    'english': {
        'start': "🎬 *Universal Video Downloader*\n\nSend me any video link from:\nYouTube • TikTok • Facebook • Instagram • Twitter • Reddit\n\n⚡ *Just send the link!*",
        'downloading': "🔄 *Downloading video...*",
        'uploading': "📤 *Uploading video...*",
        'success': "✅ *Video downloaded successfully!*",
        'failed': "❌ *Download failed!*\n\nContact {creator}",
        'large': "❌ *File too large!*\nSize: {size}MB\nTelegram limit: 50MB",
        'no_url': "❌ *No valid link found!*",
        'choose_lang': "🌐 *Choose your language:*"
    },
    'pashto': {
        'start': "🎬 *عمومي ویډیو ډاونلوډر*\n\nما ته د ویډیو لینک رالیږئ:\nیوټیوب • تیک تاک • فیسبوک • انسټاګرام • تویټر\n\n⚡ *یوازې لینک رالیږئ!*",
        'downloading': "🔄 *ویډیو ډاونلوډ کوم...*",
        'uploading': "📤 *ویډیو اپلوډ کوم...*",
        'success': "✅ *ویډیو په بریالیتوب سره ډاونلوډ شوه!*",
        'failed': "❌ *ډاونلوډ ناکام شو!*\n\nاړیکه {creator}",
        'large': "❌ *فایل ډیر لوی دی!*\nاندازه: {size}MB\nد ټیلیګرام حد: 50MB",
        'no_url': "❌ *سم لینک ونه موندل شو!*",
        'choose_lang': "🌐 *خپله ژبه غوره کړئ:*"
    },
    'farsi': {
        'start': "🎬 *دانلودر جهانی ویدیو*\n\nلینک ویدیو را بفرستید:\nیوتیوب • تیک‌تاک • فیسبوک • اینستاگرام • توییتر\n\n⚡ *فقط لینک را بفرستید!*",
        'downloading': "🔄 *در حال دانلود ویدیو...*",
        'uploading': "📤 *در حال آپلود ویدیو...*",
        'success': "✅ *ویدیو با موفقیت دانلود شد!*",
        'failed': "❌ *دانلود ناموفق!*\n\nتماس با {creator}",
        'large': "❌ *فایل خیلی بزرگ است!*\nحجم: {size}MB\nمحدودیت تلگرام: 50MB",
        'no_url': "❌ *لینک معتبر یافت نشد!*",
        'choose_lang': "🌐 *زبان خود را انتخاب کنید:*"
    }
}

def get_text(user_id, key):
    lang = user_langs.get(user_id, 'english')
    return TEXTS[lang].get(key, TEXTS['english'][key])

# ==================== BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_english"),
        InlineKeyboardButton("🇦🇫 پښتو", callback_data="lang_pashto"),
        InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_farsi")
    )
    bot.send_message(user_id, get_text(user_id, 'choose_lang'), reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def lang_cb(call):
    user_id = call.from_user.id
    lang = call.data.split('_')[1]
    user_langs[user_id] = lang
    
    bot.edit_message_text(get_text(user_id, 'start'), user_id, call.message.message_id, parse_mode='Markdown')
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: True)
def handle(m):
    user_id = m.chat.id
    text = m.text.strip()
    
    if user_id not in user_langs:
        start_cmd(m)
        return
    
    urls = re.findall(r'https?://[^\s]+', text)
    if not urls:
        bot.reply_to(m, get_text(user_id, 'no_url'), parse_mode='Markdown')
        return
    
    msg = bot.reply_to(m, get_text(user_id, 'downloading'), parse_mode='Markdown')
    
    path, title, duration, size = download_video(urls[0])
    
    if path and os.path.exists(path):
        if size > 50:
            os.remove(path)
            bot.edit_message_text(get_text(user_id, 'large').format(size=f"{size:.1f}"), user_id, msg.message_id, parse_mode='Markdown')
            return
        
        bot.edit_message_text(get_text(user_id, 'uploading'), user_id, msg.message_id, parse_mode='Markdown')
        
        # Convert to MP4 if needed
        if not path.endswith('.mp4'):
            new_path = path.rsplit('.', 1)[0] + '.mp4'
            try:
                import subprocess
                subprocess.run(['ffmpeg', '-i', path, '-c', 'copy', new_path], capture_output=True)
                if os.path.exists(new_path):
                    os.remove(path)
                    path = new_path
            except:
                pass
        
        mins = duration // 60 if duration else 0
        secs = duration % 60 if duration else 0
        
        try:
            # Try sending as video
            with open(path, 'rb') as f:
                bot.send_video(
                    user_id, 
                    f, 
                    caption=f"✅ {title}\n⏱️ {mins}:{secs:02d}",
                    timeout=300,
                    supports_streaming=True
                )
            bot.delete_message(user_id, msg.message_id)
            os.remove(path)
        except Exception as e:
            error = str(e)
            if "413" in error or "too large" in error.lower():
                bot.edit_message_text(f"❌ File too large! {size:.1f}MB > 50MB", user_id, msg.message_id)
            else:
                # Try sending as document
                try:
                    with open(path, 'rb') as f:
                        bot.send_document(user_id, f, caption=f"🎬 {title}")
                    bot.delete_message(user_id, msg.message_id)
                except:
                    bot.edit_message_text(get_text(user_id, 'failed').format(creator=BOT_CREATOR), user_id, msg.message_id, parse_mode='Markdown')
            os.remove(path)
    else:
        bot.edit_message_text(get_text(user_id, 'failed').format(creator=BOT_CREATOR), user_id, msg.message_id, parse_mode='Markdown')

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    os.makedirs('downloads', exist_ok=True)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()
    print("Bot started...")
    bot.infinity_polling(timeout=30)
