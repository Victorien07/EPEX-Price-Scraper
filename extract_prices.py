# scripts/extract_prices.py

from bs4 import BeautifulSoup
import pandas as pd
import glob
import re
import os

# Récupérer le dernier fichier HTML
html_files = sorted(glob.glob("html/epex_FR_*.html"), reverse=True)
if not html_files:
    raise FileNotFoundError("Aucun fichier HTML trouvé dans html/")
html_file = html_files[0]
delivery_date = re.search(r"epex_FR_(\d{4}-\d{2}-\d{2})", html_file).group(1)

with open(html_file, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# 🟡 1. Heures
hour_tags = soup.select("div.fixed-column ul li a")
hours = [a.text.strip() for a in hour_tags]

# 🟡 2. Prix horaires
price_tags = soup.select("div.js-table-values table tbody tr td:nth-of-type(4)")
prices = [float(td.text.strip().replace(",", ".")) for td in price_tags]

# 🟡 3. Baseload et Peakload
baseload_tag = soup.find("th", string=re.compile("Baseload"))
peakload_tag = soup.find("th", string=re.compile("Peakload"))
baseload = float(baseload_tag.find_next("span").text.strip().replace(",", ".")) if baseload_tag else None
peakload = float(peakload_tag.find_next("span").text.strip().replace(",", ".")) if peakload_tag else None

# ✅ Vérifications
if len(hours) != 24 or len(prices) != 24:
    raise ValueError("Erreur : heures ou prix incomplets (attendu 24 chacun).")

# 📈 Construire le DataFrame
df = pd.DataFrame({
    "Date": delivery_date,
    "Hour": hours,
    "Price (€/MWh)": prices,
    "Baseload": [baseload]*24,
    "Peakload": [peakload]*24
})

# 📁 Écrire dans le CSV général (append)
csv_file = "data/epexspot_prices.csv"
if os.path.exists(csv_file):
    df.to_csv(csv_file, mode="a", index=False, header=False)
else:
    df.to_csv(csv_file, index=False)

print(f"✅ Extraction réussie pour {delivery_date} ({html_file}) → {csv_file}")
