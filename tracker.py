import os
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
REG_NUMBER = os.environ.get("REG_NUMBER", "PAK-0072/26")
EMAIL = os.environ.get("APP_EMAIL", "ahmeddmemon@gmail.com")
PORTAL_URL = "https://russia-edu.minobrnauki.gov.ru"
STATE_FILE = "last_status.txt"
SCREENSHOT_FILE = "screen.png"

def send_alert(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=15)

def send_photo(photo_path: str, caption: str):
    if not BOT_TOKEN or not CHAT_ID or not os.path.exists(photo_path):
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": f}, timeout=30)

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

        try:
            print(f"1. Loading {PORTAL_URL}...")
            page.goto(PORTAL_URL, timeout=60000, wait_until="networkidle")
            page.wait_for_timeout(2000)

            print("2. Filling input fields...")
            reg_input = page.locator("input[placeholder*='ABC-0123'], input[placeholder*='Регистрационный']").first
            email_input = page.locator("input[placeholder*='E-mail'], input[placeholder*='e-mail']").first

            reg_input.click()
            reg_input.fill(REG_NUMBER)
            email_input.click()
            email_input.fill(EMAIL)

            print("3. Submitting form...")
            btn = page.locator("button:has-text('Показать'), button:has-text('Show')").first
            btn.click()

            print("4. Waiting for response...")
            page.wait_for_timeout(7000)

            # Capture full page screenshot for verification
            page.screenshot(path=SCREENSHOT_FILE, full_page=True)

            body = page.locator("body").inner_text()

            current_status = None
            if "Consideration of application" in body or "Рассмотрение заявки" in body or "Рассмотрение заявления" in body:
                current_status = "Stage 2: Consideration of application"
            elif "Distribution" in body or "Распределение" in body:
                current_status = "Stage 3: Distribution"
            elif "Verification" in body or "Проверка" in body:
                current_status = "Stage 4: Verification"
            elif "Entering the questionnaire" in body or "Заполнение анкеты" in body:
                current_status = "Stage 1: Entering the questionnaire"

            if current_status:
                print(f"Status Found: {current_status}")
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
                        f"🔄 *Old Status:* {old_status if old_status else 'First Run / Initial Setup'}\n"
                        f"🚀 *Current Status:* *{current_status}*\n\n"
                        f"🔗 [Open Portal]({PORTAL_URL})"
                    )
                    send_alert(msg)
                    send_photo(SCREENSHOT_FILE, f"Portal snapshot for {REG_NUMBER}")
                    print("Notification sent to Telegram!")
                else:
                    print("Status unchanged.")
            else:
                print("Stage text not detected on page. Sending debug screenshot to Telegram...")
                send_photo(SCREENSHOT_FILE, "⚠️ Portal loaded but status text wasn't recognized. Check image.")

        finally:
            browser.close()

if __name__ == "__main__":
    execute_check()
