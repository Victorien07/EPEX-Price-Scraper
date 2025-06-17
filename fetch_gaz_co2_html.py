import os, re, glob, requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd

# === Préparation des dates ===
today = datetime.utcnow() + timedelta(hours=2)  # UTC→Paris
trading = today.strftime("%Y-%m-%d")
delivery = (today + timedelta(days=1)).strftime("%Y-%m-%d")

# === Télécharger page ELECTRICITÉ si pas déjà ===
os.makedirs("archives/html", exist_ok=True)
elec_html = f"archives/html/epex_FR_{delivery}.html"
url = (f"https://www.epexspot.com/en/market-results?"
       f"market_area=FR&auction=MRC&trading_date={trading}"
       f"&delivery_date={delivery}&modality=Auction"
       "&sub_modality=DayAhead&data_mode=table")
if not os.path.exists(elec_html):
    r = requests.get(url, timeout=20)
    with open(elec_html, "w", encoding="utf-8") as f:
        f.write(r.text)

# === Fonction d'extraction heure par heure ===
def extract_elec(html_file):
    soup = BeautifulSoup(open(html_file, encoding="utf-8"), "html.parser")
    hours = [f"{str(h).zfill(2)} - {str(h+1).zfill(2)}" for h in range(24)]
    price_tags = soup.select("table.market-result__table tbody tr td:nth-of-type(2)")
    if len(price_tags) == 24:
        values = [float(td.text.replace(",", ".")) for td in price_tags]
    else:
        values = ["-"] * 24
    return pd.DataFrame([values], index=[delivery], columns=hours).T

# === Gaz & CO₂ comme avant (extraits des HTML existants) ===
# [Ton code Gaz et CO2 ici, non modifié...]

# === Génère Excel ===
df_elec = extract_elec(elec_html)
# ensuite df_gaz, df_co2

with pd.ExcelWriter("data/epexspot_prices.xlsx", engine="openpyxl") as writer:
    df_elec.to_excel(writer, sheet_name="Prix Spot")
    df_gaz.to_excel(writer, sheet_name="Gaz", index=False)
    df_co2.to_excel(writer, sheet_name="CO2", index=False)
