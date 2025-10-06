import os
import glob
import re
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

# === Préparation ===
os.makedirs("data", exist_ok=True)
excel_file = "data/epexspot_prices.xlsx"

# === Helper : Récupérer date depuis le nom de fichier ===
def extract_date(filename, prefix):
    match = re.search(fr"{prefix}_(\d{{4}}-\d{{2}}-\d{{2}})", filename)
    return match.group(1) if match else None

# === Lecture fichier Excel existant si dispo ===
if os.path.exists(excel_file):
    existing_sheets = pd.read_excel(excel_file, sheet_name=None, index_col=0)
    df_existing_elec = existing_sheets.get("Prix Spot", pd.DataFrame())
    df_existing_gaz = existing_sheets.get("Gaz", pd.DataFrame())
    df_existing_co2 = existing_sheets.get("CO2", pd.DataFrame())
else:
    df_existing_elec = pd.DataFrame()
    df_existing_gaz = pd.DataFrame()
    df_existing_co2 = pd.DataFrame()

# === Électricité ("Prix Spot") ===
elec_files = sorted(glob.glob("archives/html/epex_FR_*.html"), key=os.path.getmtime)
elec_latest = {}
for path in elec_files:
    date_str = extract_date(path, "epex_FR")
    if date_str:
        elec_latest[date_str] = path

price_data = {}
for delivery_date, html_file in sorted(elec_latest.items()):
    date_obj = datetime.strptime(delivery_date, "%Y-%m-%d")
    col_label = date_obj.strftime("%d-%b").lower().replace("jan", "janv").replace("may", "mai").replace("oct", "oct.")

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    hour_tags = soup.select("div.fixed-column ul li a")
    hours = [a.text.strip() for a in hour_tags]

    price_tags = soup.select("div.js-table-values table tbody tr td:nth-of-type(4)")
    prices = [td.text.strip().replace(",", ".") for td in price_tags]

    try:
        prices = [float(p) for p in prices]
    except ValueError:
        prices = []
        
    if len(prices) == 24:
        price_data[col_label] = price
    
    elif len(prices) == 96:
        # Données quart-horaires → on fait la moyenne par heure
        hourly_prices = []
        for h in range(24):
            quarter_values = prices[h*4:(h+1)*4]
            avg = sum(quarter_values) / len(quarter_values)
            hourly_prices.append(round(avg, 2))
        price_data[col_label] = hourly_prices
        print(f"🕐 {delivery_date} : 96 valeurs détectées → moyennées en 24 valeurs horaires")

    else:
        # Nombre inattendu de valeurs
        print(f"⚠️ {delivery_date} : {len(prices)} valeurs détectées (inattendu)")
        price_data[col_label] = ["-"] * 24


# Créer labels horaires
heure_labels = [f"{str(h).zfill(2)} - {str(h+1).zfill(2)}" for h in range(24)]
df_new_elec = pd.DataFrame(price_data, index=heure_labels)

# Fusion avec ancienne version
df_elec = df_existing_elec.copy()
for col in df_new_elec.columns:
    if col not in df_existing_elec.columns:
        df_elec[col] = df_new_elec[col]
    else:
        # Mettre à jour uniquement si les valeurs sont différentes
        old = df_existing_elec[col].tolist()
        new = df_new_elec[col].tolist()
        if old != new:
            df_elec[col] = new

# Conserver les colonnes de l'ancien Excel qui n'existent plus en HTML
for col in df_existing_elec.columns:
    if col not in df_elec.columns:
        df_elec[col] = df_existing_elec[col]

# Réordonner colonnes par date
def date_key(col):
    try:
        return datetime.strptime(col[:2] + "-" + col[3:], "%d-%b")
    except:
        return datetime.max

df_elec = df_elec.reindex(sorted(df_elec.columns, key=date_key), axis=1)

# === GAZ ===
gaz_files = sorted(glob.glob("archives/html_gaz/eex_gaz_*.html"), key=os.path.getmtime)
gaz_records = []
for path in gaz_files:
    date_str = extract_date(path, "eex_gaz")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        item = data["results"]["items"][0]
        gaz_records.append({
            "Date": date_str,
            "Last Price": item.get("ontradeprice", "-")
        })
    except Exception:
        gaz_records.append({
            "Date": date_str,
            "Last Price": "-"
        })

df_new_gaz = pd.DataFrame(gaz_records).sort_values("Date")

if not df_existing_gaz.empty:
    df_gaz = pd.merge(df_existing_gaz, df_new_gaz, on="Date", how="outer", suffixes=("_old", ""))
    if "Last Price_old" in df_gaz.columns:
        df_gaz["Last Price"] = df_gaz["Last Price"].combine_first(df_gaz["Last Price_old"])
        df_gaz.drop(columns=["Last Price_old"], inplace=True)
else:
    df_gaz = df_new_gaz

# On garde uniquement les colonnes souhaitées
df_gaz = df_gaz[["Date", "Last Price"]]

# === CO2 ===
co2_files = sorted(glob.glob("archives/html_co2/eex_co2_*.html"), key=os.path.getmtime)
co2_records = []
for path in co2_files:
    date_str = extract_date(path, "eex_co2")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        item = data["results"]["items"][0]
        co2_records.append({
            "Date": date_str,
            "Last Price": item.get("ontradeprice", "-")
        })
    except Exception:
        co2_records.append({
            "Date": date_str,
            "Last Price": "-"
        })

df_new_co2 = pd.DataFrame(co2_records).sort_values("Date")
if not df_existing_co2.empty:
    df_co2 = pd.merge(df_existing_co2, df_new_co2, on="Date", how="outer", suffixes=("_old", ""))
    if "Last Price_old" in df_co2.columns:
        df_co2["Last Price"] = df_co2["Last Price"].combine_first(df_co2["Last Price_old"])
        df_co2.drop(columns=["Last Price_old"], inplace=True)
else:
    df_co2 = df_new_co2

# === Sauvegarde Excel ===
colonnes_a_supprimer = ["Bid", "Ask", "Last"]
for df in [df_gaz, df_co2]:
    for col in colonnes_a_supprimer:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df_elec.to_excel(writer, sheet_name="Prix Spot", index_label="Heure")
    df_gaz.to_excel(writer, sheet_name="Gaz", index=False)
    df_co2.to_excel(writer, sheet_name="CO2", index=False)

print(f"✅ Fichier Excel mis à jour avec électricité, gaz et CO2 : {excel_file}")



