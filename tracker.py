import os
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
REG_NUMBER = os.environ.get("REG_NUMBER", "PAK-0072/26")
EMAIL = os.environ.get("APP_EMAIL", "ahmeddmemon@gmail.com")
PORTAL_URL = "https://russia.edu.minobrnauki.gov.ru"
STATE_FILE = "last_status.txt"

def send_alert(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram configuration missing. Skipping message.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        res.raise_for_status()
    except Exception as exc:
        print(f"Failed to send Telegram alert: {exc}")

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
            print("Connecting to Minobrnauki portal...")
            page.goto(PORTAL_URL, timeout=60000, wait_until="networkidle")

            # Locate the status card container
            card = page.locator("div").filter(has_text="Отслеживание статуса").first
            if card.count() == 0:
                card = page.locator("div").filter(has_text="Tracking the status").first

            # Fill inputs inside the tracking section
            if card.count() > 0:
                card.locator("input").nth(0).fill(REG_NUMBER)
                card.locator("input").nth(1).fill(EMAIL)
                card.locator("button").click()
            else:
                inputs = page.locator("input[type='text'], input:not([type])")
                inputs.nth(0).fill(REG_NUMBER)
                inputs.nth(1).fill(EMAIL)
                page.locator("button:has-text('Show'), button:has-text('Показать')").first.click()

            # Wait for results container to appear
            page.wait_for_selector(
                "text=Information on the application review, text=Информация о ходе рассмотрения",
                timeout=30000
            )
            page.wait_for_timeout(2500)

            # Identify current stage
            body_text = page.locator("body").inner_text()
            current_status = "Unknown / Stage Update"
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

            print(f"Current detected stage: {current_status}")

            # Read cached state
            old_status = ""
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    old_status = f.read().strip()

            # Compare and alert if status updated
            if current_status != old_status:
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    f.write(current_status)

                msg = (
                    f"🎓 *Minobrnauki Status Update!*\n\n"
                    f"📌 *Reg No:* `{REG_NUMBER}`\n"
                    f"🔄 *Previous Stage:* {old_status if old_status else 'Initial Setup'}\n"
                    f"🚀 *Current Stage:* *{current_status}*\n\n"
                    f"🔗 [Open Portal]({PORTAL_URL})"
                )
                send_alert(msg)
                print("Status changed! Telegram message sent.")
            else:
                print("Status unchanged since last check.")

        except Exception as error:
            print(f"Check encountered an issue: {error}")
        finally:
            browser.close()

if __name__ == "__main__":
    execute_check()
