import datetime
import os
import requests
import sys  # <- ajouté

def fetch_epex_prices():
    trading_date = datetime.date.today().strftime("%Y-%m-%d")
    delivery_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    os.makedirs("archives/html", exist_ok=True)
    os.makedirs("archives/csv", exist_ok=True)

    url = (
        f"https://www.epexs"
        f"market_area=FR&auction=MRC"
        f"&trading_date={trading_date}"
        f"&delivery_date={delivery_date}"
        f"&modality=Auction&sub_modality=DayAhead&data_mode=table&product=60"
    )

    html_path = f"archives/html/epex_FR_{delivery_date}.html"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Referer": "https://www.epexspot.com/en/market-results",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        print("📡 Requête principale (requests)...")
        response = requests.get(url, headers=headers, timeout=30)
        status = response.status_code
        print(f"📶 Statut HTTP : {status}")

        if status == 200 and "Forbidden" not in response.text:
            print("✅ Page HTML téléchargée avec succès.")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"📄 Page HTML archivée : {html_path}")
        else:
            print("❌ Accès refusé ou page vide, page sauvegardée pour diagnostic.")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"📄 Page archivée pour analyse : {html_path}")
            sys.exit(1)  # <- signal d’échec pour GitHub

    except Exception as e:
        print(f"❌ Erreur lors de la récupération : {e}")
        sys.exit(1)  # <- signal d’échec pour GitHub

if __name__ == "__main__":
    fetch_epex_prices()


'''

import datetime
import os
import requests

def fetch_epex_prices():
    # 📅 Dates
    trading_date = datetime.date.today().strftime("%Y-%m-%d")
    delivery_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    # 📂 Dossiers
    os.makedirs("archives/html", exist_ok=True)
    os.makedirs("archives/csv", exist_ok=True)

    # 🌐 URL cible
    url = (
        f"https://www.epexspot.com/en/market-results?"
        f"market_area=FR&auction=MRC"
        f"&trading_date={trading_date}"
        f"&delivery_date={delivery_date}"
        f"&modality=Auction&sub_modality=DayAhead&data_mode=table&product=60"
    )

    print(f"🔗 URL utilisée : {url}")

    # 🧠 Headers complets (simulation navigateur Chrome)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Referer": "https://www.epexspot.com/en/market-results",
        "Upgrade-Insecure-Requests": "1",
    }

    html_path = f"archives/html/epex_FR_{delivery_date}.html"

    try:
        print("📡 Requête principale (requests)...")
        response = requests.get(url, headers=headers, timeout=30)
        status = response.status_code
        print(f"📶 Statut HTTP : {status}")

        # ⚠️ Vérification simple du contenu
        if status == 200 and "Forbidden" not in response.text:
            print("✅ Page HTML téléchargée avec succès.")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"📄 Page HTML archivée : {html_path}")
        else:
            print("❌ Accès refusé ou page vide, page sauvegardée pour diagnostic.")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"📄 Page archivée pour analyse : {html_path}")

    except Exception as e:
        print(f"❌ Erreur lors de la récupération : {e}")

if __name__ == "__main__":
    fetch_epex_prices()



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
        f"&modality=Auction&sub_modality=DayAhead&data_mode=table&product=60"
    )
    print(f"🔗 URL utilisée : {url}")

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    # 💾 Archive HTML
    html_path = f"archives/html/epex_FR_{delivery_date}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"📄 Page HTML archivée : {html_path}")


if __name__ == "__main__":
    fetch_epex_prices()
'''
