import os
import glob
import re
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

# === Fichier de sortie Excel ===
os.makedirs("data", exist_ok=True)
excel_file = "data/epexspot_prices.xlsx"

# === Helper : Fonction pour récupérer la date à partir du nom du fichier ===
def extract_date(filename, prefix):
    match = re.search(fr"{prefix}_(\d{{4}}-\d{{2}}-\d{{2}})", filename)
    return match.group(1) if match else None

# === Étape 1 : Feuille "Prix Spot" (électricité) ===
elec_files = sorted(glob.glob("archives/html/epex_FR_*.html"), key=os.path.getmtime)

# On conserve uniquement le fichier le plus récent pour chaque date
elec_latest = {}
for path in elec_files:
    date_str = extract_date(path, "epex_FR")
    if not date_str:
        continue
    elec_latest[date_str] = path  # Remplace si déjà vu = on garde le plus récent

price_data = {}
for delivery_date, html_file in sorted(elec_latest.items()):
    date_obj = datetime.strptime(delivery_date, "%Y-%m-%d")
    col_label = date_obj.strftime("%d-%b").lower().replace("jan", "janv").replace("may", "mai").replace("oct", "oct.")

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    hour_tags = soup.select("div.fixed-column ul li a")
    hours = [a.text.strip() for a in hour_tags]

    price_tags = soup.select("div.js-table-values table tbody tr td:nth-of-type(4)")
    prices = [float(td.text.strip().replace(",", ".")) for td in price_tags]

    if len(hours) == 24 and len(prices) == 24:
        price_data[col_label] = prices

heure_labels = [f"{str(h).zfill(2)} - {str(h+1).zfill(2)}" for h in range(24)]
df_elec = pd.DataFrame(price_data, index=heure_labels)

# === Étape 2 : Feuille "Gaz" ===
gaz_files = sorted(glob.glob("archives/html_gaz/eex_gaz_*.html"), key=os.path.getmtime)
gaz_latest = {}
for path in gaz_files:
    date_str = extract_date(path, "eex_gaz")
    if date_str:
        gaz_latest[date_str] = path

gaz_data = []
for gaz_date, gaz_file in sorted(gaz_latest.items()):
    with open(gaz_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    peg_row = soup.find("td", string=re.compile("PEG Day-Ahead", re.I))
    if not peg_row:
        continue

    row = peg_row.find_parent("tr")
    values = row.find_all("td")[1:4]
    parsed_values = [float(td.text.strip().replace(",", ".")) if td.text.strip() else "-" for td in values]

    gaz_data.append({
        "Date": gaz_date,
        "Bid": parsed_values[0],
        "Ask": parsed_values[1],
        "Last": parsed_values[2]
    })

df_gaz = pd.DataFrame(gaz_data).sort_values("Date") if gaz_data else pd.DataFrame([{
    "Date": datetime.today().strftime("%Y-%m-%d"),
    "Bid": "-", "Ask": "-", "Last": "-"
}])

# === Étape 3 : Feuille "CO2" ===
co2_files = sorted(glob.glob("archives/html_co2/eex_co2_*.html"), key=os.path.getmtime)
co2_latest = {}
for path in co2_files:
    date_str = extract_date(path, "eex_co2")
    if date_str:
        co2_latest[date_str] = path

co2_data = []
for co2_date, co2_file in sorted(co2_latest.items()):
    with open(co2_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    last_price_tag = soup.find("th", string=re.compile("Last Price", re.I))
    td = last_price_tag.find_next("td") if last_price_tag else None
    last_price = float(td.text.strip().replace(",", ".")) if td and td.text.strip() else "-"

    co2_data.append({
        "Date": co2_date,
        "Last Price": last_price
    })

df_co2 = pd.DataFrame(co2_data).sort_values("Date") if co2_data else pd.DataFrame([{
    "Date": datetime.today().strftime("%Y-%m-%d"),
    "Last Price": "-"
}])

# === Écriture dans l'Excel final ===
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df_elec.to_excel(writer, sheet_name="Prix Spot", index_label="Heure")
    df_gaz.to_excel(writer, sheet_name="Gaz", index=False)
    df_co2.to_excel(writer, sheet_name="CO2", index=False)

print(f"✅ Fichier Excel mis à jour avec électricité, gaz et CO2 : {excel_file}")
