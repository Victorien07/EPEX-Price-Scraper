import os
import requests
from datetime import datetime, timedelta

# === Setup
now = datetime.utcnow() + timedelta(hours=2)
yesterday = now - timedelta(days=1)
today_api = yesterday.strftime("%Y/%m/%d")

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

# === GAZ ===
gaz_api = "https://webservice-eex.gvsi.com/query/json/getDaily/ontradeprice/onexchsingletradevolume/close/tradedatetimegmt/"
gaz_params = {
    "priceSymbol": '"#E.PEG_GND1"',
    "chartstartdate": today_api,
    "chartstopdate": today_api,
    "dailybarinterval": "Days",
    "aggregatepriceselection": "First"
}

try:
    print("🌐 Récupération données GAZ...")
    resp = requests.get(gaz_api, headers=headers, params=gaz_params, timeout=15)
    resp.raise_for_status()
    json_data = resp.json()

    item = json_data.get("results", {}).get("items", [])[0]
    raw_date = item.get("tradedatetimegmt", "")
    parsed_date = datetime.strptime(raw_date.split()[0], "%m/%d/%Y").strftime("%Y-%m-%d")
    gaz_html = f"archives/html_gaz/eex_gaz_{parsed_date}.html"

    with open(gaz_html, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"✅ Données GAZ sauvegardées : {gaz_html}")

except Exception as e:
    print(f"❌ Erreur récupération GAZ : {e}")

# === CO2 ===
co2_api = "https://webservice-eex.gvsi.com/query/json/getDaily/ontradeprice/onexchsingletradevolume/close/onexchtradevolumeeex/offexchtradevolumeeex/tradedatetimegmt/"
co2_params = {
    "priceSymbol": '"/E.SEME[0]"',
    "chartstartdate": today_api,
    "chartstopdate": today_api,
    "dailybarinterval": "Days",
    "aggregatepriceselection": "First"
}

try:
    print("🌐 Récupération données CO2...")
    resp = requests.get(co2_api, headers=headers, params=co2_params, timeout=15)
    resp.raise_for_status()
    json_data = resp.json()

    item = json_data.get("results", {}).get("items", [])[0]
    raw_date = item.get("tradedatetimegmt", "")
    parsed_date = datetime.strptime(raw_date.split()[0], "%m/%d/%Y").strftime("%Y-%m-%d")
    co2_html = f"archives/html_co2/eex_co2_{parsed_date}.html"

    with open(co2_html, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"✅ Données CO2 sauvegardées : {co2_html}")

except Exception as e:
    print(f"❌ Erreur récupération CO2 : {e}")
