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
        page.wait_for_timeout(10000)           # 10 s laukiam kol viskas kraunasi

        # ---- DEBUG: kiek kortelių radome? ----
        rows = page.query_selector_all('div[role="listitem"]')[:10]
        print(f"🔍 Rasta {len(rows)} kortelių (skrydžių blokų)")

        offers = []
        for i, row in enumerate(rows):
            print(f"➡️ Tikrinu kortelę #{i+1}")
            try:
                price_el = row.query_selector('[data-test-id="offer-price"]')
                airline_el = row.query_selector('[data-test-id="airline-name"]')
                times = row.query_selector_all('[data-test-id="departure-time"]')

                if not price_el or not airline_el or len(times) < 2:
                    print("   ⚠️ Nepavyko rasti visų laukų – praleidžiu")
                    continue

                price_text = price_el.inner_text()
                price = int("".join(filter(str.isdigit, price_text)))
                currency = price_text.replace(str(price), "").strip()
                dep_time, arr_time = (t.inner_text() for t in times[:2])
                airline = airline_el.inner_text()

                print(f"   ✅ Kaina: {price_text}, Oro linija: {airline}")

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
            except Exception as e:
                print(f"   ❌ Klaida: {e}")
                continue

        # ---- Išrikiuojame ir paimame tik 3 pigiausius ----
        offers = sorted(offers, key=lambda x: x["price"])[:3]

        if not offers:
            print("❌ Nerasta nė vieno tinkamo pasiūlymo – darau ekrano nuotrauką.")
            page.screenshot(path="screenshot.png", full_page=True)
        else:
            print(f"✅ Įrašau {len(offers)} pigiausius pasiūlymus į CSV.")
            page.screenshot(path="scraper/screenshot.png", full_page=True)


        browser.close()

    # ---- CSV įrašymas ----
    df_new = pd.DataFrame(offers)
    if CSV_PATH.exists():
        df_new.to_csv(CSV_PATH, mode="a", header=False, index=False)
    else:
        df_new.to_csv(CSV_PATH, index=False)


if __name__ == "__main__":
    scrape()
