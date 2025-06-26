import os
import requests
from datetime import datetime, timedelta

# === Setup
now = datetime.utcnow() + timedelta(hours=2)
weekday = now.weekday()

# 🔧 SIMULATION : Forcer la date pour tester le dimanche ou le lundi
# Ex : simuler lundi 2025-06-23 (le vendredi précédent est le 2025-06-20)
TEST_MODE = False
if TEST_MODE:
    now = datetime(2025, 6, 23, 10, 0)  # 👈 Change la date ici (dimanche ou lundi)

weekday = now.weekday()

# Ne s'exécute que dimanche (6) et lundi (0)
if weekday not in [0, 6]:
    print("⏩ Ce n'est ni dimanche ni lundi : pas de récupération PEG WEEKEND / CO2.")
    exit(0)

# === Dossiers
os.makedirs("archives/html_gaz", exist_ok=True)
os.makedirs("archives/html_co2", exist_ok=True)
os.makedirs("data", exist_ok=True)

headers = {
    "Accept": "*/*",
    "Origin": "https://www.eex.com",
    "Referer": "https://www.eex.com",
    "User-Agent": "Mozilla/5.0"
}

# === Dates cibles
friday = now - timedelta(days=(3 if weekday == 0 else 2))
friday_api = friday.strftime("%Y/%m/%d")
parsed_friday = friday.strftime("%Y-%m-%d")
saturday = (friday + timedelta(days=1)).strftime("%Y-%m-%d")
sunday = (friday + timedelta(days=2)).strftime("%Y-%m-%d")

# === GAZ : PEG WEEKEND
gaz_api = "https://webservice-eex.gvsi.com/query/json/getDaily/ontradeprice/onexchsingletradevolume/close/tradedatetimegmt/"
gaz_params = {
    "priceSymbol": '"#E.PEG_GWE1"',
    "chartstartdate": friday_api,
    "chartstopdate": friday_api,
    "dailybarinterval": "Days",
    "aggregatepriceselection": "First"
}

try:
    print("🌐 Récupération PEG WEEKEND (GAZ)...")
    resp = requests.get(gaz_api, headers=headers, params=gaz_params, timeout=15)
    resp.raise_for_status()
    json_data = resp.json()

    item = json_data.get("results", {}).get("items", [])[0]

    for label_date in [saturday, sunday]:
        gaz_html = f"archives/html_gaz/eex_gaz_{label_date}.html"
        if os.path.exists(gaz_html):
            print(f"📝 Fichier existant (GAZ {label_date}), il sera remplacé.")
        with open(gaz_html, "w", encoding="utf-8") as f:
            f.write(resp.text)
        print(f"✅ Données GAZ PEG WEEKEND sauvegardées : {gaz_html}")

except Exception as e:
    print(f"❌ Erreur GAZ PEG WEEKEND : {e}")

# === CO2 : toujours la donnée du vendredi
co2_api = "https://webservice-eex.gvsi.com/query/json/getDaily/ontradeprice/onexchsingletradevolume/close/onexchtradevolumeeex/offexchtradevolumeeex/tradedatetimegmt/"
co2_params = {
    "priceSymbol": '"/E.SEME[0]"',
    "chartstartdate": friday_api,
    "chartstopdate": friday_api,
    "dailybarinterval": "Days",
    "aggregatepriceselection": "First"
}

try:
    print("🌐 Récupération CO2 (vendredi pour archive week-end)...")
    resp = requests.get(co2_api, headers=headers, params=co2_params, timeout=15)
    resp.raise_for_status()
    json_data = resp.json()

    item = json_data.get("results", {}).get("items", [])[0]

    for label_date in [saturday, sunday]:
        co2_html = f"archives/html_co2/eex_co2_{label_date}.html"
        if os.path.exists(co2_html):
            print(f"📝 Fichier existant (CO2 {label_date}), il sera remplacé.")
        with open(co2_html, "w", encoding="utf-8") as f:
            f.write(resp.text)
        print(f"✅ Données CO2 sauvegardées : {co2_html}")

except Exception as e:
    print(f"❌ Erreur récupération CO2 : {e}")
