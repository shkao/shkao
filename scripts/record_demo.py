"""Record a phone-sized walkthrough for a profile demo WebP.

Copy this file per project: change the URL and the tap/scroll choreography.
Keep VIEWPORT at the same aspect ratio as the frame's video pane (VW:VH in
frame.env) or compose_demo.sh will stretch the recording.
"""
from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 390, "height": 767}

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(
        viewport=VIEWPORT,
        is_mobile=True, has_touch=True,
        record_video_dir="video",
        record_video_size=VIEWPORT,
    )
    page = ctx.new_page()

    def scroll(times, dy, pause):
        for _ in range(times):
            page.mouse.wheel(0, dy)
            page.wait_for_timeout(pause)

    # Events
    page.goto("https://gentropy.vercel.app/en", wait_until="networkidle")
    page.wait_for_timeout(4000)   # linger on the countdown and the list
    page.locator('[aria-label^="Save: "]').first.click()
    page.wait_for_timeout(1800)   # bookmark fills in
    page.get_by_role("button", name="Live jazz").click()
    page.wait_for_timeout(2500)   # the jazz gig guide, night by night
    scroll(2, 380, 1300)
    page.get_by_role("button", name="Gallery", exact=True).click()
    page.wait_for_timeout(3000)

    # Map
    page.get_by_text("Map", exact=True).last.click()
    page.wait_for_timeout(9000)
    page.mouse.move(195, 420)
    page.mouse.down()
    page.mouse.move(150, 330, steps=20)
    page.mouse.up()
    page.wait_for_timeout(1500)
    page.get_by_role("button", name="Toilets").click()
    page.wait_for_timeout(2200)
    page.get_by_role("button", name="Water points").click()
    page.wait_for_timeout(2800)

    # Plans: the event saved above shows up under My events
    page.get_by_text("Plans", exact=True).last.click()
    page.wait_for_timeout(4000)

    # News
    page.get_by_text("News", exact=True).last.click()
    page.wait_for_timeout(3500)
    scroll(2, 420, 1300)
    page.wait_for_timeout(1500)

    ctx.close()
    browser.close()
print("recorded")
