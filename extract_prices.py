from bs4 import BeautifulSoup
import pandas as pd
import glob
import re
import os

# Trouver le dernier fichier HTML dans archives/html/
html_files = sorted(glob.glob("archives/html/epex_FR_*.html"), reverse=True)
if not html_files:
    raise FileNotFoundError("Aucun fichier HTML trouvé dans archives/html/")
html_file = html_files[0]
delivery_date = re.search(r"epex_FR_(\d{4}-\d{2}-\d{2})", html_file).group(1)

# Lire le fichier HTML
with open(html_file, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Extraire les heures
hour_tags = soup.select("div.fixed-column ul li a")
hours = [a.text.strip() for a in hour_tags]

# Extraire les prix horaires (colonne 4)
price_tags = soup.select("div.js-table-values table tbody tr td:nth-of-type(4)")
prices = [float(td.text.strip().replace(",", ".")) for td in price_tags]

# Extraire baseload et peakload
baseload_tag = soup.find("th", string=re.compile("Baseload"))
peakload_tag = soup.find("th", string=re.compile("Peakload"))
baseload = float(baseload_tag.find_next("span").text.strip().replace(",", ".")) if baseload_tag else None
peakload = float(peakload_tag.find_next("span").text.strip().replace(",", ".")) if peakload_tag else None

if len(hours) != 24 or len(prices) != 24:
    raise ValueError("Erreur : heures ou prix incomplets")

# Construire le tableau
df = pd.DataFrame({
    "Date": delivery_date,
    "Hour": hours,
    "Price (€/MWh)": prices,
    "Baseload": [baseload] * 24,
    "Peakload": [peakload] * 24
})

# Sauvegarde dans data/epexspot_prices.csv
os.makedirs("data", exist_ok=True)
csv_path = "data/epexspot_prices.csv"
if os.path.exists(csv_path):
    df.to_csv(csv_path, mode="a", index=False, header=False)
else:
    df.to_csv(csv_path, index=False)

print(f"✅ Extraction réussie → {csv_path}")
