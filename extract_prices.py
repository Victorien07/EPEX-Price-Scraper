import os
import glob
import re
import json
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup  # pour parser plus fiablement

# === Préparation ===
os.makedirs("data", exist_ok=True)
excel_file = "data/epexspot_prices.xlsx"

def extract_date(filename, prefix):
    m = re.search(fr"{prefix}_(\d{{4}}-\d{{2}}-\d{{2}})", filename)
    return m.group(1) if m else None

if os.path.exists(excel_file):
    sheets = pd.read_excel(excel_file, sheet_name=None, index_col=0)
    df_existing_elec = sheets.get("Prix Spot", pd.DataFrame())
    df_existing_gaz = sheets.get("Gaz", pd.DataFrame())
    df_existing_co2 = sheets.get("CO2", pd.DataFrame())
else:
    df_existing_elec = pd.DataFrame()
    df_existing_gaz = pd.DataFrame()
    df_existing_co2 = pd.DataFrame()

# === ÉLECTRICITÉ ===
elec_files = sorted(glob.glob("archives/html/epex_FR_*.html"), key=os.path.getmtime)
new_cols = []
df_new_elec = pd.DataFrame(index=[f"{h:02d} - {h+1:02d}" for h in range(24)])

for path in elec_files:
    date_str = extract_date(path, "epex_FR")
    if not date_str:
        continue

    col_label = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%b").lower().replace("jan", "janv").replace("may", "mai").replace("oct", "oct.")

    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # extraction robuste : on cherche les cellules de prix
    tds = soup.find_all("td")
    prices = []
    for td in tds:
    txt = td.get_text(strip=True).replace(",", ".")
    if re.fullmatch(r"\d+\.\d+", txt):
        try:
            prices.append(float(txt))
        except ValueError:
            continue
            prices.append(float(td.get_text().replace(",", ".")))
    if len(prices) < 24:
        print(f"⚠️ Données incomplètes pour {col_label} ({len(prices)}/24)")
    prices = prices[:24] + ["-"] * max(0, 24 - len(prices))
    df_new_elec[col_label] = prices
    new_cols.append(col_label)

# On écrase les anciennes colonnes concernées
df_elec = df_existing_elec.copy()
for col in new_cols:
    df_elec[col] = df_new_elec[col]

# === GAZ ===
gaz_files = sorted(glob.glob("archives/html_gaz/eex_gaz_*.html"), key=os.path.getmtime)
gaz_records = []
for path in gaz_files:
    date_str = extract_date(path, "eex_gaz")
    try:
        data = json.load(open(path, encoding="utf-8"))
        item = data["results"]["items"][0]
        gaz_records.append({
            "Date": date_str,
            "Last Price": item.get("ontradeprice", "-"),
            "Last Volume": item.get("onexchsingletradevolume", "-"),
            "End of Day Index": item.get("close", "-")
        })
    except Exception:
        gaz_records.append({"Date": date_str, "Last Price": "-", "Last Volume": "-", "End of Day Index": "-"})

df_new_gaz = pd.DataFrame(sorted(gaz_records, key=lambda x: x["Date"]))
if not df_existing_gaz.empty:
    df_gaz = pd.merge(df_existing_gaz, df_new_gaz, on="Date", how="outer", suffixes=("_old", ""))
    for c in ["Last Price", "Last Volume", "End of Day Index"]:
        if f"{c}_old" in df_gaz:
            df_gaz[c] = df_gaz[c].combine_first(df_gaz[f"{c}_old"])
            df_gaz.drop(columns=[f"{c}_old"], inplace=True)
else:
    df_gaz = df_new_gaz

# === CO2 ===
co2_files = sorted(glob.glob("archives/html_co2/eex_co2_*.html"), key=os.path.getmtime)
co2_records = []
for path in co2_files:
    date_str = extract_date(path, "eex_co2")
    try:
        data = json.load(open(path, encoding="utf-8"))
        item = data["results"]["items"][0]
        co2_records.append({"Date": date_str, "Last Price": item.get("ontradeprice", "-")})
    except Exception:
        co2_records.append({"Date": date_str, "Last Price": "-"})

df_new_co2 = pd.DataFrame(sorted(co2_records, key=lambda x: x["Date"]))
if not df_existing_co2.empty:
    df_co2 = pd.merge(df_existing_co2, df_new_co2, on="Date", how="outer", suffixes=("_old", ""))
    if "Last Price_old" in df_co2:
        df_co2["Last Price"] = df_co2["Last Price"].combine_first(df_co2["Last Price_old"])
        df_co2.drop(columns=["Last Price_old"], inplace=True)
else:
    df_co2 = df_new_co2

# === Nettoyage colonnes inutiles ===
for df in [df_gaz, df_co2]:
    for drop in ["Bid", "Ask", "Last"]:
        if drop in df.columns:
            df.drop(columns=[drop], inplace=True)

# === Sauvegarde ===
with pd.ExcelWriter(excel_file, engine="openpyxl") as w:
    df_elec.to_excel(w, sheet_name="Prix Spot", index_label="Heure")
    df_gaz.to_excel(w, sheet_name="Gaz", index=False)
    df_co2.to_excel(w, sheet_name="CO2", index=False)

print(f"✅ Excel mis à jour : {excel_file}")
