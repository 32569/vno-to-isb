from playwright.sync_api import sync_playwright
from datetime import datetime
import pandas as pd
from pathlib import Path

TARGET_DATE = "2025-09-04"
URL = (
    f"https://www.google.com/travel/flights?hl=en"
    f"&q=Flights%20from%20VNO%20to%20ISB%20on%20{TARGET_DATE}"
)

CSV_PATH = Path("data/flights.csv")
CSV_PATH.parent.mkdir(exist_ok=True)

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(10000)  # 10 sekundžių laukia kol viskas užsikrauna
        rows = page.query_selector_all('div[role="listitem"]')[:10]
        offers = []
        for row in rows:
            try:
                price_text = row.query_selector('[data-test-id="offer-price"]').inner_text()
                price = int("".join(filter(str.isdigit, price_text)))
                currency = price_text.replace(str(price), "").strip()
                airline = row.query_selector('[data-test-id="airline-name"]').inner_text()
                times = row.query_selector_all('[data-test-id="departure-time"]')
                dep_time, arr_time = (t.inner_text() for t in times[:2])
                offers.append(
                    dict(
                        date_checked=datetime.utcnow().strftime("%Y-%m-%d"),
                        departure_date=TARGET_DATE,
                        from_="VNO",
                        to="ISB",
                        price=price,
                        currency=currency,
                        airline=airline,
                        departure_time=dep_time,
                        arrival_time=arr_time,
                    )
                )
            except:
                continue
        browser.close()

    offers = sorted(offers, key=lambda x: x["price"])[:3]
    df_new = pd.DataFrame(offers)

    if CSV_PATH.exists():
        df_new.to_csv(CSV_PATH, mode="a", header=False, index=False)
    else:
        df_new.to_csv(CSV_PATH, index=False)

if __name__ == "__main__":
    scrape()
