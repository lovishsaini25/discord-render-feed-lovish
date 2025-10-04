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
        
        logging.info(f"🔥 NEW MESSAGE DETECTED!")
        logging.info(f"Channel: {channel_name}")
        logging.info(f"Message ID: {mid}")
        logging.info(f"Last processed ID: {last_id()}")
        logging.info(f"Message text: {(msg.message or 'No text')[:200]}")
        
        if mid <= last_id():
            logging.info("⏭️ Message already processed, skipping")
            return
        
        txt = msg.message or "Media message"
        link = f"https://t.me/{channel_name}/{mid}" if hasattr(chat, 'username') and chat.username else f"Message ID: {mid}"
        
        if msg.media:
            txt += "\n[📎 Media attached]"
        
        discord_message = f"📢 **{channel_name}**\n\n{txt}\n\n🔗 {link}"
        
        if post_discord(discord_message):
            save_id(mid)
            logging.info("✅ Message forwarded successfully")
        else:
            logging.error("❌ Failed to forward to Discord")
            
    except Exception as e:
        logging.error(f"❌ Handler error: {e}")

async def main():
    try:
        logging.info("🚀 Starting Telegram bot...")
        
        # Start client
        await client.start(bot_token=os.environ['BOT_TOKEN'])
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
