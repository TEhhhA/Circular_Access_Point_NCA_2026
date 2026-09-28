from playwright.sync_api import sync_playwright
import time
AP_IP = "192.168.1.1"
USERNAME = "ubnt"
PASSWORD = "ubnt"
CLIENT_MAC = "80:c0:1e:54:55:1a"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f"http://{AP_IP}")
    
    # login
    page.fill("#Username", USERNAME)
    page.fill("#Password", PASSWORD)
    page.click('[name="login"]')
    page.wait_for_selector(".navigation_item_device_details", timeout=10000)
    page.click('.navigation_item_device_details')
    page.wait_for_selector("#dd_wireless", timeout=10000)
    page.click('#dd_wireless')
    row_selector = f'tr:has(td:text("{CLIENT_MAC}"))'
    page.wait_for_selector(row_selector, timeout=20000)
    rssi_text = page.locator(f'{row_selector} td:nth-child(3)').inner_text()
    

    # Remove 'dBm', strip spaces, replace '/' with space
    parts = [p for p in rssi_text.replace('dBm', '').split() if p != '/']
    clean_rssi = ','.join(parts)

    print(clean_rssi)  # Output: -43 -27
