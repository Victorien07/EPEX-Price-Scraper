import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def fetch_epex_prices():
    # 📅 Aujourd’hui = jour d’exécution ; Demain = livraison
    trading_date = datetime.date.today().strftime("%Y-%m-%d")
    delivery_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    # 📂 Créer les dossiers d’archives
    os.makedirs("archives/html", exist_ok=True)
    os.makedirs("archives/csv", exist_ok=True)

    # 🌐 URL cible
    url = (
        f"https://www.epexspot.com/en/market-results?"
        f"market_area=FR&auction=MRC"
        f"&trading_date={trading_date}"
        f"&delivery_date={delivery_date}"
        f"&modality=Auction&sub_modality=DayAhead&data_mode=table"
    )
    print(f"🔗 URL utilisée : {url}")

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    # 💾 Archive HTML
    html_path = f"archives/html/epex_FR_{delivery_date}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"📄 Page HTML archivée : {html_path}")

    # 📊 Extraction du tableau
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="table table-sm table-hover")

    if not table:
        print("⚠️ Tableau introuvable (probablement trop tôt).")
        return

    # 🔍 Lecture des lignes
    data = []
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 2:
            hour = cols[0].get_text(strip=True)
            price = cols[1].get_text(strip=True).replace(",", ".").replace("€", "")
            try:
                data.append({"hour": hour, "price_eur_mwh": float(price)})
            except ValueError:
                continue

    # 💾 Sauvegarde CSV
    if data:
        df = pd.DataFrame(data)
        csv_path = f"archives/csv/epex_FR_{delivery_date}.csv"
        df.to_csv(csv_path, index=False)
        print(f"✅ Données enregistrées : {csv_path}")
    else:
        print("⚠️ Aucun prix valide trouvé dans le tableau.")

if __name__ == "__main__":
    fetch_epex_prices()
