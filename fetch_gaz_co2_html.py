import os
import requests
from datetime import datetime, timedelta

# Dates
today = datetime.today()
tomorrow = today + timedelta(days=1)
delivery_day = tomorrow.strftime("%Y-%m-%d")

# URL gaz : lien "market results" pour Day-Ahead France
gaz_url = (
    "https://www.epexspot.com/en/market-results"
    f"?market_area=FR&auction=MRC&trading_date={today.strftime('%Y-%m-%d')}"
    f"&delivery_date={delivery_day}"
    "&underlying_year=&modality=Auction&sub_modality=DayAhead"
    "&technology=&data_mode=table&period=&production_period="
)

# CO₂ comme avant
co2_url = "https://www.eex.com/en/market-data/market-data-hub/environmentals/spot"

# Dossiers de sortie
os.makedirs("archives/html_gaz", exist_ok=True)
os.makedirs("archives/html_co2", exist_ok=True)

gaz_file = f"archives/html_gaz/eex_gaz_{delivery_day}.html"
co2_file = f"archives/html_co2/eex_co2_{today.strftime('%Y-%m-%d')}.html"

def download(url, path, label):
    if os.path.exists(path):
        print(f"✅ {label} déjà téléchargé ({path})")
    else:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            open(path, "w", encoding="utf-8").write(r.text)
            print(f"⬇️ {label} téléchargé sur {path}")
        else:
            print(f"⚠️ Pas encore disponible : {label} (HTTP {r.status_code})")
            open(path, "w", encoding="utf-8").write(r.text)  # Optionnel

download(gaz_url, gaz_file, f"Gaz PEG Day-Ahead {delivery_day}")
download(co2_url, co2_file, "CO₂ EUA Spot")
