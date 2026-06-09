import yfinance as yf
import ta
import pandas as pd
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Bot
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8751700772:AAHi8hLJnM1La7kY40KmnwlkEl_JGJ7eKR8"
CHAT_ID = "1130759384"

SYMBOLS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "XAUUSD": "GC=F",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
}

RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
INTERVAL = "1h"
CHECK_MINUTES = 60

def analyze(ticker, name):
    try:
        df = yf.download(ticker, period="7d", interval=INTERVAL, progress=False)
        if df.empty or len(df) < 30:
            return None
        close = df["Close"].squeeze()
        rsi = ta.momentum.RSIIndicator(close, window=14).rsi()
        macd_obj = ta.trend.MACD(close)
        macd_line = macd_obj.macd()
        signal_line = macd_obj.macd_signal()
        prev_rsi = rsi.iloc[-3]
        last_rsi = rsi.iloc[-2]
        prev_macd = macd_line.iloc[-3]
        last_macd = macd_line.iloc[-2]
        prev_sig = signal_line.iloc[-3]
        last_sig = signal_line.iloc[-2]
        price = float(close.iloc[-1])
        signal = None
        if prev_rsi < RSI_OVERSOLD and last_rsi > RSI_OVERSOLD and prev_macd < prev_sig and last_macd > last_sig:
            signal = "BUY"
        elif prev_rsi > RSI_OVERBOUGHT and last_rsi < RSI_OVERBOUGHT and prev_macd > prev_sig and last_macd < last_sig:
            signal = "SELL"
        if signal:
            return {"name": name, "signal": signal, "price": price, "rsi": last_rsi, "macd": last_macd}
        return None
    except Exception as e:
        logger.error(f"Error {name}: {e}")
        return None

async def send_signals(bot):
    for name, ticker in SYMBOLS.items():
        result = analyze(ticker, name)
        if result:
            emoji = "🟢" if result["signal"] == "BUY" else "🔴"
            msg = (f"{emoji} *{result['signal']}* | {result['name']}\n"
                   f"💰 السعر: `{result['price']:.5f}`\n"
                   f"📊 RSI: `{result['rsi']:.2f}`\n"
                   f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                   f"⚠️ _للتداول اليدوي فقط_")
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def scheduled_check(context: ContextTypes.DEFAULT_TYPE):
    await send_signals(context.bot)

async def start(update, context):
    await update.message.reply_text("👋 بوت الإشارات يعمل!\n/scan - فحص فوري\n/status - الحالة")

async def scan_now(update, context):
    await update.message.reply_text("🔍 جاري الفحص...")
    await send_signals(context.bot)
    await update.message.reply_text("✅ انتهى الفحص!")

async def status(update, context):
    await update.message.reply_text(f"✅ البوت يعمل\n📊 الأزواج: {len(SYMBOLS)}\n⏱ كل {CHECK_MINUTES} دقيقة")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan_now))
    app.add_handler(CommandHandler("status", status))
    app.job_queue.run_repeating(scheduled_check, interval=CHECK_MINUTES * 60, first=10)
    logger.info("🤖 البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
