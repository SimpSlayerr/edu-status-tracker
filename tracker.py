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
# ROSTER: Ongoing tracking for Ahmed; Imran retires after tomorrow's first run
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
        "state_file": "status_imran.txt",
        "retire_after_next_briefing": True  # Sends farewell on next new-day run, then terminates
    }
]

# ==============================================================================
# 30 PURE RAW QUOTES (Zero character names, zero show titles)
# ==============================================================================
DAILY_QUOTES = [
    "Well, well, well, how the turntables... haven't turned at all. Not even a single degree. Zero updates today.",
    "Did I stutter? Status is unchanged. Back to work.",
    "Here's what's gonna happen: You're gonna put the phone down, leave the browser alone, and go about your day. Zero delta.",
    "Say my name? Still Stage 1 on the registry.",
    "Did you know you have rights? The Constitution says you do. But Moscow's portal doesn't care. Nothing changed.",
    "That's what I do: I drink, and I know things. And today, I know Moscow hasn't touched your file.",
    "Winter is coming, but this status update is not. Telemetry completely static.",
    "Why do you think I came all this way? Certainly not to watch an empty database. Screen off.",
    "This little maneuver is going to cost us 51 years. Another day, another zero on the portal.",
    "I can only show you the door. You have to wait outside until Moscow decides to unlock it.",
    "You're waiting for a train that hasn't even left the station yet. Put the phone down.",
    "Why so serious? It's just an unchanged Russian portal. Put a smile on that face and close Telegram.",
    "Some men just want to watch the world burn. Others just want Moscow to click one button. Today is not that day.",
    "I am inevitable. But this Russian portal? Completely immovable. Zero change detected.",
    "Say 'refresh' again. Say 'refresh' again, I dare you, I double dare you! Status unchanged.",
    "The things you own end up owning you—like this status tracker. Let it go. Zero movement detected.",
    "By order of the Peaky Blinders... do not check this damn portal until tomorrow. Stand down.",
    "I made them an application they couldn't refuse... yet here we are, still waiting. Respect the timeline.",
    "Yeah, well, that's just, like, the database's opinion, man. Abide the wait.",
    "Could this portal BE any slower? Absolutely nothing changed today.",
    "Status update: Bone-dry. Zero movement detected. As predictable as it is devastating. Dismissed.",
    "Give me all the bacon and eggs you have. Because you're getting zero status updates from Russia today.",
    "I automated this script because human patience is inefficient. The status didn't move. Go away.",
    "Are we there yet? No. Are we there yet? Still no. Stage 1 locked in.",
    "You are not serious people if you think Moscow moves on your schedule. Go do some real work.",
    "You shall not pass to Stage 2 yet. The Ministry stands firm. Pocket the phone.",
    "Patience you must have. Move today, the portal does not.",
    "Are you not entertained? Too bad, because the Ministry gave us zero entertainment today.",
    "Life is like a box of chocolates. Except this portal—you already know what you're getting: nothing.",
    "Houston, we have a problem: absolutely nothing is happening on this server."
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

# ==============================================================================
# FINAL FAREWELL DIALOGUE (Circuit / Munna Bhai)
# ==============================================================================
FAREWELL_MESSAGE = (
    "🛑 *CIRCUIT REPORTING: SHUTDOWN COMPLETE*\n\n"
    "\"_Bhai ne bola bot band karne ka toh band karne ka._\n\n"
    "_Imran bhai, tension nahi lene ka re mamu. Ab kal subah se carrom ramwanu, juice peewanu, majja ni life! "
    "Pura system server se logout maar diya hai._\n\n"
    "_Mast jadoo ki jhappi lo aur aaram se so jao!_\""
)


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


def scrape_applicant(browser, user):
    """Scrapes one applicant with an isolated browser context and dynamic polling."""
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    screenshot_file = f"screen_{user['name'].lower().replace(' ', '_')}.png"
    matched_status = None

    try:
        page.goto(PORTAL_URL, timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(3000)

        reg_input = page.locator("input[placeholder*='ABC-0123'], input[placeholder*='Регистрационный']").first
        email_input = page.locator("input[placeholder*='E-mail'], input[placeholder*='e-mail']").first

        reg_input.scroll_into_view_if_needed()
        reg_input.fill("")
        reg_input.fill(user["reg_number"].strip())

        email_input.scroll_into_view_if_needed()
        email_input.fill("")
        email_input.fill(user["email"].strip().lower())

        submit_btn = page.locator("//input[contains(@placeholder, 'mail') or contains(@placeholder, 'E-mail')]/following::button").first
        submit_btn.scroll_into_view_if_needed()
        submit_btn.click()

        # Dynamic Polling: Check DOM every 2s up to 26s
        for _ in range(13):
            page.wait_for_timeout(2000)
            norm_body = normalize_text(page.locator("body").inner_text())

            if re.search(r'(consideration of application|рассмотрение заявк|рассмотрение заявлен|на рассмотрении)', norm_body):
                matched_status = "Stage 2: Consideration of application"
                break
            elif re.search(r'(distribution|распределени)', norm_body):
                matched_status = "Stage 3: Distribution"
                break
            elif re.search(r'(verification|проверк)', norm_body):
                matched_status = "Stage 4: Verification"
                break
            elif re.search(r'(questionnaire|ввод анкет|анкет|заполнение|черновик)', norm_body):
                matched_status = "Stage 1: Entering the questionnaire"
                break

        page.screenshot(path=screenshot_file, full_page=True)
        return matched_status, screenshot_file

    finally:
        page.close()
        context.close()


def execute_check():
    now_pkt = datetime.now(PKT)
    today_pkt = now_pkt.strftime("%Y-%m-%d")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        try:
            for index, user in enumerate(APPLICANTS):
                state_file = user["state_file"]

                # If applicant has been retired in previous runs, bypass entirely
                if os.path.exists(state_file):
                    with open(state_file, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f if l.strip()]
                        if len(lines) >= 3 and lines[2] == "RETIRED":
                            print(f"⏩ Tracking deactivated for {user['name']} (RETIRED). Skipping entirely.")
                            continue

                print(f"=== Scraping for {user['name']} ({user['reg_number']}) ===")

                # Cooldown before consecutive scraping attempts
                if index > 0:
                    time.sleep(10)

                # Attempt 1
                current_status, screenshot_file = scrape_applicant(browser, user)

                # Auto-retry once if status missed due to network lag
                if not current_status:
                    print(f"⚠️ Initial query missed for {user['name']}. Retrying in 8 seconds...")
                    time.sleep(8)
                    current_status, screenshot_file = scrape_applicant(browser, user)

                if current_status:
                    print(f"Status Matched for {user['name']}: {current_status}")

                    old_status = ""
                    last_recap_date = ""
                    if os.path.exists(state_file):
                        with open(state_file, "r", encoding="utf-8") as f:
                            lines = [l.strip() for l in f if l.strip()]
                            if len(lines) >= 1:
                                old_status = lines[0]
                            if len(lines) >= 2:
                                last_recap_date = lines[1]

                    is_retiring = user.get("retire_after_next_briefing", False)

                    # Case 1: Status changed -> Priority Alert + Screenshot
                    if current_status != old_status:
                        retire_flag = "\nRETIRED\n" if is_retiring else "\n"
                        with open(state_file, "w", encoding="utf-8") as f:
                            f.write(f"{current_status}\n{today_pkt}{retire_flag}")

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

                        if is_retiring:
                            msg += f"\n\n{FAREWELL_MESSAGE}"

                        send_alert(msg, user["chat_id"])
                        send_photo(screenshot_file, f"Protocol shifted: {current_status}", user["chat_id"])
                        print(f"Priority alert dispatched to {user['name']}{' (FINAL - RETIRED)' if is_retiring else ''}.")

                    # Case 2: First run of calendar day -> Briefing or Standalone Farewell
                    elif today_pkt != last_recap_date:
                        retire_flag = "\nRETIRED\n" if is_retiring else "\n"
                        with open(state_file, "w", encoding="utf-8") as f:
                            f.write(f"{current_status}\n{today_pkt}{retire_flag}")

                        # If retiring and status unchanged, send ONLY the farewell dialogue
                        if is_retiring:
                            recap_msg = FAREWELL_MESSAGE
                        else:
                            quote = random.choice(DAILY_QUOTES)
                            recap_msg = f"📊 *{current_status}* (Unchanged)\n\n_{quote}_"

                        send_alert(recap_msg, user["chat_id"])
                        print(f"Daily briefing dispatched to {user['name']}{' (FINAL - RETIRED)' if is_retiring else ''}.")

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
