import pandas as pd
import numpy as np
from typing import List, Dict, Any
import json
from csv import DictWriter
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Process trades and historical quotes.")
    parser.add_argument('-t', '--trades', required=True, help='Path to the trades CSV file')
    parser.add_argument('-q', '--quotes', required=True, help='Path to the historical quotes CSV file')
    parser.add_argument('-o', '--out', help='Path to the output CSV file (optional)')

    args = parser.parse_args()

    try:
        historical = pd.read_csv(args.quotes)
    except Exception as e:
        print(f"Error reading historical quotes file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        trades = pd.read_csv(args.trades)
    except Exception as e:
        print(f"Error reading trades file: {e}", file=sys.stderr)
        sys.exit(1)

    reformed = process_rows(trades, historical)

    if args.out:
        with open(args.out, mode="w") as f:
            write_output(reformed, f)
    write_output(reformed, sys.stdout)

def process_rows(rows: pd.DataFrame, historical: pd.DataFrame) -> List[Dict[str, Any]]:
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
            print("cannot happen", file=sys.stderr)
            sys.exit(1)
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
                print(f"Could not find the asset value for {tx['pair']} on {tx['date']}", file=sys.stderr)
                sys.exit(1)

            p0_record = {"type": p0_action, "ticker symbol": tx["pair"][0], "shares": p0_amount, "exchange rate": p0_price, "date": tx["date"]}
            p1_record = {"type": p1_action, "ticker symbol": tx["pair"][1], "shares": p1_amount, "exchange rate": p1_price, "date": tx["date"]}
            reformed.append(p0_record)
            reformed.append(p1_record)

    for tx in reformed:
        tx["value"] = tx["exchange rate"] * tx["shares"]

    return reformed

def write_output(reformed: List[Dict[str, Any]], output):
    w = DictWriter(output, reformed[0].keys())
    w.writeheader()
    w.writerows(reformed)

def clean_number(num_str):
    return float(num_str.replace(',', ''))

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
    if local is not None:
        return local
    else:
        print(f"Asset value not found for {asset} on {date}. Please update the --quotes file.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
