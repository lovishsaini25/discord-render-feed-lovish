from telethon import TelegramClient, events
import requests, os, json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio

# ====== CONFIG ======
API_ID = int(os.environ.get("TG_API_ID"))
API_HASH = os.environ.get("TG_API_HASH")

# Multiple channels list
CHANNELS = [
    "Stock_aaj_or_kal",
    "fundamental_analysis_lovish",
    "stockinsights01",
    "fundamental3"
]

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
SESSION = "session"
LAST_FILE = "last_multi.json"

client = TelegramClient(SESSION, API_ID, API_HASH)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Multi-Channel News Bot Running")
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

def load_last_ids():
    try:
        with open(LAST_FILE) as f: 
            return json.load(f)
    except: 
        return {}

def save_last_id(channel, msg_id):
    data = load_last_ids()
    data[channel] = msg_id
    with open(LAST_FILE, "w") as f: 
        json.dump(data, f)

def get_last_id(channel):
    data = load_last_ids()
    return data.get(channel, 0)

def post_discord(text):
    if not text: return
    if len(text) > 1900: 
        text = text[:1900]+"...(truncated)"
    try:
        response = requests.post(DISCORD_WEBHOOK, json={"content": text}, timeout=10)
        print(f"Discord: {response.status_code}")
    except Exception as e:
        print(f"Discord error: {e}")

@client.on(events.NewMessage(chats=CHANNELS))
async def handler(event):
    msg = event.message
    mid = msg.id
    chat = await event.get_chat()
    channel_name = chat.username or chat.title
    
    print(f"📨 {channel_name}: Message ID {mid}")
    
    if mid <= get_last_id(channel_name): 
        return
    
    txt = msg.message or ""
    link = f"https://t.me/{channel_name}/{mid}"
    
    if msg.media:
        txt += "\n[📎 Media attached — view on Telegram]"
    
    # Include channel source in Discord message
    discord_message = f"📢 **{channel_name}**\n\n{txt}\n\n🔗 [View Message]({link})"
    
    post_discord(discord_message)
    save_last_id(channel_name, mid)
    print(f"✅ Forwarded from {channel_name}")

async def main():
    await client.start(bot_token=os.environ['BOT_TOKEN'])
    print("✅ Connected to Telegram")
    
    # Verify access to all channels
    for channel in CHANNELS:
        try:
            entity = await client.get_entity(channel)
            print(f"📢 Connected to: {entity.title} (@{channel})")
        except Exception as e:
            print(f"❌ Cannot access {channel}: {e}")
    
    print(f"📡 Monitoring {len(CHANNELS)} channels...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
