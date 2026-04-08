# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import re
import threading
from flask import Flask, request

# ==================== CONFIG ====================
BOT_TOKEN = "8607359712:AAGVPHwLolvKL7MZUp16nHcY00yf3bP0R60"
ADMIN_ID = "8518408753"

# Required channels
REQUIRED_CHANNELS = [
    {"username": "@WahidModeX", "url": "https://t.me/WahidModeX"},
    {"username": "@ProTech43", "url": "https://t.me/ProTech43"}
]

# Flask app for webhook
app = Flask(__name__)

# Bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Store user verification status
user_verified = {}

# ==================== BUTTONS ====================
def get_check_button():
    keyboard = InlineKeyboardMarkup()
    check_btn = InlineKeyboardButton("✅ Check Membership", callback_data="check_membership")
    keyboard.add(check_btn)
    return keyboard

def get_channels_text():
    channels = "\n".join([f"📢 {ch['username']}" for ch in REQUIRED_CHANNELS])
    return channels

# ==================== CHECK MEMBERSHIP ====================
def is_user_member(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            chat_member = bot.get_chat_member(channel["username"], user_id)
            if chat_member.status in ['left', 'kicked']:
                return False
        return True
    except:
        return False

# ==================== DOWNLOAD VIDEO ====================
def download_video(url, user_id):
    download_path = f"downloads/{user_id}"
    os.makedirs(download_path, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
        'format': 'best[height<=720]',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Get actual file extension
            if not os.path.exists(filename):
                filename = filename.replace('.webm', '.mp4').replace('.mkv', '.mp4')
            return filename
    except Exception as e:
        print(f"Error: {e}")
        return None

# ==================== TELEGRAM BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    welcome_text = f"""🚀 **Welcome to Video Downloader Bot!**

📌 **Features:**
• Download videos from YouTube, Instagram, TikTok, Facebook, Twitter, Telegram
• Fast and High Quality
• Free to use

📢 **Join our channels to use this bot:**
{get_channels_text()}

✅ After joining, click the button below to verify."""

    bot.send_message(
        user_id, 
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=get_check_button()
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def check_membership(call):
    user_id = call.from_user.id
    
    if is_user_member(user_id):
        user_verified[user_id] = True
        bot.edit_message_text(
            "✅ **Verification Successful!**\n\nYou are now verified. Send me any video link to download.",
            user_id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.send_message(
            user_id,
            "📎 **Send me a video link:**\n\nSupported platforms:\nYouTube • Instagram • TikTok • Facebook • Twitter • Telegram"
        )
    else:
        not_joined = []
        for channel in REQUIRED_CHANNELS:
            try:
                chat_member = bot.get_chat_member(channel["username"], user_id)
                if chat_member.status in ['left', 'kicked']:
                    not_joined.append(f"❌ {channel['username']}")
            except:
                not_joined.append(f"❌ {channel['username']}")
        
        channels_text = "\n".join(not_joined)
        bot.answer_callback_query(
            call.id,
            "Please join all channels first!",
            show_alert=True
        )
        bot.edit_message_text(
            f"❌ **You haven't joined these channels:**\n\n{channels_text}\n\nPlease join them and click verify again.",
            user_id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=get_check_button()
        )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text
    
    # Check if user is verified
    if not user_verified.get(user_id, False):
        if not is_user_member(user_id):
            bot.send_message(
                user_id,
                "❌ **Access Denied!**\n\nPlease join our channels first:\n" + get_channels_text(),
                reply_markup=get_check_button()
            )
            return
        else:
            user_verified[user_id] = True
    
    # Check if message contains a URL
    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(text)
    
    if not urls:
        bot.send_message(
            user_id,
            "📎 **Please send a valid video link!**\n\nExamples:\n• https://youtube.com/watch?v=...\n• https://instagram.com/p/...\n• https://tiktok.com/@.../video/..."
        )
        return
    
    url = urls[0]
    
    # Send processing message
    msg = bot.send_message(user_id, "⏬ **Downloading video...**\n\nPlease wait, this may take a few seconds.")
    
    # Download video
    video_path = download_video(url, user_id)
    
    if video_path and os.path.exists(video_path):
        bot.edit_message_text("📤 **Uploading video...**", user_id, msg.message_id)
        
        try:
            # Send video
            with open(video_path, 'rb') as video:
                bot.send_video(user_id, video, caption="✅ **Video downloaded successfully!**\n\nEnjoy! 🎬")
            
            bot.delete_message(user_id, msg.message_id)
            
            # Clean up
            os.remove(video_path)
            os.rmdir(f"downloads/{user_id}")
            
        except Exception as e:
            bot.edit_message_text(f"❌ **Error uploading video!**\n\nTry a shorter video or different link.", user_id, msg.message_id)
    else:
        bot.edit_message_text(
            "❌ **Download failed!**\n\nPossible reasons:\n• Link is invalid\n• Video is private\n• Unsupported platform\n\nTry another link.",
            user_id,
            msg.message_id
        )

@bot.message_handler(commands=['creators'])
def creators_command(message):
    creators_text = """👨‍💻 **Bot Creators:**\n@Kingwahid\n@XFPro43\n\n📢 **Our Channels:**\n@WahidModeX\n@ProTech43"""
    bot.send_message(message.chat.id, creators_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = message.from_user.id
    is_member = is_user_member(user_id)
    is_verified = user_verified.get(user_id, False)
    
    status_text = f"""📊 **Bot Status**

✅ Verified: {is_verified}
📢 Channel Member: {is_member}

Send /start to re-verify."""
    bot.send_message(user_id, status_text, parse_mode='Markdown')

# ==================== FLASK WEBHOOK ====================
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/')
def home():
    return "Video Downloader Bot is running!"

def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://telegrambothost-op7o.onrender.com/webhook/{BOT_TOKEN}"
    response = requests.get(url)
    print(response.text)

if __name__ == "__main__":
    # Create downloads folder
    os.makedirs("downloads", exist_ok=True)
    
    # Remove webhook and use polling (better for Render)
    bot.remove_webhook()
    
    # Start bot in a separate thread
    def run_bot():
        print("Bot started polling...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask server
    print("Flask server running on port 8080...")
    app.run(host='0.0.0.0', port=8080)
