# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import re
import threading
from flask import Flask, request
import json
from datetime import datetime

# ==================== CONFIG ====================
BOT_TOKEN = "8434128207:AAH-BnEeeW1pR2X2n1OjrUs2NtWJGPh8Qs8"
ADMIN_ID = "8518408753"

# Required channels (both)
REQUIRED_CHANNELS = [
    {"username": "@SQFORCEZONE", "url": "https://t.me/SQFORCEZONE", "name": "SQ FORCE ZONE"},
    {"username": "@WahidModeX", "url": "https://t.me/WahidModeX", "name": "Wahid Mode X"}
]

# Bot creators
CREATORS = ["@Kingwahid", "@XFPro43"]

# Flask app
app = Flask(__name__)

# Bot instance
bot = telebot.TeleBot(BOT_TOKEN)

# Store data
user_verified = {}
total_users = set()

# ==================== SAVE/LOAD USER STATS ====================
def save_user_stats():
    try:
        with open("users.json", "w") as f:
            json.dump(list(total_users), f)
    except:
        pass

def load_user_stats():
    global total_users
    try:
        with open("users.json", "r") as f:
            data = json.load(f)
            total_users = set(data)
    except:
        total_users = set()

def update_user(user_id):
    total_users.add(str(user_id))
    save_user_stats()

# ==================== BUTTONS WITH JOIN LINKS ====================
def get_join_buttons():
    """Buttons to join both channels and verify"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Join button for first channel
    join1 = InlineKeyboardButton(
        f"📢 Join {REQUIRED_CHANNELS[0]['name']}", 
        url=REQUIRED_CHANNELS[0]['url']
    )
    # Join button for second channel
    join2 = InlineKeyboardButton(
        f"📢 Join {REQUIRED_CHANNELS[1]['name']}", 
        url=REQUIRED_CHANNELS[1]['url']
    )
    keyboard.add(join1, join2)
    
    # Verify button
    verify_btn = InlineKeyboardButton("✅ I Have Joined - Verify", callback_data="check_membership")
    keyboard.add(verify_btn)
    
    return keyboard

def get_fail_buttons():
    """Buttons when verification fails (shows only unjoined channels)"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Add join buttons for all channels (they will see which ones they missed)
    for ch in REQUIRED_CHANNELS:
        join_btn = InlineKeyboardButton(
            f"📢 Join {ch['name']}", 
            url=ch['url']
        )
        keyboard.add(join_btn)
    
    # Retry button
    retry_btn = InlineKeyboardButton("🔄 Try Again", callback_data="check_membership")
    keyboard.add(retry_btn)
    
    return keyboard

def get_main_menu():
    """Main menu after verification"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("📥 Download Video", callback_data="download")
    btn2 = InlineKeyboardButton("👨‍💻 Creators", callback_data="creators")
    btn3 = InlineKeyboardButton("📊 Stats", callback_data="stats")
    btn4 = InlineKeyboardButton("🎨 Sticker", callback_data="sticker")
    keyboard.add(btn1, btn2, btn3, btn4)
    return keyboard

def get_channels_text():
    return "\n".join([f"📢 {ch['name']}\n   {ch['url']}" for ch in REQUIRED_CHANNELS])

# ==================== CHECK MEMBERSHIP ====================
def is_user_member(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            chat_member = bot.get_chat_member(channel["username"], user_id)
            if chat_member.status in ['left', 'kicked']:
                return False
        return True
    except Exception as e:
        print(f"Check error: {e}")
        return False

def get_not_joined_channels(user_id):
    """Return list of channels user hasn't joined"""
    not_joined = []
    for channel in REQUIRED_CHANNELS:
        try:
            chat_member = bot.get_chat_member(channel["username"], user_id)
            if chat_member.status in ['left', 'kicked']:
                not_joined.append(channel)
        except:
            not_joined.append(channel)
    return not_joined

# ==================== GET VIDEO INFO ====================
def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            duration = info.get('duration', 0)
            minutes = duration // 60
            seconds = duration % 60
            duration_str = f"{minutes}:{seconds:02d}"
            
            likes = info.get('like_count', 0)
            comments = info.get('comment_count', 0)
            views = info.get('view_count', 0)
            
            video_data = {
                'title': info.get('title', 'Unknown'),
                'channel': info.get('uploader', 'Unknown'),
                'duration': duration_str,
                'views': f"{views:,}" if views else "0",
                'likes': f"{likes:,}" if likes else "0",
                'comments': f"{comments:,}" if comments else "0",
                'thumbnail': info.get('thumbnail', ''),
                'url': url,
            }
            return video_data
    except Exception as e:
        print(f"Info error: {e}")
        return None

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
            
            # Fix extension if needed
            if not os.path.exists(filename):
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_file = filename.rsplit('.', 1)[0] + ext
                    if os.path.exists(test_file):
                        filename = test_file
                        break
            
            return filename, info
    except Exception as e:
        print(f"Download error: {e}")
        return None, None

# ==================== TELEGRAM HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.from_user.id)
    update_user(user_id)
    
    total = len(total_users)
    
    welcome_text = f"""🚀 **Welcome to Video Downloader Bot!**

📌 **Features:**
• Download videos from YouTube, Instagram, TikTok, Facebook, Twitter
• Shows likes, comments, views
• Fast and High Quality

👥 **Total Users:** {total}+

📢 **Please join both channels to use this bot:**
{get_channels_text()}

✅ After joining, click the button below to verify."""

    bot.send_message(
        user_id, 
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=get_join_buttons()
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def check_membership(call):
    user_id = str(call.from_user.id)
    
    if is_user_member(user_id):
        user_verified[user_id] = True
        bot.edit_message_text(
            "✅ **Verification Successful!**\n\nYou can now use the bot.",
            user_id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.send_message(
            user_id,
            "📎 **Send me a video link to download!**\n\nSupported:\nYouTube • Instagram • TikTok • Facebook • Twitter",
            reply_markup=get_main_menu()
        )
    else:
        not_joined = get_not_joined_channels(user_id)
        channels_text = "\n".join([f"❌ {ch['name']}" for ch in not_joined])
        
        bot.answer_callback_query(call.id, "Join all channels first!", show_alert=True)
        bot.edit_message_text(
            f"❌ **You haven't joined these channels:**\n\n{channels_text}\n\nPlease join them and click verify again.",
            user_id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=get_fail_buttons()
        )

@bot.callback_query_handler(func=lambda call: call.data == "download")
def download_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, "📎 **Send me the video link:**")

@bot.callback_query_handler(func=lambda call: call.data == "creators")
def creators_callback(call):
    creators_text = f"""👨‍💻 **Bot Creators:**

{chr(10).join(CREATORS)}

📢 **Our Channels:**
@SQFORCEZONE
@WahidModeX

💡 **For support:** Contact creators"""
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, creators_text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats_callback(call):
    total = len(total_users)
    verified = len(user_verified)
    
    stats_text = f"""📊 **Bot Statistics**

👥 **Total Users:** {total}
✅ **Verified Users:** {verified}
🟢 **Bot Status:** Active
📅 **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

🚀 **Keep using!**"""
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, stats_text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "sticker")
def sticker_callback(call):
    sticker_text = f"""🎨 **Sticker Pack**

Coming soon! Stickers will be available at:
@WahidModeX

Stay tuned! 🔥"""
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, sticker_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    text = message.text
    
    # Check verification
    if not user_verified.get(user_id, False):
        if not is_user_member(user_id):
            not_joined = get_not_joined_channels(user_id)
            channels_text = "\n".join([f"❌ {ch['name']}" for ch in not_joined])
            bot.send_message(
                user_id,
                f"❌ **Access Denied!**\n\nPlease join these channels first:\n{channels_text}",
                reply_markup=get_fail_buttons()
            )
            return
        else:
            user_verified[user_id] = True
    
    # Check for URL
    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(text)
    
    if not urls:
        bot.send_message(
            user_id,
            "📎 **Send a valid video link!**\n\nExamples:\n• https://youtube.com/watch?v=...\n• https://instagram.com/p/...\n• https://tiktok.com/@.../video/...\n• https://twitter.com/.../status/...",
            reply_markup=get_main_menu()
        )
        return
    
    url = urls[0]
    
    # Get video info
    info_msg = bot.send_message(user_id, "📊 **Getting video information...**")
    
    video_info = get_video_info(url)
    
    if video_info:
        info_text = f"""🎬 **Video Information**

📌 **Title:** {video_info['title']}
👤 **Channel:** {video_info['channel']}
⏱️ **Duration:** {video_info['duration']}
👁️ **Views:** {video_info['views']}
❤️ **Likes:** {video_info['likes']}
💬 **Comments:** {video_info['comments']}

🔄 **Downloading video...**"""
        
        bot.edit_message_text(info_text, user_id, info_msg.message_id, parse_mode='Markdown')
        
        # Download video
        video_path, _ = download_video(url, user_id)
        
        if video_path and os.path.exists(video_path):
            bot.edit_message_text("📤 **Uploading video...**", user_id, info_msg.message_id)
            
            try:
                caption = f"""✅ **Download Complete!**

📌 **Title:** {video_info['title']}
👤 **Channel:** {video_info['channel']}
⏱️ **Duration:** {video_info['duration']}
❤️ **Likes:** {video_info['likes']} | 💬 **Comments:** {video_info['comments']}

🎬 **Enjoy!**"""
                
                with open(video_path, 'rb') as video:
                    bot.send_video(
                        user_id, 
                        video, 
                        caption=caption,
                        parse_mode='Markdown',
                        timeout=120
                    )
                
                bot.delete_message(user_id, info_msg.message_id)
                
                # Cleanup
                os.remove(video_path)
                os.rmdir(f"downloads/{user_id}")
                
            except Exception as e:
                bot.edit_message_text(f"❌ **Upload failed!**\n\nError: {str(e)[:100]}", user_id, info_msg.message_id)
        else:
            bot.edit_message_text("❌ **Download failed!**\n\nCheck link or try again.", user_id, info_msg.message_id)
    else:
        bot.edit_message_text("❌ **Invalid link!**\n\nMake sure it's from YouTube, Instagram, TikTok, Facebook, or Twitter.", user_id, info_msg.message_id)

# ==================== FLASK WEBHOOK ====================
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/')
def home():
    return f"Video Downloader Bot is running! Total users: {len(total_users)}"

if __name__ == "__main__":
    # Load data
    load_user_stats()
    os.makedirs("downloads", exist_ok=True)
    
    # Start bot
    bot.remove_webhook()
    
    def run_bot():
        print("Bot started polling...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    print("Flask server running on port 8080...")
    app.run(host='0.0.0.0', port=8080)
