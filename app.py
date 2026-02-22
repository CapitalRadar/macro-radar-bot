import os
import requests

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

message = "Macro Radar Test ✅\n\nБот подключён и работает."

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

payload = {
    "chat_id": CHAT_ID,
    "text": message
}

requests.post(url, data=payload)
