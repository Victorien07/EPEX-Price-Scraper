import os, re, time
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

now = datetime.utcnow() + timedelta(hours=2)
yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

os.makedirs("archives/html_gaz", exist_ok=True)
os.makedirs("archives/html_co2", exist_ok=True)
os.makedirs("data", exist_ok=True)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # use new mode for better rendering
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def fetch_html_with_date(url, path, date_str, max_wait=60):
    driver = setup_driver()
    print(f"🌐 Accès à {url}")
    driver.get(url)

    try:
        # Attente de l'apparition d'au moins une iframe (chargée dynamiquement)
        print("⏳ Attente iframe dynamique...")
        WebDriverWait(driver, max_wait).until(
            lambda d: len(d.find_elements(By.TAG_NAME, "iframe")) > 0
        )

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"✅ {len(iframes)} iframe(s) détectée(s). Passage à la première.")
        driver.switch_to.frame(iframes[0])

        # Attente que le champ de date apparaisse
        print("⏳ Recherche champ date dans l’iframe...")
        date_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.eex-date-picker__input"))
        )
        print("✅ Champ date détecté.")

        # Scroll et interaction
        driver.execute_script("arguments[0].scrollIntoView();", date_input)
        time.sleep(1)
        date_input.clear()
        date_input.send_keys(date_str)
        date_input.send_keys(Keys.ENTER)
        print(f"📅 Date envoyée : {date_str}")

        # Attente que la page se mette à jour
        time.sleep(10)

        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ HTML sauvegardé dans {path}")

    except Exception as e:
        print(f"❌ Erreur pendant la récupération : {e}")
        with open("debug_failed_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot("debug_failed_screenshot.png")
        print("📸 Screenshot sauvegardé pour analyse.")
        raise

    finally:
        driver.quit()


# === Téléchargement GAZ
gaz_html = f"archives/html_gaz/eex_gaz_{yesterday}.html"
if not os.path.exists(gaz_html):
    fetch_html_with_date("https://www.eex.com/en/market-data/market-data-hub/natural-gas/spot", gaz_html, yesterday)

# === Téléchargement CO2
co2_html = f"archives/html_co2/eex_co2_{yesterday}.html"
if not os.path.exists(co2_html):
    fetch_html_with_date("https://www.eex.com/en/market-data/market-data-hub/environmentals/spot", co2_html, yesterday)

# === Extraction GAZ
gaz_data = []
with open(gaz_html, encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")
peg_row = soup.find("td", string=re.compile("PEG Day Ahead", re.I))
if peg_row:
    row = peg_row.find_parent("tr")
    values = row.find_all("td")[1:4]
    gaz_data.append({
        "Date": yesterday,
        "Bid": float(values[0].text.strip().replace(",", ".")) if values[0].text.strip() else "-",
        "Ask": float(values[1].text.strip().replace(",", ".")) if values[1].text.strip() else "-",
        "Last": float(values[2].text.strip().replace(",", ".")) if values[2].text.strip() else "-"
    })
else:
    gaz_data.append({"Date": yesterday, "Bid": "-", "Ask": "-", "Last": "-"})
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
co2_data.append({"Date": yesterday, "Last Price": last_price})
df_co2 = pd.DataFrame(co2_data)

# === Export Excel
excel_file = "data/gaz_co2_data.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df_gaz.to_excel(writer, sheet_name="Gaz", index=False)
    df_co2.to_excel(writer, sheet_name="CO2", index=False)

print("✅ Données Gaz & CO2 récupérées et enregistrées.")
