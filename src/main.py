import pandas as pd
import numpy as np
from typing import List, Dict, Any
import requests
import json
from csv import DictWriter

def main():
    historical = pd.read_csv("All_historical_Quotes.csv")
    trades = pd.read_csv("trades.csv")

    process_rows(trades, historical)

def process_rows(rows: pd.DataFrame, historical: pd.DataFrame):
    txs = {}
    for index, row in rows.iterrows():
        pair = row["pair"].split("/")
        date = row["time"].split(" ")[0]
        price = row["price"]
        vol = row["vol"]
        txid = row["ordertxid"]

        if txid in txs:
            txs[txid]["vol"] += vol
        else:
            txs[txid] = {
                "date": date,
                "pair": pair,
                "price": price,
                "vol": vol,
                "cost": row["cost"],
                "id": txid,
                "type": row["type"]
            }
    txs = txs.values()

    reformed = []
    for tx in txs:
        if tx["pair"][0] == "EUR":
            print("cannot happen")
            exit(1)
        elif tx["pair"][1] == "EUR":
            record = {"type": tx["type"], "ticker symbol": tx["pair"][0], "shares": tx["vol"], "exchange rate": tx["price"], "date": tx["date"]}
            reformed.append(record)
        else:
            p0_price = get_asset_value(historical, tx["date"], tx["pair"][0])
            p0_amount = tx["vol"]
            p0_action = tx["type"]
            p1_price = get_asset_value(historical, tx["date"], tx["pair"][1])
            p1_amount = tx["cost"]
            p1_action = "buy" if p0_action == "sell" else "sell"

            if p0_price == 0 or p1_price == 0:
                print("Could not find the asset value for {} on {}".format(tx["bought"], tx["date"]))
                exit(1)

            p0_record = {"type": p0_action, "ticker symbol": tx["pair"][0], "shares": p0_amount, "exchange rate": p0_price, "date": tx["date"]}
            p1_record = {"type": p1_action, "ticker symbol": tx["pair"][1], "shares": p1_amount, "exchange rate": p1_price, "date": tx["date"]}
            reformed.append(p0_record)
            reformed.append(p1_record)

    for t in reformed:
        print(t)

    for tx in reformed:
        tx["value"] = tx["exchange rate"] * tx["shares"]

    w = DictWriter(open("out.pp.csv", mode="w"), reformed[0].keys())
    w.writeheader()
    w.writerows(reformed)


def clean_number(num_str):
    return float(num_str.replace(',', ''))

base_url = "https://api.kraken.com/0/public/OHLC"
payload = {}
headers = {
    'Accept': 'application/json'
}
cache = {}

def get_asset_value_remote(date: str, asset: str):
    print("Date not found in the historical data {} {}".format(date, asset))
    ts = pd.to_datetime(date).timestamp()
    pair = "{}EUR".format(asset)
    query = "{}?pair={}&since={}&interval=1440".format(base_url, pair, int(ts - 10000))
    print(int(ts), query)
    response = requests.request("GET", query, headers=headers, data=payload)

    response_data = json.loads(response.text)

    target_date = pd.to_datetime(date)

    for item in response_data['result'][pair]:
        item_timestamp = item[0]
        item_date = pd.to_datetime(item_timestamp, unit='s')

        print(item_date.date(), target_date.date())
        if item_date.date() == target_date.date():
            return float(item[1])

    print("No matching date found in the response.")
    return None

def get_asset_value_local(historical: pd.DataFrame, date: str, asset: str):
    row = historical.loc[historical['Date'] == date]
    if row.empty:
        return None

    value = row[asset].values[0]
    if type(value) == str:
        value = clean_number(value)

    if value != value:
        return None

    return float(value)

def get_asset_value(historical: pd.DataFrame, date: str, asset: str):
    local = get_asset_value_local(historical, date, asset)
    if local != None:
        return local
    else:
        print(asset, date)
        exit(1)
        remote = get_asset_value_remote(date, asset)
        if remote != None:
            return remote
        else:
            print("Could not find the asset value for {} on {}".format(asset, date))
            return exit(1)


if __name__ == "__main__":
    main()
