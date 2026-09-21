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
# 30 ICONIC DESI CINEMA & MEME BRIEFINGS (First run of every calendar day)
# ==============================================================================
DAILY_QUOTES = [
    # 1. Gangs of Wasseypur (Ramadhir Singh)
    "Beta, tumse na ho payega... Moscow ka babu chai pee raha hai aur tum yahan screen ghoor rahe ho. Status bilkul nahi hila, phone jeb mein daalo.",

    # 2. Mirzapur (Kaleen Bhaiya)
    "Rest kijiye, varna rest in peace ho jaoge. Telemetry bilkul static hai aaj. Phone side pe rakho aur aaraam se apna din guzaro.",

    # 3. Hera Pheri (Baburao Apte)
    "Utha le re baba, utha le... arey status ko nahi, is phone ko side pe utha ke rakh! Ek byte nahi badla Moscow ke server pe.",

    # 4. Munna Bhai M.B.B.S. (Circuit)
    "Bhai ne bola status unchanged hai, matlab unchanged hai! Tension nahi lene ka mamu, apun kal subah direct ping karega.",

    # 5. Welcome (Uday Shetty)
    "Control, Majnu, control! Subah-subah itna hyper hone ki zaroorat nahi hai. Moscow abhi so raha hai, screen lock karo aur kaam pe lago.",

    # 6. 3 Idiots (Rancho)
    "Arey shanti, dost... portal koi rocket science nahi chala raha. Status wahi ka wahi hai. 'All is well' bolo aur phone pocket mein daalo.",

    # 7. Sholay (Gabbar Singh)
    "Kitne updates the? Ek bhi nahi! Portal bilkul sunsaan pada hai. So jao beta, jab tak Moscow file nahi kholta tab tak notifications band.",

    # 8. Sacred Games (Ganesh Gaitonde)
    "Kabhi kabhi lagta hai apun hi idhar wait kar raha hai, Moscow ko koi parwah hi nahi. Telemetry bilkul silent hai aaj, chill maaro.",

    # 9. Gangs of Wasseypur (Sardar Khan)
    "Baap ka, dada ka, bhai ka... sabka badla lega re tera tracker, lekin tab jab Moscow ka status hilega. Filhaal zero movement hai.",

    # 10. Phir Hera Pheri (Raju)
    "25 din mein status double? Aisa koi scheme nahi hai Russian Ministry mein. File bilkul freeze hai, phone rakh do chup chaap.",

    # 11. Andaz Apna Apna (Crime Master Gogo)
    "Aankhein nikaal ke gotiyan khelunga agar bar bar refresh kiya! Status wahi hai, khali hath ja rahe ho aaj. Phone lock karo.",

    # 12. Mirzapur (Guddu Pandit)
    "Shuru majboori mein kiye the, ab maza tab aayega jab Stage 2 aayega. Par aaj nahi aa raha. Shanti se baitho.",

    # 13. Deewar (Vijay)
    "Aaj mere paas automated script hai, GitHub Actions hai, Playwright hai... par status wahi ka wahi hai. Pocket the phone.",

    # 14. Hera Pheri (Kachra Seth)
    "Dedh sau rupiya dega... par Moscow ka babu file ko haath bhi nahi lagayega. Zero progress detected, band karo Telegram.",

    # 15. DDLJ (Bauji)
    "Jaa Simran jaa, jee le apni zindagi... kyunki Russian portal to hilne se raha. Status unchanged hai, shaam tak aish kar.",

    # 16. Chup Chup Ke (Bandya)
    "Mujhe sab aata hai, main sab kar sakta hoon... bas Moscow ka server nahi chala sakta. Shanti se phone rakh de bhai.",

    # 17. Sarabhai vs Sarabhai (Maya Sarabhai)
    "Subah-subah bar-bar screen refresh karna is categorically middle class! Status freeze hai, chai piyo aur class dikhao.",

    # 18. Munna Bhai M.B.B.S. (Dr. Asthana)
    "Laughter is the best medicine... par is portal ki speed dekh ke hasi bhi nahi aa rahi. Static telemetry. Silent mode on.",

    # 19. Don (SRK)
    "Status update ko pakadna mushkil hi nahi, namumkin hai... filhaal ke liye. Aaj ka scorecard zero hai, kal milte hain.",

    # 20. Welcome (Majnu Bhai)
    "Yeh meri live-drawn painting nahi hai jo badal jaye, Russian database hai, ek inch nahi hil raha! Screen band karo.",

    # 21. Om Shanti Om (Om Kapoor)
    "Picture abhi baaki hai mere dost... lekin aaj ka show bilkul static hai. Low-power mode engaged, go do some real work.",

    # 22. Sholay (Thakur)
    "Yeh haath mujhe de de Gabbar... taaki main is phone ko lock karke side pe phenk sakun! Ek bhi status transition nahi hua.",

    # 23. Singham (Bajirao Singham)
    "Aata maajhi satakli bolne se dossier aage nahi badhega. Moscow apne hisaab se chalega. Screen off karo aur kaam dhoondo.",

    # 24. Gangs of Wasseypur (Definite)
    "Hamaar naam hai Definite, aur definite baat yeh hai ki file bilkul nahi hili. Aaj ka quota khatam, radio silence shuru.",

    # 25. Sacred Games (Guruji)
    "Aham Brahmasmi... par Moscow ka portal alag hi maya mein phansa hua hai. Kripya dhyan lagayein aur refresh karna chhod dein.",

    # 26. Lagaan (Bhuvan)
    "Dugna lagaan nahi maang raha Moscow, bas dugna time le raha hai! Dossier static hai, field pe jao aur kaam pe dhyan do.",

    # 27. PK (PK)
    "Lul ho gaya! Moscow portal pe lagta hai koi wrong number lag gaya hai. Status hil hi nahi raha. Phone jeb mein daalo bhaiya.",

    # 28. Baahubali (Katappa)
    "Maine status nahi badla... kyunki Moscow ne hi nahi badla! Telemetry freeze hai, talwaar aur phone dono aaram se rakh do.",

    # 29. Mirzapur (Munna Bhaiya)
    "Hum karte hain prabandh... par babu log file ko chhoo bhi nahi rahe. Aukaat mein reh ke phone pocket mein rakho, zero delta hai.",

    # 30. Hera Pheri (Baburao - Part 2)
    "Khopdi tod saale ka... arey Russian server ka nahi re, apna dimaag thanda rakh. Status same hai, mute pe ja raha hoon."
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


def scrape_applicant(browser, user):
    """Scrapes one applicant with an isolated browser context and dynamic polling."""
    # Fresh isolated context for every search (eliminates cookie/session bleed)
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

        # Dynamic Polling: Check DOM every 2s up to 26s (prevents early cutoff if Russian server is slow)
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
                print(f"=== Scraping for {user['name']} ({user['reg_number']}) ===")

                # 10s cooldown before Imran so the portal doesn't throttle consecutive requests
                if index > 0:
                    time.sleep(10)

                # Attempt 1
                current_status, screenshot_file = scrape_applicant(browser, user)

                # Auto-retry once if status missed due to transient network lag
                if not current_status:
                    print(f"⚠️ Initial query missed for {user['name']}. Retrying in 8 seconds...")
                    time.sleep(8)
                    current_status, screenshot_file = scrape_applicant(browser, user)

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
