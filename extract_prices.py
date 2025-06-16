from bs4 import BeautifulSoup
import pandas as pd
import glob
import re
import os

# Lire tous les fichiers HTML triés par date
html_files = sorted(glob.glob("archives/html/epex_FR_*.html"))
if not html_files:
    raise FileNotFoundError("Aucun fichier HTML trouvé dans archives/html/")

# Créer le dossier CSV s’il n’existe pas
os.makedirs("docs", exist_ok=True)
csv_file = "docs/epexspot_prices.csv"

# Charger l’existant s’il y a déjà un CSV
existing = pd.read_csv(csv_file) if os.path.exists(csv_file) else pd.DataFrame()

# Pour chaque HTML
all_data = []
for html_file in html_files:
    date_match = re.search(r"epex_FR_(\d{4}-\d{2}-\d{2})", html_file)
    if not date_match:
        continue
    delivery_date = date_match.group(1)

    # Sauter les doublons déjà dans le CSV
    if not existing.empty and delivery_date in existing["Date"].values:
        continue

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    hour_tags = soup.select("div.fixed-column ul li a")
    hours = [a.text.strip() for a in hour_tags]

    price_tags = soup.select("div.js-table-values table tbody tr td:nth-of-type(4)")
    prices = [float(td.text.strip().replace(",", ".")) for td in price_tags]

    baseload_tag = soup.find("th", string=re.compile("Baseload"))
    peakload_tag = soup.find("th", string=re.compile("Peakload"))
    baseload = float(baseload_tag.find_next("span").text.strip().replace(",", ".")) if baseload_tag else None
    peakload = float(peakload_tag.find_next("span").text.strip().replace(",", ".")) if peakload_tag else None

    if len(hours) != 24 or len(prices) != 24:
        continue

    df = pd.DataFrame({
        "Date": delivery_date,
        "Hour": hours,
        "Price (€/MWh)": prices,
        "Baseload": [baseload]*24,
        "Peakload": [peakload]*24
    })

    all_data.append(df)

# Fusionner et écrire
if all_data:
    new_data = pd.concat(all_data)
    if not existing.empty:
        final = pd.concat([existing, new_data])
    else:
        final = new_data
    final.to_csv(csv_file, index=False)
    print(f"✅ CSV mis à jour : {csv_file}")
else:
    print("⚠️ Aucun nouveau fichier HTML à traiter.")
