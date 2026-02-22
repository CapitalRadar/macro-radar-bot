import os
import requests
import feedparser
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# --------- RSS SOURCES ----------
RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
]

# --------- GET BTC PRICE ----------
def get_btc_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
        return float(r.json()["price"])
    except:
        return None

# --------- GET NEWS ----------
def get_news():
    headlines = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            headlines.append(entry.title)
    return headlines[:5]

# --------- SEND MESSAGE ----------
def send_message():
    btc_price = get_btc_price()
    news = get_news()

    message = "📊 Crypto Macro Radar\n\n"

    if btc_price:
        message += f"💰 BTC: ${btc_price:,.2f}\n\n"

    message += "📰 Top Headlines:\n"
    for n in news:
        message += f"• {n}\n"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=data)

# --------- WEB SERVER ----------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Macro Radar running")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

if __name__ == "__main__":
    send_message()
    run_server()
