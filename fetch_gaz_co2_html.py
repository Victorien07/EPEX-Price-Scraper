import os
import re
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd

# === Dates ===
now = datetime.utcnow() + timedelta(hours=2)  # UTC->Paris
today = now.strftime("%Y-%m-%d")      # Date du jour J (gaz & CO2)
delivery = (now + timedelta(days=1)).strftime("%Y-%m-%d")  # J+1 (élec)

# === Dossiers ===
os.makedirs("archives/html", exist_ok=True)
os.makedirs("archives/html_gaz", exist_ok=True)
os.makedirs("archives/html_co2", exist_ok=True)
os.makedirs("data", exist_ok=True)

# === Téléchargement Électricité (J+1) ===
elec_html = f"archives/html/epex_FR_{delivery}.html"
elec_url = (
    f"https://www.epexspot.com/en/market-results?"
    f"market_area=FR&auction=MRC&trading_date={today}"
    f"&delivery_date={delivery}&modality=Auction"
    "&sub_modality=DayAhead&data_mode=table"
)
if not os.path.exists(elec_html):
    r = requests.get(elec_url, timeout=20)
    with open(elec_html, "w", encoding="utf-8") as f:
        f.write(r.text)

# === Extraction électricité ===
def extract_elec(html_file):
    soup = BeautifulSoup(open(html_file, encoding="utf-8"), "html.parser")
    hours = [f"{str(h).zfill(2)} - {str(h+1).zfill(2)}" for h in range(24)]
    price_tags = soup.select("table.market-result__table tbody tr td:nth-of-type(2)")
    if len(price_tags) == 24:
        try:
            values = [float(td.text.replace(",", ".")) for td in price_tags]
        except Exception:
            values = ["-"] * 24
    else:
        values = ["-"] * 24
    return pd.DataFrame([values], index=[delivery], columns=hours).T

df_elec = extract_elec(elec_html)

# === Télécharger et extraire Gaz (J) ===
gaz_html = f"archives/html_gaz/eex_gaz_{today}.html"
gaz_url = "https://www.eex.com/en/market-data/market-data-hub/natural-gas/spot"
if not os.path.exists(gaz_html):
    r = requests.get(gaz_url, timeout=20)
    with open(gaz_html, "w", encoding="utf-8") as f:
        f.write(r.text)

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
        "Date": today,
        "Bid": parsed_values[0],
        "Ask": parsed_values[1],
        "Last": parsed_values[2],
    })
else:
    gaz_data.append({
        "Date": today,
        "Bid": "-",
        "Ask": "-",
        "Last": "-",
    })
df_gaz = pd.DataFrame(gaz_data)

# === Télécharger et extraire CO2 (J) ===
co2_html = f"archives/html_co2/eex_co2_{today}.html"
co2_url = "https://www.eex.com/en/market-data/market-data-hub/environmentals/spot"
if not os.path.exists(co2_html):
    r = requests.get(co2_url, timeout=20)
    with open(co2_html, "w", encoding="utf-8") as f:
        f.write(r.text)

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
    "Date": today,
    "Last Price": last_price,
})
df_co2 = pd.DataFrame(co2_data)

# === Export Excel ===
excel_file = "data/epexspot_prices.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df_elec.to_excel(writer, sheet_name="Prix Spot", index_label="Heure")
    df_gaz.to_excel(writer, sheet_name="Gaz", index=False)
    df_co2.to_excel(writer, sheet_name="CO2", index=False)

print(f"✅ Excel mis à jour : {excel_file}")
