from telethon import TelegramClient, events
import requests, os, json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio
import logging
from datetime import datetime

# Configure logging for GitHub/deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

# ====== CONFIG ======
API_ID = int(os.environ.get("TG_API_ID"))
API_HASH = os.environ.get("TG_API_HASH")
CHANNELS = ["Stock_aaj_or_kal", "fundamental_analysis_lovish", "stockinsights01", "fundamental3"]
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
SESSION = "session"
LAST_FILE = "last.json"

client = TelegramClient(SESSION, API_ID, API_HASH)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        
        # Status page with logs
        status = f"""
        <h1>Telegram Bot Status</h1>
        <p>Time: {datetime.now()}</p>
        <p>Monitoring {len(CHANNELS)} channels</p>
        <pre>{open('bot.log').read() if os.path.exists('bot.log') else 'No logs yet'}</pre>
        """
        self.wfile.write(status.encode())
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
    try:
        response = requests.post(DISCORD_WEBHOOK, json={"content": text}, timeout=10)
        logging.info(f"Discord: {response.status_code}")
        return response.status_code == 204
    except Exception as e:
        logging.error(f"Discord error: {e}")
        return False

# Test function to verify Telegram connection
async def test_telegram_connection():
    try:
        # Test basic connection
        me = await client.get_me()
        logging.info(f"✅ Logged in as: {me.username or me.first_name}")
        
        # Test each channel
        for channel in CHANNELS:
            try:
                entity = await client.get_entity(channel)
                logging.info(f"📢 Channel found: {entity.title} (@{getattr(entity, 'username', 'no_username')})")
                
                # Get recent messages to test read access
                messages = await client.get_messages(entity, limit=5)
                logging.info(f"📊 {channel}: Can read {len(messages)} recent messages")
                
                for msg in messages[:2]:  # Log first 2 messages
                    logging.info(f"  - ID: {msg.id}, Text: {(msg.message or 'Media/No text')[:100]}")
                    
            except Exception as e:
                logging.error(f"❌ Cannot access {channel}: {e}")
                
        return True
        
    except Exception as e:
        logging.error(f"❌ Telegram connection failed: {e}")
        return False

@client.on(events.NewMessage(chats=CHANNELS))
async def handler(event):
    try:
        msg = event.message
        mid = msg.id
        chat = await event.get_chat()
        channel_name = getattr(chat, 'username', None) or chat.title or 'Unknown'
        
        logging.info(f"🔥 NEW MESSAGE from {channel_name}")
        logging.info(f"Message ID: {mid}, Last processed: {get_last_id(channel_name)}")
        
        # Check last ID per channel
        if mid <= get_last_id(channel_name):
            logging.info(f"⏭️ Already processed for {channel_name}")
            return
        
        txt = msg.message or "Media message"
        
        if msg.media:
            txt += "\n\n[📎 Media content]"
        
        discord_message = f"{txt}"
        
        if post_discord(discord_message):
            save_last_id(channel_name, mid)  # Save per channel
            logging.info(f"✅ Forwarded from {channel_name}")
            
    except Exception as e:
        logging.error(f"❌ Handler error: {e}")

async def main():
    try:
        logging.info("🚀 Starting Telegram bot...")
        
        # Start client
        await client.start()
        logging.info("✅ Telegram client started")
        
        # Test connection
        if await test_telegram_connection():
            logging.info("🎉 All systems ready!")
        else:
            logging.error("⚠️ Some issues detected, but continuing...")
        
        # Send startup notification to Discord
        post_discord("🤖 Telegram News Bot started successfully!")
        
        logging.info("📡 Listening for new messages...")
        await client.run_until_disconnected()
        
    except Exception as e:
        logging.error(f"❌ Startup failed: {e}")
        post_discord(f"❌ Bot startup failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
