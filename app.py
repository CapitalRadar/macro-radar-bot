import os
import requests
import feedparser
import time
from datetime import datetime
from deep_translator import GoogleTranslator
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
]

SEND_HOURS = [6, 11, 16, 21]  # Челябинск UTC+5
last_sent_hour = None


# -------- BTC PRICE --------
def get_btc_data():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
        )
        data = r.json()
        return {
            "price": float(data["lastPrice"]),
            "change": float(data["priceChangePercent"]),
        }
    except:
        return None


# -------- NASDAQ + DXY --------
def get_market_data():
    try:
        url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC,^DXY"
        r = requests.get(url)
        data = r.json()["quoteResponse"]["result"]

        nasdaq = None
        dxy = None

        for item in data:
            if item["symbol"] == "^IXIC":
                nasdaq = {
                    "price": item["regularMarketPrice"],
                    "change": item["regularMarketChangePercent"],
                }
            elif item["symbol"] == "^DXY":
                dxy = {
                    "price": item["regularMarketPrice"],
                    "change": item["regularMarketChangePercent"],
                }

        return nasdaq, dxy
    except:
        return None, None


# -------- TRANSLATE --------
def translate_text(text):
    try:
        return GoogleTranslator(source="auto", target="ru").translate(text)
    except:
        return text


# -------- CLASSIFY --------
def classify_news(title):
    t = title.lower()

    if "rate" in t or "inflation" in t:
        return "🔵 Денежная политика"
    elif "etf" in t:
        return "🟣 ETF и институционалы"
    elif "nasdaq" in t or "tech" in t:
        return "🟢 Технологический рынок"
    elif "dollar" in t or "yield" in t:
        return "🟡 Доллар и облигации"
    elif "war" in t or "sanction" in t:
        return "🔴 Геополитика"
    else:
        return "🟠 Крипторынок"


# -------- GET NEWS --------
def get_news():
    headlines = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:2]:
            headlines.append(entry.title)
    return headlines[:5]


# -------- MARKET MODE --------
def market_mode(btc, nasdaq, dxy):
    score = 0

    if btc and btc["change"] > 0:
        score += 1
    if nasdaq and nasdaq["change"] > 0:
        score += 1
    if dxy and dxy["change"] < 0:
        score += 1

    return "🟢 RISK-ON" if score >= 2 else "🔴 RISK-OFF"


# -------- SEND MESSAGE --------
def send_message():
    global last_sent_hour

    btc = get_btc_data()
    nasdaq, dxy = get_market_data()
    news = get_news()

    mode = market_mode(btc, nasdaq, dxy)

    message = "📊 <b>Crypto Macro Radar</b>\n\n"

    if btc:
        emoji = "🟢" if btc["change"] > 0 else "🔴"
        message += f"💰 <b>BTC:</b> ${btc['price']:,.0f} {emoji} {btc['change']:.2f}%\n"

    if nasdaq:
        emoji = "🟢" if nasdaq["change"] > 0 else "🔴"
        message += f"📈 <b>NASDAQ:</b> {emoji} {nasdaq['change']:.2f}%\n"

    if dxy:
        emoji = "🔴" if dxy["change"] > 0 else "🟢"
        message += f"💵 <b>DXY:</b> {emoji} {dxy['change']:.2f}%\n"

    message += f"\n⚖️ <b>Режим рынка:</b> {mode}\n"

    message += "\n━━━━━━━━━━━━━━━━\n\n"
    message += "📰 <b>Главные события</b>\n\n"

    for n in news:
        translated = translate_text(n)
        category = classify_news(n)

        message += f"{category}\n"
        message += f"{translated}\n\n"

    message += "━━━━━━━━━━━━━━━━\n"
    message += f"⏱ Обновление: {datetime.now().strftime('%H:%M')} (Челябинск)"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    requests.post(url, data=data)

    # фиксируем именно челябинский час
    now = datetime.utcnow()
    last_sent_hour = (now.hour + 5) % 24


# -------- SCHEDULER --------
def scheduler():
    global last_sent_hour
    while True:
        now = datetime.utcnow()
        chelyabinsk_hour = (now.hour + 5) % 24

        if chelyabinsk_hour in SEND_HOURS and last_sent_hour != chelyabinsk_hour:
            send_message()

        time.sleep(60)


# -------- WEB SERVER --------
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
    send_message()  # тестовое сообщение при деплое
    threading.Thread(target=scheduler).start()
    run_server()
