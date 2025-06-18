import os
import requests
from datetime import datetime, timedelta

# === Dates ===
now = datetime.utcnow() + timedelta(hours=2)
yesterday_display = (now - timedelta(days=1)).strftime("%Y-%m-%d")
yesterday_api = (now - timedelta(days=1)).strftime("%Y/%m/%d")  # format API

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

# === Gaz
gaz_api = "https://webservice-eex.gvsi.com/query/json/getDaily/ontradeprice/onexchsingletradevolume/close/tradedatetimegmt/"
gaz_params = {
    "priceSymbol": '"#E.PEG_GND1"',
    "chartstartdate": yesterday_api,
    "chartstopdate": yesterday_api,
    "dailybarinterval": "Days",
    "aggregatepriceselection": "First"
}
gaz_html = f"archives/html_gaz/eex_gaz_{yesterday_display}.html"

try:
    print(f"🌐 Récupération données GAZ pour {yesterday_display}...")
    resp = requests.get(gaz_api, headers=headers, params=gaz_params, timeout=15)
    resp.raise_for_status()
    with open(gaz_html, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"✅ Fichier HTML GAZ sauvegardé dans {gaz_html}")
except Exception as e:
    print(f"❌ Erreur récupération gaz : {e}")
    with open(gaz_html, "w", encoding="utf-8") as f:
        f.write("")

# === CO2
co2_api = "https://webservice-eex.gvsi.com/query/json/getDaily/ontradeprice/onexchsingletradevolume/close/onexchtradevolumeeex/offexchtradevolumeeex/tradedatetimegmt/"
co2_params = {
    "priceSymbol": '"/E.SEME[0]"',
    "chartstartdate": yesterday_api,
    "chartstopdate": yesterday_api,
    "dailybarinterval": "Days",
    "aggregatepriceselection": "First"
}
co2_html = f"archives/html_co2/eex_co2_{yesterday_display}.html"

try:
    print(f"🌐 Récupération données CO2 pour {yesterday_display}...")
    resp = requests.get(co2_api, headers=headers, params=co2_params, timeout=15)
    resp.raise_for_status()
    with open(co2_html, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"✅ Fichier HTML CO2 sauvegardé dans {co2_html}")
except Exception as e:
    print(f"❌ Erreur récupération CO2 : {e}")
    with open(co2_html, "w", encoding="utf-8") as f:
        f.write("")
