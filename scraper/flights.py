from playwright.sync_api import sync_playwright
from datetime import datetime
import pandas as pd
from pathlib import Path

# ---------- Parametrai ----------
TARGET_DATE = "2025-09-04"
URL = (
    f"https://www.google.com/travel/flights?hl=en"
    f"&q=Flights%20from%20VNO%20to%20ISB%20on%20{TARGET_DATE}"
)

BASE_DIR = Path(__file__).parent        # = scraper/
SS_PATH  = BASE_DIR / "screenshot.png"
CSV_PATH = Path("data/flights.csv")

# ---------- Aplankų kūrimas ----------
BASE_DIR.mkdir(exist_ok=True, parents=True)
CSV_PATH.parent.mkdir(exist_ok=True, parents=True)

def scrape() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(10000)  # 10 s laukiam

        rows = page.query_selector_all('div[role="listitem"]')
        print(f"🔍 Rasta {len(rows)} kortelių")

        offers = []
        for row in rows[:10]:
            price_el   = row.query_selector('[data-test-id="offer-price"]')
            airline_el = row.query_selector('[data-test-id="airline-name"]')
            times      = row.query_selector_all('[data-test-id="departure-time"]')

            if not price_el or not airline_el or len(times) < 2:
                continue

            price_text = price_el.inner_text()
            price = int("".join(filter(str.isdigit, price_text)))
            currency = price_text.replace(str(price), "").strip()

            offers.append(
                dict(
                    date_checked=datetime.utcnow().strftime("%Y-%m-%d"),
                    departure_date=TARGET_DATE,
                    from_="VNO",
                    to="ISB",
                    price=price,
                    currency=currency,
                    airline=airline_el.inner_text(),
                    departure_time=times[0].inner_text(),
                    arrival_time=times[1].inner_text(),
                )
            )

        # -------- Screenshot --------
        try:
            page.screenshot(path=str(SS_PATH), full_page=True)
            print("📸 Screenshot išsaugotas.")
        except Exception as e:
            print(f"⚠️ Screenshot nepavyko: {e}")

        browser.close()

    # -------- CSV --------
    if not offers:
        print("❌ Offer'ų nerasta. Paliekam tik antraštes.")
        if not CSV_PATH.exists():
            pd.DataFrame(columns=[
                "date_checked","departure_date","from","to","price",
                "currency","airline","departure_time","arrival_time"
            ]).to_csv(CSV_PATH, index=False)
        return

    pd.DataFrame(sorted(offers, key=lambda x: x["price"])[:3]) \
      .to_csv(CSV_PATH, mode="a", header=not CSV_PATH.exists(), index=False)
    print("💾 CSV atnaujintas.")

if __name__ == "__main__":
    scrape()
