from playwright.sync_api import sync_playwright
from datetime import datetime
import pandas as pd
from pathlib import Path
import os

# --- Parametrai --------------------------------------------------------------
TARGET_DATE = "2025-09-04"
URL = (
    f"https://www.google.com/travel/flights?hl=en"
    f"&q=Flights%20from%20VNO%20to%20ISB%20on%20{TARGET_DATE}"
)

# --- Kelių nustatymai --------------------------------------------------------
BASE_DIR = Path(__file__).parent           # = scraper/
CSV_PATH = Path("data/flights.csv")        # duomenų failas
SS_PATH = BASE_DIR / "screenshot.png"      # ekrano nuotrauka

# Užtikriname, kad aplankai egzistuoja
CSV_PATH.parent.mkdir(exist_ok=True, parents=True)
BASE_DIR.mkdir(exist_ok=True, parents=True)

def scrape() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(10000)  # 10 s laukiam kol JS užsikrauna

        rows = page.query_selector_all('div[role="listitem"]')
        print(f"🔍 Rasta {len(rows)} kortelių (skrydžių blokų)")

        offers = []
        for i, row in enumerate(rows[:10]):
            print(f"➡️ Kortelė #{i+1}")
            try:
                price_el   = row.query_selector('[data-test-id="offer-price"]')
                airline_el = row.query_selector('[data-test-id="airline-name"]')
                times      = row.query_selector_all('[data-test-id="departure-time"]')

                if not price_el or not airline_el or len(times) < 2:
                    print("   ⚠️ Nepilni duomenys – praleidžiu")
                    continue

                price_text = price_el.inner_text()
                price      = int("".join(filter(str.isdigit, price_text)))
                currency   = price_text.replace(str(price), "").strip()
                dep_time, arr_time = (t.inner_text() for t in times[:2])
                airline    = airline_el.inner_text()

                print(f"   ✅ {airline} – {price_text}")

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

        # --- Išsaugom ekrano nuotrauką ---------------------------------------
        try:
            page.screenshot(path=str(SS_PATH), full_page=True)
            print(f"📸 Ekrano nuotrauka išsaugota: {SS_PATH}")
        except Exception as e:
            print(f"⚠️ Nepavyko padaryti screenshot: {e}")

        browser.close()

    # --- CSV įrašymas --------------------------------------------------------
    # Jei nerasta pasiūlymų, įrašome tik antraštes (kad failas nebūtų tuščias)
    if not offers:
        print("❌ Nepavyko gauti skrydžių pasiūlymų.")
        if not CSV_PATH.exists():
            print("📄 Kuriu CSV su antraštėmis.")
            empty_df = pd.DataFrame(
                columns=[
