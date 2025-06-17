# === Setup Selenium (Headless) ===
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# === Télécharger et extraire Gaz (J–1) via Selenium ===
gaz_html = f"archives/html_gaz/eex_gaz_{yesterday}.html"
if not os.path.exists(gaz_html):
    driver = setup_driver()
    driver.get("https://www.eex.com/en/market-data/market-data-hub/natural-gas/spot")
    import time
    time.sleep(8)  # attendre chargement JS
    with open(gaz_html, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    driver.quit()

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

# === Télécharger et extraire CO2 (J–1) via Selenium ===
co2_html = f"archives/html_co2/eex_co2_{yesterday}.html"
if not os.path.exists(co2_html):
    driver = setup_driver()
    driver.get("https://www.eex.com/en/market-data/market-data-hub/environmentals/spot")
    import time
    time.sleep(8)  # attendre chargement JS
    with open(co2_html, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    driver.quit()

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
