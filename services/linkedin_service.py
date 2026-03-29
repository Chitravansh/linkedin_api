import os
import time
import random
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

AUTH_FILE = "auth.json"


# ------------------ Utility ------------------

def human_delay(a=2, b=5):
    time.sleep(random.uniform(a, b))


def type_like_human(page, text):
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.02, 0.08))


# ------------------ Auth ------------------

# def is_logged_in(page):
#     try:
#         print("Checking login status...")
#         page.goto("https://www.linkedin.com/feed/", timeout=60000)
#         page.wait_for_selector("text=Start a post", timeout=5000)
#         return True
#     except:
#         return False


#-----------More reliable login check----------------

def is_logged_in(page):
    try:
        print("🔍 Checking login status...")

        page.goto("https://www.linkedin.com/feed/", timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        # check URL contains linkedin feed
        if "linkedin.com/feed" in page.url:
            print("✅ Feed URL detected")

            # check stable logged-in navbar elements
            nav_checks = [
                "text=Home",
                "text=My Network",
                "text=Me",
                "text=Start a post"
            ]

            for selector in nav_checks:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    print(f"✅ Logged-in element found: {selector}")
                    return True
                except:
                    continue

        print("❌ Session invalid")
        return False

    except Exception as e:
        print(f"⚠️ Login check failed: {e}")
        return False

def login_and_save(context, page):
    print("🔐 Logging in...")

    page.goto("https://www.linkedin.com/login")

    #-------------Navigate to  logion page more reliably----------------
    print("📍 Navigating to login page...")

    page.wait_for_selector("input[name='session_key']", timeout=60000)

    page.fill("input[name='session_key']", EMAIL)
    page.fill("input[name='session_password']", PASSWORD)

    page.click("button[type='submit']")
    page.wait_for_url("https://www.linkedin.com/feed/", timeout=60000)

    time.sleep(5)
    context.storage_state(path=AUTH_FILE)


# ------------------ Core Function ------------------

def run_linkedin_post(group_url, content, image_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        if os.path.exists(AUTH_FILE):
            context = browser.new_context(storage_state=AUTH_FILE)
        else:
            context = browser.new_context()

        page = context.new_page()

        if not is_logged_in(page):
            login_and_save(context, page)

        post_with_image(page, group_url, content, image_path)

        browser.close()

        return {"status": "success"}


# ------------------ Posting ------------------

def post_with_image(page, group_url, content, image_path):
    page.goto(group_url)
    human_delay(4, 7)

    page.mouse.wheel(0, 500)
    human_delay()

    click_start_post(page)
    human_delay()

    type_like_human(page, content)
    human_delay()

    upload_image(page, image_path)
    handle_image_editor(page)

    human_delay(5, 8)

    page.locator("div[role='dialog']").get_by_role("button", name="Post", exact=True).click()

    human_delay(5, 10)


def click_start_post(page):
    try:
        page.get_by_role("button", name="Start a public post").click()
    except:
        try:
            page.locator("button:has-text('Start a')").first.click()
        except:
            page.locator("div[role='button']:has-text('Start')").first.click()


def upload_image(page, image_path):
    modal = page.locator("div[role='dialog']")

    with page.expect_file_chooser() as fc_info:
        modal.get_by_role("button", name="Add media", exact=False).click()

    file_chooser = fc_info.value
    file_chooser.set_files(image_path)


def handle_image_editor(page):
    page.wait_for_selector("button:has-text('Next')", timeout=10000)

    try:
        page.get_by_role("button", name="Next").click()
    except:
        page.locator("button:has-text('Next')").click()

    human_delay(3, 5)


#------------------Repost Service------------------
def run_repost_latest_post(company_posts_url, group_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
        storage_state=AUTH_FILE if os.path.exists(AUTH_FILE) else None,
        permissions=["clipboard-read", "clipboard-write"]
        )

        page = context.new_page()

        if not is_logged_in(page):
            login_and_save(context, page)

        post_link = get_latest_post_link(page,company_posts_url)

        if not post_link:
            return {"status": "error", "message": "No latest post found"}

        post_to_group(page, group_url, post_link)

        browser.close()

        return {"status": "success", "post_link": post_link}


def get_latest_post_link(page, company_posts_url):
    print("🔍 Fetching latest company post...")

    page.goto(company_posts_url, timeout=60000)
    page.wait_for_load_state("domcontentloaded")

    page.wait_for_selector("div.feed-shared-update-v2", timeout=10000)

    posts = page.locator("div.feed-shared-update-v2")
    count = posts.count()

    if count == 0:
        print("❌ No posts found")
        return None

    first_post = posts.nth(0)

    try:
        menu_button = first_post.locator("button[aria-label*='control menu']")
        menu_button.click()

        time.sleep(2)

        page.get_by_role("button", name="Copy link to post").click()

        time.sleep(2)

        post_link = page.evaluate("navigator.clipboard.readText()")

        print(f"✅ Latest Post: {post_link}")

        return post_link

    except Exception as e:
        print(f"❌ Failed to fetch post link: {e}")
        return None


def post_to_group(page, group_url, post_link):
    print(f"📢 Reposting in group: {group_url}")

    page.goto(group_url, timeout=60000)
    human_delay(3, 5)

    click_start_post(page)

    human_delay(2, 3)

    textbox = page.locator("div[role='textbox']").first
    textbox.click()

    textbox.fill(post_link)
    wait_for_link_preview(page)

    human_delay(4, 6)

    page.get_by_role("button", name="Post", exact=True).click()

    print("✅ Reposted successfully")

def wait_for_link_preview(page, timeout=15000):
    print("⏳ Waiting for link preview...")

    preview_selectors = [
        "div.feed-shared-update-v2",
        "div.ember-view a[href*='linkedin.com']",
        "article",
        "div[role='dialog'] img"
    ]

    for selector in preview_selectors:
        try:
            page.wait_for_selector(selector, timeout=timeout)
            print(f'✅ Preview detected {selector}')
            return True
        except:
            continue

    print("⚠️ Preview not detected, proceeding anyway")
    return False