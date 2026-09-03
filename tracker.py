import os
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

        print(f"Connecting to {PORTAL_URL}...")
        page.goto(PORTAL_URL, timeout=60000, wait_until="networkidle")

        # Fill the tracking inputs
        inputs = page.locator("input[placeholder*='ABC-0123'], input[placeholder*='Регистрационный']")
        if inputs.count() > 0:
            inputs.first.fill(REG_NUMBER)
            page.locator("input[placeholder*='E-mail'], input[placeholder*='e-mail']").first.fill(EMAIL)
        else:
            # Fallback to general input fields in card
            all_inputs = page.locator("input[type='text'], input:not([type])")
            all_inputs.nth(0).fill(REG_NUMBER)
            all_inputs.nth(1).fill(EMAIL)

        # Click search button
        page.locator("button:has-text('Показать'), button:has-text('Show')").first.click()

        # Wait for review information card to appear
        page.wait_for_selector(
            "text=Information on the application review, text=Информация о ходе рассмотрения",
            timeout=30000
        )
        page.wait_for_timeout(2500)

        # Detect the current stage
        body_text = page.locator("body").inner_text()
        current_status = "Unknown / Need Review"
        known_stages = [
            "Entering the questionnaire",
            "Consideration of application",
            "Distribution",
            "Verification",
            "Заполнение анкеты",
            "Рассмотрение заявки",
            "Распределение",
            "Проверка"
        ]
        for stage in known_stages:
            if stage in body_text:
                current_status = stage
                break

        print(f"Detected Status: {current_status}")

        old_status = ""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                old_status = f.read().strip()

        if current_status != old_status:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                f.write(current_status)

            msg = (
                f"🎓 *Minobrnauki Status Update!*\n\n"
                f"📌 *Reg No:* `{REG_NUMBER}`\n"
                f"🔄 *Previous Stage:* {old_status if old_status else 'First Run / Initialized'}\n"
                f"🚀 *Current Stage:* *{current_status}*\n\n"
                f"🔗 [Open Portal]({PORTAL_URL})"
            )
            send_alert(msg)
            print("Status updated! Telegram message sent.")
        else:
            print("Status unchanged.")

        browser.close()

if __name__ == "__main__":
    execute_check()
