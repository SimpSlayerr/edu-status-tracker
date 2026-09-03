import os
import re
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
REG_NUMBER = os.environ.get("REG_NUMBER", "PAK-0072/26")
EMAIL = os.environ.get("APP_EMAIL", "ahmeddmemon@gmail.com")
PORTAL_URL = "https://russia-edu.minobrnauki.gov.ru"
STATE_FILE = "last_status.txt"

def send_alert(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secret!")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    res = requests.post(url, json=payload, timeout=15)
    res.raise_for_status()

def execute_check():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"1. Connecting to {PORTAL_URL}...")
        page.goto(PORTAL_URL, timeout=60000, wait_until="networkidle")

        print("2. Filling form inputs...")
        inputs = page.locator("input[type='text'], input:not([type])")
        inputs.nth(0).fill(REG_NUMBER)
        inputs.nth(1).fill(EMAIL)

        print("3. Submitting form...")
        btn = page.locator("button, input[type='button'], input[type='submit']").filter(
            has_text=re.compile(r"Показать|Show", re.I)
        )
        if btn.count() > 0:
            btn.first.click()
        else:
            inputs.nth(1).press("Enter")

        print(f"4. Waiting for details matching {REG_NUMBER}...")
        page.locator(f"text={REG_NUMBER}").first.wait_for(timeout=30000)
        page.wait_for_timeout(2000)

        # Detect the active stage from the page
        body = page.locator("body").inner_text()
        if "Consideration of application" in body or "Рассмотрение заявки" in body or "Рассмотрение заявления" in body:
            current_status = "Stage 2: Consideration of application"
        elif "Distribution" in body or "Распределение" in body:
            current_status = "Stage 3: Distribution"
        elif "Verification" in body or "Проверка" in body:
            current_status = "Stage 4: Verification"
        elif "Entering the questionnaire" in body or "Заполнение анкеты" in body:
            current_status = "Stage 1: Entering the questionnaire"
        else:
            current_status = "Active / Status loaded (Review portal manually)"

        print(f"Detected Status: {current_status}")

        old_status = ""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                old_status = f.read().strip()

        if current_status != old_status:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                f.write(current_status)

            msg = (
                f"🎓 *Minobrnauki Scholarship Status Update!*\n\n"
                f"📌 *Reg No:* `{REG_NUMBER}`\n"
                f"🔄 *Old Status:* {old_status if old_status else 'First Run / Initialized'}\n"
                f"🚀 *New Status:* *{current_status}*\n\n"
                f"🔗 [Open Portal]({PORTAL_URL})"
            )
            send_alert(msg)
            print("Telegram alert sent successfully!")
        else:
            print("Status unchanged since last check.")

        browser.close()

if __name__ == "__main__":
    execute_check()
