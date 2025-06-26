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

# === Gestion de la date de récupération ===
now = datetime.utcnow() + timedelta(hours=2)  # Heure Paris
today_weekday = now.weekday()  # 0 = lundi ... 6 = dimanche

if today_weekday == 6:  # Dimanche
    target_date = now - timedelta(days=1)  # Samedi
    download_date = now - timedelta(days=2)  # Vendredi
    weekend_mode = True
elif today_weekday == 0:  # Lundi
    target_date = now  # Lundi
    download_date = now - timedelta(days=3)  # Vendredi
    weekend_mode = True
else:
    target_date = now - timedelta(days=1)  # Hier
    download_date = target_date
    weekend_mode = False

target_str = target_date.strftime("%Y-%m-%d")
download_str = download_date.strftime("%Y-%m-%d")

if weekend_mode:
    print(f"📆 Mode week-end activé → données du vendredi ({download_str}) enregistrées sous {target_str}")
else:
    print(f"📆 Mode semaine → données récupérées pour {target_str}")

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

# === Utilitaires ===
def fetch_html_with_date(url, path, date_str):
    driver = setup_driver()
    driver.set_page_load_timeout(60)
    try:
        print(f"🌐 Accès à {url}")
        driver.get(url)
        time.sleep(7)

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"🔍 {len(iframes)} iframe(s) détectée(s), switch vers la première.")
                driver.switch_to.frame(iframes[0])
        except:
            print("ℹ️ Pas d'iframe trouvée, on reste sur le document principal.")

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

        time.sleep(10)

        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ HTML sauvegardé : {path}")

    except Exception as e:
        print("❌ Erreur : ", e)
        with open("debug_failed_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        try:
            driver.save_screenshot("debug_failed_screenshot.png")
        except:
            pass
        raise
    finally:
        driver.quit()

# === Chemins des fichiers HTML
gaz_html = f"archives/html_gaz/eex_gaz_{target_str}.html"
co2_html = f"archives/html_co2/eex_co2_{target_str}.html"

# === Télécharger HTML si non existants
if not os.path.exists(gaz_html):
    fetch_html_with_date("https://www.eex.com/en/market-data/market-data-hub/natural-gas/spot", gaz_html, download_str)

if not os.path.exists(co2_html):
    fetch_html_with_date("https://www.eex.com/en/market-data/market-data-hub/environmentals/spot", co2_html, download_str)

# === Extraction Gaz
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
        "Date": target_str,
        "Bid": parsed_values[0],
        "Ask": parsed_values[1],
        "Last": parsed_values[2],
    })
else:
    gaz_data.append({
        "Date": target_str,
        "Bid": "-", "Ask": "-", "Last": "-",
    })
df_gaz = pd.DataFrame(gaz_data)

# === Extraction CO2
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
    "Date": target_str,
    "Last Price": last_price,
})
df_co2 = pd.DataFrame(co2_data)

# === Export Excel
excel_file = "data/gaz_co2_data.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl", mode='w') as writer:
    df_gaz.to_excel(writer, sheet_name="Gaz", index=False)
    df_co2.to_excel(writer, sheet_name="CO2", index=False)

print("✅ Données Gaz & CO2 récupérées et enregistrées.")
