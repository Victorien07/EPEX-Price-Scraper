import os
import glob
import re
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

# === Fichier de sortie Excel ===
os.makedirs("data", exist_ok=True)
excel_file = "data/epexspot_prices.xlsx"

# === Étape 1 : Feuille "Prix Spot" (électricité) ===
price_data = {}
html_files = sorted(glob.glob("archives/html/epex_FR_*.html"))

for html_file in html_files:
    date_match = re.search(r"epex_FR_(\d{4}-\d{2}-\d{2})", html_file)
    if not date_match:
        continue
    delivery_date = date_match.group(1)
    date_obj = datetime.strptime(delivery_date, "%Y-%m-%d")
    col_label = date_obj.strftime("%d-%b").lower().replace("jan", "janv").replace("may", "mai").replace("oct", "oct.")

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    hour_tags = soup.select("div.fixed-column ul li a")
    hours = [a.text.strip() for a in hour_tags]

    price_tags = soup.select("div.js-table-values table tbody tr td:nth-of-type(4)")
    prices = [float(td.text.strip().replace(",", ".")) for td in price_tags]

    if len(hours) != 24 or len(prices) != 24:
        continue

    price_data[col_label] = prices

# Feuille 1 : électricité
heure_labels = [f"{str(h).zfill(2)} - {str(h+1).zfill(2)}" for h in range(24)]
df_elec = pd.DataFrame(price_data, index=heure_labels)

# === Étape 2 : Feuille "Gaz" ===
gaz_files = sorted(glob.glob("archives/html_gaz/eex_gaz_*.html"))
gaz_data = []

for gaz_file in gaz_files:
    date_match = re.search(r"eex_gaz_(\d{4}-\d{2}-\d{2})", gaz_file)
    gaz_date = date_match.group(1) if date_match else "N/A"

    with open(gaz_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    peg_row = soup.find("td", string=re.compile("PEG Day-Ahead", re.I))
    if not peg_row:
        continue

    row = peg_row.find_parent("tr")
    values = row.find_all("td")[1:4]
    parsed_values = [float(td.text.strip().replace(",", ".")) if td.text.strip() else None for td in values]

    gaz_data.append({
        "Date": gaz_date,
        "Bid": parsed_values[0],
        "Ask": parsed_values[1],
        "Last": parsed_values[2]
    })

if gaz_data:
    df_gaz = pd.DataFrame(gaz_data).sort_values("Date")
else:
    # Si aucune donnée de gaz n'a été trouvée
    today = datetime.today().strftime("%Y-%m-%d")
    df_gaz = pd.DataFrame([{
        "Date": today,
        "Contract": "PEG Day Ahead",
        "Last": "-",
        "High": "-",
        "Low": "-"
    }])


# === Étape 3 : Feuille "CO2" ===
co2_files = sorted(glob.glob("archives/html_co2/eex_co2_*.html"))
co2_data = []

for co2_file in co2_files:
    date_match = re.search(r"eex_co2_(\d{4}-\d{2}-\d{2})", co2_file)
    co2_date = date_match.group(1) if date_match else "N/A"

    with open(co2_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    last_price_tag = soup.find("th", string=re.compile("Last Price", re.I))
    if not last_price_tag:
        continue

    td = last_price_tag.find_next("td")
    last_price = float(td.text.strip().replace(",", ".")) if td and td.text.strip() else None

    co2_data.append({
        "Date": co2_date,
        "Last Price": last_price
    })

if co2_data:
    df_co2 = pd.DataFrame(co2_data).sort_values("Date")
else:
    today = datetime.today().strftime("%Y-%m-%d")
    df_co2 = pd.DataFrame([{
        "Date": today,
        "Last Price": "-"
    }])


# === Écriture de toutes les feuilles dans l'Excel ===
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df_elec.to_excel(writer, sheet_name="Prix Spot", index_label="Heure")
    df_gaz.to_excel(writer, sheet_name="Gaz", index=False)
    df_co2.to_excel(writer, sheet_name="CO2", index=False)

print(f"✅ Fichier Excel mis à jour avec électricité, gaz et CO2 : {excel_file}")
