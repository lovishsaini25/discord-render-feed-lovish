from telethon import TelegramClient, events
import requests, os, json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio

# ====== CONFIG ======
API_ID = int(os.environ.get("TG_API_ID"))
API_HASH = os.environ.get("TG_API_HASH")
CHANNEL = "Stock_aaj_or_kal"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
SESSION = "session"
LAST_FILE = "last.json"

client = TelegramClient(SESSION, API_ID, API_HASH)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"News Bot is running")
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

def last_id():
    try:
        with open(LAST_FILE) as f: 
            return json.load(f)["id"]
    except: 
        return 0

def save_id(i):
    with open(LAST_FILE,"w") as f: 
        json.dump({"id":i},f)

def post_discord(text):
    if not text: return
    if len(text) > 1900: 
        text = text[:1900]+"...(truncated)"
    try:
        response = requests.post(DISCORD_WEBHOOK, json={"content": text}, timeout=10)
        print(f"Discord response: {response.status_code}")
    except Exception as e:
        print(f"Discord error: {e}")

@client.on(events.NewMessage(chats=CHANNEL))
async def handler(event):
    msg = event.message
    mid = msg.id
    txt = msg.message or ""
    
    print(f"📨 New message ID: {mid}, Last ID: {last_id()}")
    print(f"📄 Message: {txt[:100]}...")
    
    if mid <= last_id(): 
        print("⏭️ Message already processed, skipping")
        return
    
    link = f"https://t.me/{CHANNEL}/{mid}"
    
    if msg.media:
        txt += "\n[📎 Media attached — view on Telegram]"
    
    discord_message = f"📢 {txt}\n\n🔗 {link}"
    post_discord(discord_message)
    save_id(mid)
    print("✅ Message forwarded to Discord")

async def main():
    await client.start(bot_token=os.environ['BOT_TOKEN'])
    print("✅ Connected to Telegram")
    
    # Get recent messages to test
    try:
        entity = await client.get_entity(CHANNEL)
        print(f"📢 Channel: {entity.title}")
        
        # Get last 3 messages to see if bot can read the channel
        messages = await client.get_messages(CHANNEL, limit=3)
        print(f"📊 Found {len(messages)} recent messages")
        for msg in messages:
            print(f"  - ID: {msg.id}, Text: {(msg.message or 'No text')[:50]}...")
            
    except Exception as e:
        print(f"❌ Channel access error: {e}")
    
    print(f"📡 Listening to t.me/{CHANNEL} ...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
