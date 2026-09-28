from playwright.sync_api import sync_playwright
import time
import sys
AP_IP = "192.168.1.1"
USERNAME = "ubnt"
PASSWORD = "ubnt"
CLIENT_MAC = "80:c0:1e:54:55:1a"

#Output power: 20dBm 17dBm 14dBm 11dBm 8dBm

trans = {"20": "100",
    "17" : "50",
    "14" : "25",
    "11" : "12",
    "8" : "6"
}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f"http://{AP_IP}")
    
    # login
    page.fill("#Username", USERNAME)
    page.fill("#Password", PASSWORD)
    page.click('[name="login"]')
    page.wait_for_selector(".navigation_item_settings", timeout=10000)
    page.click('.navigation_item_settings')
    page.wait_for_selector(".tabs__item", timeout=10000)
    page.locator('.tabs__item', has_text='Wireless').click()
    page.wait_for_selector("#f2_txPower", timeout=10000)
    page.locator("#f2_txPower").select_option(value=trans[sys.argv[1]])
    button = page.locator("#changes_apply_button")
    if button.is_enabled():
        button.click()
