import os
import requests
from datetime import datetime

# Configuration
today = datetime.today().strftime("%Y-%m-%d")
gaz_url = "https://www.eex.com/en/market-data/market-data-hub/natural-gas/spot"
co2_url = "https://www.eex.com/en/market-data/market-data-hub/environmentals/spot"

# Dossiers de destination
gaz_folder = "archives/html_gaz"
co2_folder = "archives/html_co2"
os.makedirs(gaz_folder, exist_ok=True)
os.makedirs(co2_folder, exist_ok=True)

# Fichiers de sortie
gaz_file = os.path.join(gaz_folder, f"eex_gaz_{today}.html")
co2_file = os.path.join(co2_folder, f"eex_co2_{today}.html")

# Fonction utilitaire pour télécharger une page
def download_page(url, file_path, label):
    if os.path.exists(file_path):
        print(f"⏩ {label} déjà téléchargé ({file_path})")
        return
    try:
        print(f"⬇️ Téléchargement de {label} depuis {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"✅ {label} sauvegardé : {file_path}")
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement de {label} : {e}")

# Télécharger les deux pages
download_page(gaz_url, gaz_file, "Gaz NBP")
download_page(co2_url, co2_file, "CO₂ EUA Spot")
