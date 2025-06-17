from bs4 import BeautifulSoup
import pandas as pd
import glob
import re
import os
from datetime import datetime

# Lire tous les fichiers HTML triés par date
html_files = sorted(glob.glob("archives/html/epex_FR_*.html"))
if not html_files:
    raise FileNotFoundError("Aucun fichier HTML trouvé dans archives/html/")

# Créer le dossier Excel s’il n’existe pas
os.makedirs("data", exist_ok=True)
excel_file = "data/epexspot_prices.xlsx"

# Liste pour stocker les colonnes par date
price_data = {}

for html_file in html_files:
    date_match = re.search(r"epex_FR_(\d{4}-\d{2}-\d{2})", html_file)
    if not date_match:
        continue
    delivery_date = date_match.group(1)
    date_obj = datetime.strptime(delivery_date, "%Y-%m-%d")
    col_label = date_obj.strftime("%d-%b").lower().replace("jan", "janv").replace("may", "mai").replace("oct", "oct.")  # Traduction FR simplifiée

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    hour_tags = soup.select("div.fixed-column ul li a")
    hours = [a.text.strip() for a in hour_tags]

    price_tags = soup.select("div.js-table-values table tbody tr td:nth-of-type(4)")
    prices = [float(td.text.strip().replace(",", ".")) for td in price_tags]

    if len(hours) != 24 or len(prices) != 24:
        continue

    price_data[col_label] = prices

# Créer la structure de tableau
if not price_data:
    print("⚠️ Aucun nouveau fichier HTML à traiter.")
else:
    # Index des heures
    heure_labels = [f"{str(h).zfill(2)} - {str(h+1).zfill(2)}" for h in range(24)]

    df = pd.DataFrame(price_data, index=heure_labels)

    # Ajout des lignes de moyennes demandées
    df.loc["FR DAY PEAK"] = df.iloc[8:20].mean()  # de 08h à 20h exclu (08-19)
    df.loc["FR DAY BASE"] = df.iloc[0:24].mean()
    df.loc["JOURNEE ECO | MOYENNE PRIX SPOT 07h à 20h"] = df.iloc[7:20].mean()

    # Ajout d'une colonne unité
    df.insert(1, "Unité", "€/MWh")
    df.iloc[24:, 1] = ""  # Vider colonne unité pour les lignes de moyenne

    # Exporter en Excel
    df.to_excel(excel_file, sheet_name="Prix Spot", index_label="Heure")
    print(f"✅ Fichier Excel créé : {excel_file}")
