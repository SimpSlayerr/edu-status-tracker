import os
import re
from datetime import datetime, timezone, timedelta
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
REG_NUMBER = os.environ.get("REG_NUMBER", "PAK-0072/26")
EMAIL = os.environ.get("APP_EMAIL", "ahmeddmemon@gmail.com")
PORTAL_URL = "https://russia-edu.minobrnauki.gov.ru"
STATE_FILE = "last_status.txt"
SCREENSHOT_FILE = "screen.png"

# Pakistan Standard Time (UTC+5)
PKT = timezone(timedelta(hours=5))

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

def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip().lower()

def execute_check():
    today_pkt = datetime.now(PKT).strftime("%Y-%m-%d")

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
            page.wait_for_timeout(3000)

            print("2. Filling input fields...")
            reg_input = page.locator("input[placeholder*='ABC-0123'], input[placeholder*='Регистрационный']").first
            email_input = page.locator("input[placeholder*='E-mail'], input[placeholder*='e-mail']").first

            reg_input.scroll_into_view_if_needed()
            reg_input.fill(REG_NUMBER)

            email_input.scroll_into_view_if_needed()
            email_input.fill(EMAIL)

            print("3. Submitting form...")
            submit_btn = page.locator("//input[contains(@placeholder, 'mail') or contains(@placeholder, 'E-mail')]/following::button").first
            submit_btn.scroll_into_view_if_needed()
            submit_btn.click()
            
            email_input.press("Enter")

            print("4. Waiting for results to render...")
            page.wait_for_timeout(10000)

            page.screenshot(path=SCREENSHOT_FILE, full_page=True)

            raw_body = page.locator("body").inner_text()
            norm_body = normalize_text(raw_body)

            current_status = None
            if re.search(r'(consideration of application|рассмотрение заявк|рассмотрение заявлен|на рассмотрении)', norm_body):
                current_status = "Stage 2: Consideration of application"
            elif re.search(r'(distribution|распределени)', norm_body):
                current_status = "Stage 3: Distribution"
            elif re.search(r'(verification|проверк)', norm_body):
                current_status = "Stage 4: Verification"
            elif re.search(r'(questionnaire|ввод анкет|анкет|заполнение|черновик)', norm_body):
                current_status = "Stage 1: Entering the questionnaire"

            if current_status:
                print(f"Status Matched: {current_status}")

                # Read cached status and last recap date
                old_status = ""
                last_recap_date = ""
                if os.path.exists(STATE_FILE):
                    with open(STATE_FILE, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f if l.strip()]
                        if len(lines) >= 1:
                            old_status = lines[0]
                        if len(lines) >= 2:
                            last_recap_date = lines[1]

                # Case 1: Status changed -> Send alert + screenshot
                if current_status != old_status:
                    with open(STATE_FILE, "w", encoding="utf-8") as f:
                        f.write(f"{current_status}\n{today_pkt}\n")

                    msg = (
                        f"🎓 *Minobrnauki Scholarship Status Update!*\n\n"
                        f"📌 *Reg No:* `{REG_NUMBER}`\n"
                        f"🔄 *Old Status:* {old_status if old_status else 'First Run / Initialized'}\n"
                        f"🚀 *Current Status:* *{current_status}*\n\n"
                        f"🔗 [Open Portal]({PORTAL_URL})"
                    )
                    send_alert(msg)
                    send_photo(SCREENSHOT_FILE, f"Current Status: {current_status}")
                    print("Status change detected. Full alert delivered.")

                # Case 2: Status is unchanged
                else:
                    if today_pkt != last_recap_date:
                        # First run of the day -> Send one-time TEXT-ONLY daily check-in (NO screenshot)
                        with open(STATE_FILE, "w", encoding="utf-8") as f:
                            f.write(f"{current_status}\n{today_pkt}\n")

                        recap_msg = (
                            f"☀️ *Daily Check-in: Minobrnauki Tracker*\n\n"
                            f"🤖 Bot is active for the day.\n"
                            f"📌 *Reg No:* `{REG_NUMBER}`\n"
                            f"📊 *Status:* *{current_status}* (Unchanged)\n\n"
                            f"Monitoring silently for the rest of today."
                        )
                        send_alert(recap_msg)
                        print("First check of today: Text-only recap delivered.")
                    else:
                        print(f"Status unchanged ({current_status}) and recap already sent. Silent mode.")

            else:
                print("Stage name not recognized in text. Sending snapshot...")
                send_photo(SCREENSHOT_FILE, "⚠️ Result loaded after submission. Check snapshot.")

        finally:
            browser.close()

if __name__ == "__main__":
    try:
        execute_check()
    except Exception as e:
        error_msg = f"⚠️ *Minobrnauki Tracker Error*\n\n`{str(e)[:300]}`\n\nCheck GitHub Actions run."
        print(error_msg)
        send_alert(error_msg)
        raise e
