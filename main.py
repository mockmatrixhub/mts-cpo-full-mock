# ssc_telegram_bot_2025_FINAL.py
# TESTED & WORKING ON RAILWAY DEC 2025

import os
import asyncio
import logging
import random
import time

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8527995328:AAGqbxg0UKQzZSiBYXBzutHjLnVbcck_zNw")

HUMAN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9",
    "Referer": "https://sscexams.cbexams.com/",
}

# ==================== FETCH METHODS ====================
async def fetch_with_playwright(url):
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=HUMAN_HEADERS["User-Agent"],
                locale="en-IN",
                timezone_id="Asia/Kolkata"
            )
            
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
            
            page = await context.new_page()
            logger.info("Opening SSC homepage...")
            await page.goto("https://sscexams.cbexams.com/", timeout=60000)
            await page.wait_for_timeout(random.randint(8000, 12000))
            
            logger.info("Opening target URL...")
            await page.goto(url, timeout=180000, wait_until="networkidle")
            await page.wait_for_timeout(random.randint(10000, 15000))
            
            html = await page.content()
            await browser.close()
            
            if len(html) > 50000:
                return html
    except Exception as e:
        logger.error(f"Playwright failed: {e}")
    return None

async def fetch_with_curl(url):
    try:
        from curl_cffi import requests as curl_req
        r = curl_req.get(url, impersonate="chrome127", timeout=90, headers=HUMAN_HEADERS)
        if len(r.text) > 50000:
            return r.text
    except Exception as e:
        logger.error(f"curl-cffi failed: {e}")
    return None

async def fetch_ssc_response(url):
    methods = [
        ("Playwright", fetch_with_playwright),
        ("curl-cffi", fetch_with_curl),
    ]
    
    for name, func in methods:
        logger.info(f"Trying {name}...")
        result = await func(url)
        if result and len(result) > 50000:
            logger.info(f"✅ SUCCESS with {name}")
            return result
        await asyncio.sleep(10)
    
    return None

# ==================== TELEGRAM BOT ====================
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 *SSC Response Fetcher 2025*\n\n"
        "Send SSC link with EncKey\n"
        "Get full HTML in .txt file",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if "EncKey=" not in url:
        await update.message.reply_text("❌ Invalid link")
        return
    
    msg = await update.message.reply_text("🔄 Fetching... 30-90s ⏳")
    
    html = await fetch_ssc_response(url)
    
    if html and len(html) > 50000:
        filename = f"SSC_{int(time.time())}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        
        await msg.edit_text("✅ Uploading...")
        
        with open(filename, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.effective_user.id,
                document=f,
                filename="SSC_RESPONSE.txt"
            )
        
        os.remove(filename)
        await msg.delete()
    else:
        await msg.edit_text("❌ All methods failed")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
