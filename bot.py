import telebot
import subprocess
import os
import psutil
import zipfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = "8264209354:AAGUBDHsLpir61C3CTiQFz6_cWVBWOrczAI"
OWNER_ID = 6940098775

bot = telebot.TeleBot(TOKEN)

running = {}

# ---------------- RENDER PORT FIX ----------------

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_server).start()

# ---------------- OWNER CHECK ----------------

def owner(user):
    return user == OWNER_ID


# ---------------- START ----------------

@bot.message_handler(commands=['start'])
def start(m):

    if not owner(m.from_user.id):
        return

    bot.reply_to(m,
"""
⚡ Hosting Manager

Commands:

/bots
/startbot <file>
/stopbot <file>
/restartbot <file>

/run <command>

/status
/logs <file>

/install <package>

Send .py file → upload bot
Send .zip → auto extract
""")


# ---------------- SYSTEM STATUS ----------------

@bot.message_handler(commands=['status'])
def status(m):

    if not owner(m.from_user.id):
        return

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    bot.reply_to(m,f"""
💻 Server Status

CPU: {cpu}%
RAM: {ram}%
Disk: {disk}%
""")


# ---------------- RUN COMMAND ----------------

@bot.message_handler(commands=['run'])
def run(m):

    if not owner(m.from_user.id):
        return

    cmd = m.text.replace("/run ","")

    try:
        out = subprocess.check_output(cmd,shell=True).decode()

        if len(out) > 4000:
            out = out[:4000]

        bot.reply_to(m,out)

    except Exception as e:
        bot.reply_to(m,str(e))


# ---------------- LIST BOTS ----------------

@bot.message_handler(commands=['bots'])
def bots(m):

    if not owner(m.from_user.id):
        return

    os.makedirs("bots", exist_ok=True)

    files = os.listdir("bots")

    msg = "📂 Bots:\n"

    for f in files:
        msg += f"\n{f}"

    bot.reply_to(m,msg)


# ---------------- START BOT ----------------

@bot.message_handler(commands=['startbot'])
def startbot(m):

    if not owner(m.from_user.id):
        return

    file = m.text.split(" ")[1]

    path = f"bots/{file}"

    if not os.path.exists(path):

        bot.reply_to(m,"File not found")
        return

    process = subprocess.Popen(["python",path])

    running[file] = process

    bot.reply_to(m,f"🚀 Started {file}")


# ---------------- STOP BOT ----------------

@bot.message_handler(commands=['stopbot'])
def stopbot(m):

    if not owner(m.from_user.id):
        return

    file = m.text.split(" ")[1]

    if file in running:

        running[file].terminate()

        del running[file]

        bot.reply_to(m,f"🛑 Stopped {file}")

    else:

        bot.reply_to(m,"Bot not running")


# ---------------- RESTART BOT ----------------

@bot.message_handler(commands=['restartbot'])
def restart(m):

    if not owner(m.from_user.id):
        return

    file = m.text.split(" ")[1]

    if file in running:
        running[file].terminate()

    process = subprocess.Popen(["python",f"bots/{file}"])

    running[file] = process

    bot.reply_to(m,f"♻ Restarted {file}")


# ---------------- INSTALL PACKAGE ----------------

@bot.message_handler(commands=['install'])
def install(m):

    if not owner(m.from_user.id):
        return

    pkg = m.text.split(" ")[1]

    subprocess.run(f"pip install {pkg}",shell=True)

    bot.reply_to(m,f"✅ Installed {pkg}")


# ---------------- LOGS ----------------

@bot.message_handler(commands=['logs'])
def logs(m):

    if not owner(m.from_user.id):
        return

    name = m.text.split(" ")[1]

    file = f"logs/{name}.log"

    if os.path.exists(file):

        with open(file) as f:
            data = f.read()[-3500:]

        bot.reply_to(m,data)

    else:

        bot.reply_to(m,"No logs")


# ---------------- FILE UPLOAD ----------------

@bot.message_handler(content_types=['document'])
def upload(message):

    if not owner(message.from_user.id):
        return

    os.makedirs("uploads", exist_ok=True)
    os.makedirs("bots", exist_ok=True)

    file_info = bot.get_file(message.document.file_id)

    data = bot.download_file(file_info.file_path)

    name = message.document.file_name

    path = f"uploads/{name}"

    with open(path,"wb") as f:
        f.write(data)


    if name.endswith(".zip"):

        with zipfile.ZipFile(path,"r") as zip_ref:
            zip_ref.extractall("bots")

        bot.reply_to(message,"📦 ZIP extracted to bots folder")

    elif name.endswith(".py"):

        os.rename(path,f"bots/{name}")

        bot.reply_to(message,f"✅ Uploaded bot: {name}")

    else:

        bot.reply_to(message,"File uploaded")


print("🚀 Hosting Manager Started")

bot.infinity_polling()
