import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup

def fetch_epex_prices():
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://www.epexspot.com/en/market-results?market_area=FR&auction=MRC&trading_date={datetime.date.today()}&delivery_date={tomorrow}&modality=Auction&sub_modality=DayAhead&data_mode=table"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
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
        df.to_csv(f"epex_FR_{tomorrow}.csv", index=False)
        print(f"✅ Fichier enregistré : epex_FR_{tomorrow}.csv")
    else:
        print("⚠️ Aucun prix trouvé.")

if __name__ == "__main__":
    fetch_epex_prices()
