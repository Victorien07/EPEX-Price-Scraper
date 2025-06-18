import os
import re
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === Dates ===
now = datetime.utcnow() + timedelta(hours=2)  # UTC->Paris
yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

# === Dossiers ===
os.makedirs("archives/html_gaz", exist_ok=True)
os.makedirs("archives/html_co2", exist_ok=True)
os.makedirs("data", exist_ok=True)

# === Setup Selenium (Headless) ===
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# === Utilitaires pour cliquer et changer la date ===
def fetch_html_with_date(url, path, date_str):
    driver = setup_driver()
    driver.get(url)
    time.sleep(5)  # Donne du temps au JS

    try:
        # Passage à l'iframe si présente
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"🔍 Nombre d'iframes détectées : {len(iframes)}")
        driver.switch_to.frame(iframes[0])  # Tester la première iframe

        print("⏳ Attente input date...")
        date_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.eex-date-picker__input"))
        )
        date_input.clear()
        date_input.send_keys(date_str)
        date_input.send_keys(Keys.ENTER)
        print("✅ Date envoyée.")

        time.sleep(8)

        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ Page sauvegardée dans {path}")

    except Exception as e:
        with open("debug_failed_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("🛠 HTML sauvegardé pour debug: debug_failed_page.html")
        print("❌ Erreur durant fetch_html_with_date :", e)
        raise
    finally:
        driver.quit()




# === Télécharger et extraire Gaz (J–1) ===
gaz_html = f"archives/html_gaz/eex_gaz_{yesterday}.html"
if not os.path.exists(gaz_html):
    fetch_html_with_date("https://www.eex.com/en/market-data/market-data-hub/natural-gas/spot", gaz_html, yesterday)

gaz_data = []
with open(gaz_html, encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")
peg_row = soup.find("td", string=re.compile("PEG Day Ahead", re.I))
if peg_row:
    row = peg_row.find_parent("tr")
    values = row.find_all("td")[1:4]
    parsed_values = []
    for td in values:
        txt = td.text.strip()
        try:
            val = float(txt.replace(",", "."))
        except:
            val = "-"
        parsed_values.append(val)
    gaz_data.append({
        "Date": yesterday,
        "Bid": parsed_values[0],
        "Ask": parsed_values[1],
        "Last": parsed_values[2],
    })
else:
    gaz_data.append({
        "Date": yesterday,
        "Bid": "-", "Ask": "-", "Last": "-",
    })
df_gaz = pd.DataFrame(gaz_data)

# === Télécharger et extraire CO2 (J–1) ===
co2_html = f"archives/html_co2/eex_co2_{yesterday}.html"
if not os.path.exists(co2_html):
    fetch_html_with_date("https://www.eex.com/en/market-data/market-data-hub/environmentals/spot", co2_html, yesterday)

co2_data = []
with open(co2_html, encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")
last_price_tag = soup.find("th", string=re.compile("Last Price", re.I))
if last_price_tag:
    td = last_price_tag.find_next("td")
    try:
        last_price = float(td.text.strip().replace(",", "."))
    except:
        last_price = "-"
else:
    last_price = "-"
co2_data.append({
    "Date": yesterday,
    "Last Price": last_price,
})
df_co2 = pd.DataFrame(co2_data)

# === Export Excel ===
excel_file = "data/gaz_co2_data.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df_gaz.to_excel(writer, sheet_name="Gaz", index=False)
    df_co2.to_excel(writer, sheet_name="CO2", index=False)

print("✅ Données Gaz & CO2 récupérées et enregistrées.")

