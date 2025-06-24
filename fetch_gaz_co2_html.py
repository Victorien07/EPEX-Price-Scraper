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
    driver.set_page_load_timeout(60)

    try:
        print(f"🌐 Accès à {url}")
        driver.get(url)
        time.sleep(7)  # Laisse le JS charger (page très lourde)

        # Essayons de passer dans une iframe si présente, sinon on reste sur main document
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"🔍 {len(iframes)} iframe(s) détectée(s), switch vers la première.")
                driver.switch_to.frame(iframes[0])
        except:
            print("ℹ️ Pas d'iframe trouvée, on reste sur le document principal.")

        # Attente explicite du champ de date
        print("⏳ Recherche du champ date...")
        date_input = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input.eex-date-picker__input"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", date_input)
        time.sleep(1)

        print(f"📅 Saisie de la date : {date_str}")
        date_input.clear()
        date_input.send_keys(date_str)
        date_input.send_keys(Keys.ENTER)

        time.sleep(10)  # Laisse les données se rafraîchir

        # Sauvegarde HTML
        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ HTML sauvegardé : {path}")

    except Exception as e:
        print("❌ Erreur : ", e)

        # Sauvegarde page HTML
        with open("debug_failed_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("🛠 HTML sauvegardé pour debug: debug_failed_page.html")

        # Screenshot pour analyse
        screenshot_path = "debug_failed_screenshot.png"
        try:
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot sauvegardé : {screenshot_path}")
        except Exception as screen_error:
            print("⚠️ Échec de la capture écran :", screen_error)

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

