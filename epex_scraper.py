import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup

def fetch_epex_prices():
    # Date de test forcée (tu pourras remettre l'automatique ensuite)
    trading_date = "2025-06-13"
    delivery_date = "2025-06-14"

    url = f"https://www.epexspot.com/en/market-results?market_area=FR&auction=MRC&trading_date={trading_date}&delivery_date={delivery_date}&modality=Auction&sub_modality=DayAhead&data_mode=table"
    print(f"🔗 URL utilisée : {url}")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Erreur HTTP {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="table table-sm table-hover")

    if not table:
        print("❌ Tableau non trouvé sur la page.")
        return

    rows = table.find_all("tr")
    data = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            hour = cols[0].get_text(strip=True)
            price = cols[1].get_text(strip=True).replace(",", ".").replace("€", "")
            try:
                price = float(price)
                data.append({"hour": hour, "price_eur_mwh": price})
            except ValueError:
                continue

    if data:
        df = pd.DataFrame(data)
        filename = f"epex_FR_{delivery_date}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Fichier enregistré : {filename}")
    else:
        print("⚠️ Aucun prix trouvé.")

if __name__ == "__main__":
    fetch_epex_prices()
