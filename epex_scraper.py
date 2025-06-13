import datetime
import requests
import pandas as pd

def fetch_epex_prices():
    delivery_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    url = (
        f"https://www.epexspot.com/api/marketdata"
        f"?deliveryDate={delivery_date}"
        f"&marketArea=FR"
        f"&auctionCategory=MRC"
        f"&modality=Auction"
        f"&subModality=DayAhead"
        f"&dataMode=table"
    )

    response = requests.get(url)
    data = response.json()

    rows = data.get("data", {}).get("rows", [])
    parsed = []

    for row in rows:
        hour = row.get("local_time")
        price = row.get("price")
        if hour and price is not None:
            parsed.append({"hour": hour, "price_eur_mwh": float(price)})

    if parsed:
        df = pd.DataFrame(parsed)
        df.to_csv(f"epex_FR_{delivery_date}.csv", index=False)
        print(f"Saved: epex_FR_{delivery_date}.csv")
    else:
        print("No data found.")

if __name__ == "__main__":
    fetch_epex_prices()
