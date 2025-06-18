import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# === Date (hier)
now = datetime.utcnow() + timedelta(hours=2)
yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

# === Dossiers
os.makedirs("archives/html_gaz", exist_ok=True)
os.makedirs("archives/html_co2", exist_ok=True)

# === Setup navigateur headless
def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# === Fonction de téléchargement
def fetch_and_save(url, html_path, label):
    print(f"\n🌐 {label.upper()} — Chargement de {url}")
    driver = setup_driver()
    driver.get(url)
    try:
        # attente et recherche champ date
        time.sleep(5)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            driver.switch_to.frame(iframes[0])
            print(f"➡️ Iframe détectée ({label}), passage réussi")

        # champ date
        date_input = driver.find_element(By.CSS_SELECTOR, "input.eex-date-picker__input")
        date_input.clear()
        date_input.send_keys(yesterday_str)
        date_input.send_keys(Keys.ENTER)

        print(f"⏳ Attente après saisie de la date {yesterday_str}...")
        time.sleep(10)

        # enregistrement HTML
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ {label} — HTML sauvegardé dans {html_path}")

    except Exception as e:
        print(f"❌ Erreur durant {label} : {e}")
        with open(f"debug_failed_{label}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot(f"debug_failed_{label}.png")
        print(f"🛠 Page et capture pour {label} sauvegardées.")

    finally:
        driver.quit()


# === Gaz
gaz_url = "https://www.eex.com/en/market-data/market-data-hub/natural-gas/spot"
gaz_html = f"archives/html_gaz/eex_gaz_{yesterday_str}.html"
if not os.path.exists(gaz_html):
    fetch_and_save(gaz_url, gaz_html, "gaz")

# === CO2
co2_url = "https://www.eex.com/en/market-data/market-data-hub/environmentals/spot"
co2_html = f"archives/html_co2/eex_co2_{yesterday_str}.html"
if not os.path.exists(co2_html):
    fetch_and_save(co2_url, co2_html, "co2")
