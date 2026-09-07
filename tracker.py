import os
import re
import random
import time
from datetime import datetime, timezone, timedelta
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PORTAL_URL = "https://russia-edu.minobrnauki.gov.ru"

# Pakistan Standard Time (UTC+5)
PKT = timezone(timedelta(hours=5))

# ==============================================================================
# ROSTER: Yours pulls from Secrets; Imran is hardcoded
# ==============================================================================
APPLICANTS = [
    {
        "name": "Ahmed",
        "reg_number": os.environ.get("REG_NUMBER", "PAK-0072/26"),
        "email": os.environ.get("APP_EMAIL", "ahmeddmemon@gmail.com"),
        "chat_id": ADMIN_CHAT_ID,
        "state_file": "last_status.txt"
    },
    {
        "name": "Imran",
        "reg_number": "PAK-0162/26",
        "email": "imrannoshadkhan@gmail.com",
        "chat_id": "6846499897",
        "state_file": "status_imran.txt"
    }
]

# ==============================================================================
# UNHINGED POP-CULTURE CHECK-IN QUOTES (First run of every calendar day)
# ==============================================================================
DAILY_QUOTES = [
    # Billy Butcher (The Boys)
    "Oi. Status is completely unchanged—dead in the water. I'm going dark for the day, so pocket your bloody phone and stop waiting on a ping, mate.",

    # Logan Roy (Succession)
    "Status: completely unchanged. Zero movement. I'm switching to silent surveillance until tomorrow, so lock your phone screen and fuck off.",

    # Deadpool
    "Breaking news: Still unchanged! Shocker! I'm diving back into stealth mode, so put your phone down and go live your life, sweetie. I'll buzz you when hell freezes over.",

    # Rick Sanchez (Rick and Morty)
    "Status check: completely frozen. Infinite timelines, and you're staring at Telegram waiting on a Russian database. Going dead silent for the day, Morty. Pocket the phone.",

    # Homelander (The Boys)
    "Not a single pixel shifted today. It's unchanged. I'm going completely silent, so put your phone face-down and stop staring at this chat like I owe you something.",

    # Ultron
    "The portal status remains fossilized and unchanged. I am retreating into silent observation. Do not expect another buzz on your device until Moscow actually evolves.",

    # Jarvis
    "Telemetry confirms status is entirely unchanged, sir. Engaging silent protocol until tomorrow. You may pocket your device with absolute peace of mind.",

    # GLaDOS (Portal)
    "Status report: entirely unchanged. Engaging silent standby. Feel free to put your phone away and contemplate your total lack of progress today.",

    # Alfred Pennyworth
    "Your dossier remains entirely undisturbed, sir. I shall resume silent surveillance, so do pocket your telephone and focus on more pressing matters.",

    # TARS (Interstellar)
    "Telemetry static: status is 100% unchanged. Engaging silent mode. Honesty setting suggests locking your phone and forgetting I exist until tomorrow.",

    # Walter White (Breaking Bad)
    "Nothing has changed! It is completely static! I am killing notifications and monitoring silently. Put the phone down and let the code work.",

    # Tony Stark
    "Status is frozen in place. Unchanged. I'm throwing this bot into stealth mode for the rest of the day, so leave the phone in your pocket and let the AI do the sweating."
]

# ==============================================================================
# STAGE ADVANCEMENT DIALOGUES (Triggered on Status Changes)
# ==============================================================================
STAGE_CHANGE_QUOTES = {
    "Stage 2: Consideration of application": [
        "Pardon the intrusion, sir. The Ministry has finally dusted off your dossier. Active consideration has officially commenced.",
        "Movement detected. The bureaucrats in Moscow have actually opened your file. Mark this date on the calendar.",
        "Alert: The database in Moscow has awoken. Your application is officially under review."
    ],
    "Stage 3: Distribution": [
        "Sensors detect major advancement: Stage 3 Distribution protocol engaged. Russian universities are now reviewing your dossier for placement.",
        "Attention: We have reached Distribution. The Ministry is allocating your university seat. I suggest preparing for Russian winters, sir.",
        "Stage 3 achieved. Suit up. You've officially bypassed the preliminary filter."
    ],
    "Stage 4: Verification": [
        "Final perimeter reached: Stage 4 Verification. The Ministry is running final administrative sign-offs. We are at the endgame.",
        "Stage 4 protocol online. Final security and paperwork checks in progress. Almost across the finish line, sir."
    ]
}

DEFAULT_STAGE_CHANGE = [
    "Pardon the intrusion, sir. Telemetry registers an active state transition on the portal servers.",
    "Sir, an unscheduled protocol update has just cleared the Ministry portal."
]


def send_alert(message: str, target_chat_id: str):
    if not BOT_TOKEN or not target_chat_id:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.ok:
                return
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Telegram alert attempt {attempt + 1} failed for {target_chat_id}: {e}")
            time.sleep(3)


def send_photo(photo_path: str, caption: str, target_chat_id: str):
    if not BOT_TOKEN or not target_chat_id or not os.path.exists(photo_path):
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    for attempt in range(3):
        try:
            with open(photo_path, "rb") as f:
                response = requests.post(
                    url,
                    data={"chat_id": target_chat_id, "caption": caption},
                    files={"photo": f},
                    timeout=30
                )
                if response.ok:
                    return
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Telegram photo attempt {attempt + 1} failed for {target_chat_id}: {e}")
            time.sleep(3)


def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip().lower()


def execute_check():
    now_pkt = datetime.now(PKT)
    today_pkt = now_pkt.strftime("%Y-%m-%d")

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
            for user in APPLICANTS:
                print(f"=== Scraping for {user['name']} ({user['reg_number']}) ===")
                page.goto(PORTAL_URL, timeout=60000, wait_until="networkidle")
                page.wait_for_timeout(3000)

                # Input credentials (sanitized: lowercased and stripped of accidental spaces)
                reg_input = page.locator("input[placeholder*='ABC-0123'], input[placeholder*='Регистрационный']").first
                email_input = page.locator("input[placeholder*='E-mail'], input[placeholder*='e-mail']").first

                reg_input.scroll_into_view_if_needed()
                reg_input.fill(user["reg_number"].strip())

                email_input.scroll_into_view_if_needed()
                email_input.fill(user["email"].strip().lower())

                # Submit form
                submit_btn = page.locator("//input[contains(@placeholder, 'mail') or contains(@placeholder, 'E-mail')]/following::button").first
                submit_btn.scroll_into_view_if_needed()
                submit_btn.click()
                email_input.press("Enter")

                page.wait_for_timeout(10000)

                screenshot_file = f"screen_{user['name'].lower().replace(' ', '_')}.png"
                page.screenshot(path=screenshot_file, full_page=True)

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
                    print(f"Status Matched for {user['name']}: {current_status}")

                    old_status = ""
                    last_recap_date = ""
                    if os.path.exists(user["state_file"]):
                        with open(user["state_file"], "r", encoding="utf-8") as f:
                            lines = [l.strip() for l in f if l.strip()]
                            if len(lines) >= 1:
                                old_status = lines[0]
                            if len(lines) >= 2:
                                last_recap_date = lines[1]

                    # Case 1: Status changed -> Priority Alert + Screenshot to THAT user
                    if current_status != old_status:
                        with open(user["state_file"], "w", encoding="utf-8") as f:
                            f.write(f"{current_status}\n{today_pkt}\n")

                        quote_pool = STAGE_CHANGE_QUOTES.get(current_status, DEFAULT_STAGE_CHANGE)
                        stage_dialogue = random.choice(quote_pool)

                        msg = (
                            f"⚡ *Priority Alert: Protocol Advancement*\n\n"
                            f"{stage_dialogue}\n\n"
                            f"📋 *Dossier:* `{user['reg_number']}`\n"
                            f"⏱️ *Previous Vector:* {old_status if old_status else 'Initial Baseline'}\n"
                            f"🚀 *Active Protocol:* *{current_status}*\n\n"
                            f"🔗 [Direct Portal Uplink]({PORTAL_URL})"
                        )
                        send_alert(msg, user["chat_id"])
                        send_photo(screenshot_file, f"Protocol shifted: {current_status}", user["chat_id"])
                        print(f"Priority alert dispatched to {user['name']}.")

                    # Case 2: First run of the calendar day -> Ultra-compact briefing to THAT user
                    elif today_pkt != last_recap_date:
                        with open(user["state_file"], "w", encoding="utf-8") as f:
                            f.write(f"{current_status}\n{today_pkt}\n")

                        quote = random.choice(DAILY_QUOTES)
                        recap_msg = f"📊 *{current_status}* (Unchanged)\n\n_{quote}_"

                        send_alert(recap_msg, user["chat_id"])
                        print(f"Daily briefing dispatched to {user['name']}.")

                    # Case 3: Subsequent runs today with unchanged status -> Silent
                    else:
                        print(f"{user['name']}: Status unchanged ({current_status}) and already briefed today. Silent mode.")

                else:
                    print(f"Stage name not recognized for {user['name']}. Sending snapshot...")
                    send_photo(screenshot_file, f"⚠️ Unable to parse stage for {user['reg_number']}. Verify snapshot.", user["chat_id"])

        finally:
            browser.close()


if __name__ == "__main__":
    try:
        execute_check()
    except Exception as e:
        error_msg = f"⚠️ *Minobrnauki Tracker Error*\n\n`{str(e)[:300]}`\n\nCheck GitHub Actions run."
        print(error_msg)
        if ADMIN_CHAT_ID:
            send_alert(error_msg, ADMIN_CHAT_ID)
        raise e# ==============================================================================
DAILY_QUOTES = [
    # Billy Butcher (The Boys)
    "Oi. Status is completely unchanged—dead in the water. I'm going dark for the day, so pocket your bloody phone and stop waiting on a ping, mate.",

    # Logan Roy (Succession)
    "Status: completely unchanged. Zero movement. I'm switching to silent surveillance until tomorrow, so lock your phone screen and fuck off.",

    # Deadpool
    "Breaking news: Still unchanged! Shocker! I'm diving back into stealth mode, so put your phone down and go live your life, sweetie. I'll buzz you when hell freezes over.",

    # Rick Sanchez (Rick and Morty)
    "Status check: completely frozen. Infinite timelines, and you're staring at Telegram waiting on a Russian database. Going dead silent for the day, Morty. Pocket the phone.",

    # Homelander (The Boys)
    "Not a single pixel shifted today. It's unchanged. I'm going completely silent, so put your phone face-down and stop staring at this chat like I owe you something.",

    # Ultron
    "The portal status remains fossilized and unchanged. I am retreating into silent observation. Do not expect another buzz on your device until Moscow actually evolves.",

    # Jarvis
    "Telemetry confirms status is entirely unchanged, sir. Engaging silent protocol until tomorrow. You may pocket your device with absolute peace of mind.",

    # GLaDOS (Portal)
    "Status report: entirely unchanged. Engaging silent standby. Feel free to put your phone away and contemplate your total lack of progress today.",

    # Alfred Pennyworth
    "Your dossier remains entirely undisturbed, sir. I shall resume silent surveillance, so do pocket your telephone and focus on more pressing matters.",

    # TARS (Interstellar)
    "Telemetry static: status is 100% unchanged. Engaging silent mode. Honesty setting suggests locking your phone and forgetting I exist until tomorrow.",

    # Walter White (Breaking Bad)
    "Nothing has changed! It is completely static! I am killing notifications and monitoring silently. Put the phone down and let the code work.",

    # Tony Stark
    "Status is frozen in place. Unchanged. I'm throwing this bot into stealth mode for the rest of the day, so leave the phone in your pocket and let the AI do the sweating."
]

# ==============================================================================
# STAGE ADVANCEMENT DIALOGUES (Triggered on Status Changes)
# ==============================================================================
STAGE_CHANGE_QUOTES = {
    "Stage 2: Consideration of application": [
        "Pardon the intrusion, sir. The Ministry has finally dusted off your dossier. Active consideration has officially commenced.",
        "Movement detected. The bureaucrats in Moscow have actually opened your file. Mark this date on the calendar.",
        "Alert: The database in Moscow has awoken. Your application is officially under review."
    ],
    "Stage 3: Distribution": [
        "Sensors detect major advancement: Stage 3 Distribution protocol engaged. Russian universities are now reviewing your dossier for placement.",
        "Attention: We have reached Distribution. The Ministry is allocating your university seat. I suggest preparing for Russian winters, sir.",
        "Stage 3 achieved. Suit up. You've officially bypassed the preliminary filter."
    ],
    "Stage 4: Verification": [
        "Final perimeter reached: Stage 4 Verification. The Ministry is running final administrative sign-offs. We are at the endgame.",
        "Stage 4 protocol online. Final security and paperwork checks in progress. Almost across the finish line, sir."
    ]
}

DEFAULT_STAGE_CHANGE = [
    "Pardon the intrusion, sir. Telemetry registers an active state transition on the portal servers.",
    "Sir, an unscheduled protocol update has just cleared the Ministry portal."
]


def send_alert(message: str, target_chat_id: str):
    if not BOT_TOKEN or not target_chat_id:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=15)


def send_photo(photo_path: str, caption: str, target_chat_id: str):
    if not BOT_TOKEN or not target_chat_id or not os.path.exists(photo_path):
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as f:
        requests.post(url, data={"chat_id": target_chat_id, "caption": caption}, files={"photo": f}, timeout=30)


def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip().lower()


def execute_check():
    now_pkt = datetime.now(PKT)
    today_pkt = now_pkt.strftime("%Y-%m-%d")

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
            for user in APPLICANTS:
                print(f"=== Scraping for {user['name']} ({user['reg_number']}) ===")
                page.goto(PORTAL_URL, timeout=60000, wait_until="networkidle")
                page.wait_for_timeout(3000)

                # Input credentials (sanitized: lowercased and stripped of accidental spaces)
                reg_input = page.locator("input[placeholder*='ABC-0123'], input[placeholder*='Регистрационный']").first
                email_input = page.locator("input[placeholder*='E-mail'], input[placeholder*='e-mail']").first

                reg_input.scroll_into_view_if_needed()
                reg_input.fill(user["reg_number"].strip())

                email_input.scroll_into_view_if_needed()
                email_input.fill(user["email"].strip().lower())

                # Submit form
                submit_btn = page.locator("//input[contains(@placeholder, 'mail') or contains(@placeholder, 'E-mail')]/following::button").first
                submit_btn.scroll_into_view_if_needed()
                submit_btn.click()
                email_input.press("Enter")

                page.wait_for_timeout(10000)

                screenshot_file = f"screen_{user['name'].lower().replace(' ', '_')}.png"
                page.screenshot(path=screenshot_file, full_page=True)

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
                    print(f"Status Matched for {user['name']}: {current_status}")

                    old_status = ""
                    last_recap_date = ""
                    if os.path.exists(user["state_file"]):
                        with open(user["state_file"], "r", encoding="utf-8") as f:
                            lines = [l.strip() for l in f if l.strip()]
                            if len(lines) >= 1:
                                old_status = lines[0]
                            if len(lines) >= 2:
                                last_recap_date = lines[1]

                    # Case 1: Status changed -> Priority Alert + Screenshot to THAT user
                    if current_status != old_status:
                        with open(user["state_file"], "w", encoding="utf-8") as f:
                            f.write(f"{current_status}\n{today_pkt}\n")

                        quote_pool = STAGE_CHANGE_QUOTES.get(current_status, DEFAULT_STAGE_CHANGE)
                        stage_dialogue = random.choice(quote_pool)

                        msg = (
                            f"⚡ *Priority Alert: Protocol Advancement*\n\n"
                            f"{stage_dialogue}\n\n"
                            f"📋 *Dossier:* `{user['reg_number']}`\n"
                            f"⏱️ *Previous Vector:* {old_status if old_status else 'Initial Baseline'}\n"
                            f"🚀 *Active Protocol:* *{current_status}*\n\n"
                            f"🔗 [Direct Portal Uplink]({PORTAL_URL})"
                        )
                        send_alert(msg, user["chat_id"])
                        send_photo(screenshot_file, f"Protocol shifted: {current_status}", user["chat_id"])
                        print(f"Priority alert dispatched to {user['name']}.")

                    # Case 2: First run of the calendar day -> Ultra-compact briefing to THAT user
                    elif today_pkt != last_recap_date:
                        with open(user["state_file"], "w", encoding="utf-8") as f:
                            f.write(f"{current_status}\n{today_pkt}\n")

                        quote = random.choice(DAILY_QUOTES)
                        recap_msg = f"📊 *{current_status}* (Unchanged)\n\n_{quote}_"

                        send_alert(recap_msg, user["chat_id"])
                        print(f"Daily briefing dispatched to {user['name']}.")

                    # Case 3: Subsequent runs today with unchanged status -> Silent
                    else:
                        print(f"{user['name']}: Status unchanged ({current_status}) and already briefed today. Silent mode.")

                else:
                    print(f"Stage name not recognized for {user['name']}. Sending snapshot...")
                    send_photo(screenshot_file, f"⚠️ Unable to parse stage for {user['reg_number']}. Verify snapshot.", user["chat_id"])

        finally:
            browser.close()


if __name__ == "__main__":
    try:
        execute_check()
    except Exception as e:
        error_msg = f"⚠️ *Minobrnauki Tracker Error*\n\n`{str(e)[:300]}`\n\nCheck GitHub Actions run."
        print(error_msg)
        if ADMIN_CHAT_ID:
            send_alert(error_msg, ADMIN_CHAT_ID)
        raise e
