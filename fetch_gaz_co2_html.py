import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# === Dates ===
now = datetime.utcnow() + timedelta(hours=2)
yesterday_display = (now - timedelta(days=1)).strftime("%Y-%m-%d")
yesterday_api = (now - timedelta(days=1)).strftime("%Y/%m/%d")  # format pour API

# === Dossiers ===
os.makedirs("data", exist_ok=True)

# === API: Prix du GAZ ===
gaz_url = "https://webservice-eex.gvsi.com/query/json/getDaily/ontradeprice/onexchsingletradevolume/close/tradedatetimegmt/"
gaz_params = {
    "priceSymbol": '"#E.PEG_GND1"',
    "chartstartdate": yesterday_api,
    "chartstopdate": yesterday_api,
    "dailybarinterval": "Days",
    "aggregatepriceselection": "First"
}
headers = {
    "Accept": "*/*",
    "Origin": "https://www.eex.com",
    "Referer": "https://www.eex.com",
    "User-Agent": "Mozilla/5.0"
}

print(f"🌐 Récupération prix GAZ pour {yesterday_display}...")
try:
    gaz_resp = requests.get(gaz_url, params=gaz_params, headers=headers, timeout=15)
    gaz_json = gaz_resp.json()
    result = gaz_json["Series"][0]["Values"][0]
    gaz_data = [{
        "Date": yesterday_display,
        "Bid": result[1],
        "Ask": result[2],
        "Last": result[0],
    }]
except Exception as e:
    print("⚠️ Erreur Gaz :", e)
    gaz_data = [{
        "Date": yesterday_display,
        "Bid": "-", "Ask": "-", "Last": "-"
    }]
df_gaz = pd.DataFrame(gaz_data)


# === API: Prix du CO2 ===
co2_url = "https://webservice-eex.gvsi.com/query/json/getDaily/ontradeprice/onexchsingletradevolume/close/onexchtradevolumeeex/offexchtradevolumeeex/tradedatetimegmt/"
co2_params = {
    "priceSymbol": '"/E.SEME[0]"',
    "chartstartdate": yesterday_api,
    "chartstopdate": yesterday_api,
    "dailybarinterval": "Days",
    "aggregatepriceselection": "First"
}

print(f"🌐 Récupération prix CO2 pour {yesterday_display}...")
try:
    co2_resp = requests.get(co2_url, params=co2_params, headers=headers, timeout=15)
    co2_json = co2_resp.json()
    result = co2_json["Series"][0]["Values"][0]
    co2_data = [{
        "Date": result[-1].split("T")[0],
        "Last Price": result[0]
    }]
except Exception as e:
    print("⚠️ Erreur CO2 :", e)
    co2_data = [{
        "Date": yesterday_display,
        "Last Price": "-"
    }]
df_co2 = pd.DataFrame(co2_data)

# === Export Excel
excel_file = "data/gaz_co2_data.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df_gaz.to_excel(writer, sheet_name="Gaz", index=False)
    df_co2.to_excel(writer, sheet_name="CO2", index=False)

print("✅ Données Gaz & CO2 récupérées et enregistrées.")
