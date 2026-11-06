import os
import sys
import subprocess
import json
import shutil
import psutil
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ================= تنظیمات =================
TOKEN = "8702326998:AAFywSAFpz4VNlSfLwYe2aUPwFURpOEF49o"
ADMIN_ID = 8612000973  # ستاسو د ټیلګرام عددي ID
DB_FILE = "users_db.json"
# ==========================================

# د معلوماتو ذخیره کول
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

USER_DATA = load_db()
BOT_PROCESSES = {}

# د اصلي فولډرونو جوړول
os.makedirs("hosted_bots", exist_ok=True)

# د هر کاروونکي لپاره جلا فولډر جوړول
def get_user_dir(user_id):
    path = f"hosted_bots/{user_id}"
    os.makedirs(path, exist_ok=True)
    return path

# ================= ۱. اصلي مینو =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    first_name = update.effective_user.first_name
    
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"approved": False, "files": [], "running": False, "has_venv": False}
        save_db(USER_DATA)

    is_approved = USER_DATA[user_id]["approved"]
    status = "✅ Approved" if is_approved else "❌ Not Approved"

    keyboard = [
        [InlineKeyboardButton("📤 Upload File(s)", callback_data="upload")],
        [InlineKeyboardButton("▶️ Run Bot", callback_data="run"), InlineKeyboardButton("⏸ Stop Bot", callback_data="stop")],
        [InlineKeyboardButton("📁 View Files", callback_data="view"), InlineKeyboardButton("🗑 Delete All Files", callback_data="delete")],
        [InlineKeyboardButton("📦 Install Packages", callback_data="install")],
        [InlineKeyboardButton("📜 Live Logs", callback_data="logs"), InlineKeyboardButton("📊 Bot Speed", callback_data="speed")],
        [InlineKeyboardButton("👑 Request Approval", callback_data="request_approval")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"✨ ښه راغلاست {first_name}!\n\n"
        f"🆔 ستاسو ID: `{user_id}`\n"
        f"🔰 ستاسو حالت: {status}\n"
        "-------------------------\n"
        "🌟 **FEATURES:**\n"
        "• ⚡ Ultra Fast Bot Hosting\n"
        "• 🔐 Admin Approval System\n"
        "• 📜 Live Logs Streaming\n"
        "• 📦 Manual Package Install\n"
        "• 📁 Multi-File Support\n"
        "• 🐍 Independent Venv per User\n"
        "-------------------------\n"
        "👇 لاندې تڼۍ وکاروئ:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ================= ۲. د تڼیو مدیریت =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data

    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"approved": False, "files": [], "running": False, "has_venv": False}

    user_dir = get_user_dir(user_id)

    # --- اپلوډ کول ---
    if data == "upload":
        await query.edit_message_text(
            text="📤 خپل فایلونه دلته ولیږئ.\n\n"
                 "⚠️ **مهم:** ستاسو اصلي فایل باید د `bot.py` یا `main.py` په نوم وي.\n"
                 "تاسو کولی شئ نور فایلونه (لکه `.env`، `.json`، انځورونه) هم یو په یو ولیږئ.",
            parse_mode="Markdown"
        )

    # --- د فایلونو لیدل ---
    elif data == "view":
        files = USER_DATA[user_id]["files"]
        if not files:
            await query.edit_message_text("📁 تاسو تر اوسه کوم فایل نه دی اپلوډ کړی.")
        else:
            await query.edit_message_text(f"📁 ستاسو فایلونه:\n" + "\n".join([f"📄 {f}" for f in files]))

    # --- د فایلونو پاکول ---
    elif data == "delete":
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
        USER_DATA[user_id]["files"] = []
        USER_DATA[user_id]["running"] = False
        save_db(USER_DATA)
        await query.edit_message_text("🗑 ټول فایلونه او د هغوی چاپیریال پاک شول.")

    # --- د پیکیج نصبول ---
    elif data == "install":
        await query.edit_message_text(
            text="📦 د نصبولو لپاره د پیکیج نوم ولیکه (د کاما په واسطه جلا کړه).\n"
                 "بېلګه: `requests, python-telegram-bot, python-dotenv`", 
            parse_mode="Markdown"
        )

    # --- باټ چلول (Run) ---
    elif data == "run":
        if not USER_DATA[user_id]["approved"]:
            await query.edit_message_text("❌ ستاسو حساب لا تر اوسه د ادمین لخوا تایید شوی نه دی!\n👑 Request Approval ته لاړ شه.")
            return
            
        files = USER_DATA[user_id]["files"]
        main_file = None
        if "bot.py" in files: main_file = "bot.py"
        elif "main.py" in files: main_file = "main.py"

        if not main_file:
            await query.edit_message_text("❌ ستاسو د چلولو وړ فایل (bot.py یا main.py) نه دی اپلوډ کړی!")
            return

        if user_id in BOT_PROCESSES and BOT_PROCESSES[user_id].poll() is None:
            await query.edit_message_text("⚠️ ستاسو باټ لا دمخه چالان دی!")
            return

        filepath = os.path.join(user_dir, main_file)
        log_path = os.path.join(user_dir, "bot_log.txt")
        
        # د چاپیریال (venv) جوړول که نه وي شوی
        venv_path = os.path.join(user_dir, "venv")
        python_exec = os.path.join(venv_path, "bin", "python") if os.name != 'nt' else os.path.join(venv_path, "Scripts", "python.exe")

        msg = await query.edit_message_text("⏳ د باټ لپاره چاپیریال چمتو کیږي (دا ممکن لږ وخت ونیسي)...")

        try:
            # که venv نه وي، یې جوړوي
            if not os.path.exists(venv_path):
                subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
                USER_DATA[user_id]["has_venv"] = True
                save_db(USER_DATA)
                # د پایتون بنسټیز کتابتونونه نصبوي
                subprocess.run([python_exec, "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run([python_exec, "-m", "pip", "install", "python-telegram-bot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # که requirements.txt وي، هغه نصبوي
            req_file = os.path.join(user_dir, "requirements.txt")
            if os.path.exists(req_file):
                subprocess.run([python_exec, "-m", "pip", "install", "-r", req_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # د لاګ فایل پاکول
            with open(log_path, "w") as f:
                f.write("--- Bot Started ---\n")

            # د پایتون فایل چلول
            process = subprocess.Popen(
                [python_exec, filepath],
                cwd=user_dir, # مهم: فایل باید په خپل فولډر کې چل شي
                stdout=open(log_path, "a"),
                stderr=subprocess.STDOUT
            )
            BOT_PROCESSES[user_id] = process
            USER_DATA[user_id]["running"] = True
            save_db(USER_DATA)
            
            await msg.edit_text(f"✅ ستاسو باټ ({main_file}) په بریالیتوب سره پیل شو! 🚀\n📜 Live Logs وګورئ که ستونزه وي.")
        except Exception as e:
            await msg.edit_text(f"❌ د چلولو پر مهال خطا:\n`{str(e)}`", parse_mode="Markdown")

    # --- باټ بندول (Stop) ---
    elif data == "stop":
        if user_id in BOT_PROCESSES and BOT_PROCESSES[user_id].poll() is None:
            BOT_PROCESSES[user_id].terminate()
            BOT_PROCESSES[user_id].wait()
            USER_DATA[user_id]["running"] = False
            save_db(USER_DATA)
            await query.edit_message_text("⏸ ستاسو باټ په بریالیتوب سره بند شو.")
        else:
            await query.edit_message_text("❌ کوم چالان باټ نه لرې.")

    # --- د لاګونو لیدل ---
    elif data == "logs":
        log_path = os.path.join(user_dir, "bot_log.txt")
        if not os.path.exists(log_path):
            await query.edit_message_text("📜 تر اوسه کوم لاګ نه دی جوړ شوی.")
            return
        
        with open(log_path, "r", errors="ignore") as f:
            logs = f.read()
        
        if not logs.strip():
            logs = "هیڅ پیغام یا خطا نه ده ثبت شوې."
        if len(logs) > 3500:
            logs = "...(پیل پرې شو)...\n" + logs[-3500:]
            
        await query.edit_message_text(f"📜 **Live Logs:**\n\n`{logs}`", parse_mode="Markdown")

    # --- د باټ چټکتیا ---
    elif data == "speed":
        if user_id in BOT_PROCESSES and BOT_PROCESSES[user_id].poll() is None:
            pid = BOT_PROCESSES[user_id].pid
            try:
                p = psutil.Process(pid)
                cpu = p.cpu_percent(interval=0.5)
                mem = p.memory_info().rss / (1024 * 1024) # MB
                await query.edit_message_text(f"📊 **Bot Speed:**\n\n🖥 CPU: `{cpu}%`\n💾 RAM: `{mem:.2f} MB`", parse_mode="Markdown")
            except:
                await query.edit_message_text("❌ د معلوماتو اخیستلو کې ستونزه.")
        else:
            await query.edit_message_text("⚠️ ستاسو باټ چالان نه دی.")

    # --- اجازه غوښتل ---
    elif data == "request_approval":
        if USER_DATA[user_id]["approved"]:
            await query.edit_message_text("✅ ستاسو حساب لا دمخه تایید شوی دی!")
            return
        
        await query.edit_message_text("⏳ ستاسو غوښتنه ادمین ته ولېږل شوه...")
        admin_keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")]]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👑 **نوی غوښتنه!**\n\nکاروونکی: {query.from_user.first_name}\nID: `{user_id}`\n\nاجازه ورکړې؟",
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="Markdown"
        )

    # --- د ادمین لخوا تایید/رد ---
    elif data.startswith("approve_") or data.startswith("reject_"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("❌ تاسو ادمین نه یاست!", show_alert=True)
            return
        
        target_id = data.split("_")[1]
        if data.startswith("approve_"):
            USER_DATA[target_id]["approved"] = True
            save_db(USER_DATA)
            await query.edit_message_text(f"✅ کاروونکی `{target_id}` تایید شو.")
            await context.bot.send_message(chat_id=target_id, text="🎉 ستاسو حساب تایید شو! اوس کولای شئ باټ چل کړئ.")
        else:
            await query.edit_message_text(f"❌ کاروونکی `{target_id}` رد شو.")
            await context.bot.send_message(chat_id=target_id, text="❌ ستاسو غوښتنه رد شوه.")

# ================= ۳. د فایلونو او متنونو اخیستل =================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message = update.message
    user_dir = get_user_dir(user_id)

    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"approved": False, "files": [], "running": False, "has_venv": False}

    # که فایل وي (هر ډول فایل)
    if message.document:
        document = message.document
        # د امنیت لپاره یوازې اجازه ورکوو چې ځینې فایلونه اپلوډ شي
        allowed_exts = ['.py', '.txt', '.json', '.env', '.jpg', '.png', '.mp3', '.mp4', '.csv']
        if not any(document.file_name.endswith(ext) for ext in allowed_exts):
            await message.reply_text(f"❌ دا فایل منل کیږي نه: {document.file_name}\nیوازې دا ډولونه: {', '.join(allowed_exts)}")
            return

        file = await document.get_file()
        filepath = os.path.join(user_dir, document.file_name)
        await file.download_to_drive(filepath)
        
        if document.file_name not in USER_DATA[user_id]["files"]:
            USER_DATA[user_id]["files"].append(document.file_name)
            save_db(USER_DATA)

        await message.reply_text(f"✅ فایل `{document.file_name}` اپلوډ شو!", parse_mode="Markdown")
        return

    # که متن وي (د پیکیج نصبولو لپاره)
    if message.text:
        packages = message.text.strip()
        # د امنیت لپاره یوازې اجازه ورکوو چې د کاما سره جلا شوي وي
        if not all(c.isalnum() or c in ['-', '_', '=', '.', ',', ' ', '>', '<'] for c in packages):
            await message.reply_text("❌ ناسم پیکیج نوم یا ناسم حروف!")
            return
            
        msg = await message.reply_text(f"⏳ د پیکیجونو نصبول روان دي...", parse_mode="Markdown")
        
        venv_path = os.path.join(user_dir, "venv")
        python_exec = os.path.join(venv_path, "bin", "python") if os.name != 'nt' else os.path.join(venv_path, "Scripts", "python.exe")

        try:
            if not os.path.exists(venv_path):
                subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
                subprocess.run([python_exec, "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # د پیکیجونو نصبول
            pkg_list = [p.strip() for p in packages.split(',')]
            subprocess.run([python_exec, "-m", "pip", "install"] + pkg_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            await msg.edit_text(f"✅ پیکیجونه په بریالیتوب سره نصب شول!", parse_mode="Markdown")
        except Exception as e:
            await msg.edit_text(f"❌ د نصبولو پر مهال خطا:\n`{str(e)}`", parse_mode="Markdown")

# ================= اصلي فعالیت =================
def main():
    print("🚀 د باټ ها스ټینګ پینل پیل شو...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_messages))

    print("✅ باټ فعال دی.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()