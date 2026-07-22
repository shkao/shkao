from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(
        viewport={"width": 390, "height": 767},
        is_mobile=True, has_touch=True,
        record_video_dir="video",
        record_video_size={"width": 390, "height": 767},
    )
    page = ctx.new_page()

    # Now
    page.goto("https://gentropy.vercel.app/en", wait_until="networkidle")
    page.wait_for_timeout(5000)   # linger on the Your Thing card
    try:
        page.get_by_text("Live music").first.click(timeout=5000)
    except Exception:
        pass
    page.wait_for_timeout(3000)   # card collapses, feed re-ranks
    for _ in range(3):
        page.mouse.wheel(0, 420)
        page.wait_for_timeout(1400)
    page.wait_for_timeout(1500)

    # Explore
    page.get_by_text("Explore", exact=True).last.click()
    page.wait_for_timeout(3500)
    for _ in range(2):
        page.mouse.wheel(0, 450)
        page.wait_for_timeout(1100)
    page.wait_for_timeout(800)

    # Map
    page.get_by_text("Map", exact=True).last.click()
    page.wait_for_timeout(9000)
    page.mouse.move(195, 480)
    page.mouse.down()
    page.mouse.move(150, 380, steps=20)
    page.mouse.up()
    page.wait_for_timeout(1500)

    # amenity layers: toilets, then water points
    page.locator('[aria-label="Toilets"]').click()
    page.wait_for_timeout(2200)
    page.locator('[aria-label="Water points"]').click()
    page.wait_for_timeout(2800)

    # Plans
    page.get_by_text("Plans", exact=True).last.click()
    page.wait_for_timeout(4000)

    ctx.close()
    browser.close()
print("recorded")
