# requirements: telethon, requests
# pip install telethon requests

from telethon import TelegramClient, events
import requests, os, json

# ====== CONFIG ======
API_ID = int(os.environ.get("TG_API_ID"))      # from my.telegram.org
API_HASH = os.environ.get("TG_API_HASH")
CHANNEL = "earnings_pulse"                     # without @
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
SESSION = "session"
LAST_FILE = "last.json"

# keywords to forward (edit or leave empty to forward everything)
KEYWORDS = ["result","results","earnings","profit","loss","quarter","q1","q2","q3","q4"]
# ====================

client = TelegramClient(SESSION, API_ID, API_HASH)

def last_id():
    try:
        with open(LAST_FILE) as f: return json.load(f)["id"]
    except: return 0

def save_id(i):
    with open(LAST_FILE,"w") as f: json.dump({"id":i},f)

def post_discord(text):
    if not text: return
    if len(text) > 1900: text = text[:1900]+"...(truncated)"
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": text})
    except Exception as e:
        print("Discord error:", e)

@client.on(events.NewMessage(chats=CHANNEL))
async def handler(event):
    msg = event.message
    mid = msg.id
    if mid <= last_id(): return
    txt = msg.message or ""
    if KEYWORDS and not any(k in txt.lower() for k in KEYWORDS): return
    link = f"https://t.me/{CHANNEL}/{mid}"
    if msg.media:
        txt += "\n[Media attached — view on Telegram]"
    post_discord(f"📢 {txt}\n\n🔗 {link}")
    save_id(mid)

async def main():
    await client.start()
    print(f"Listening to t.me/{CHANNEL} ...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
