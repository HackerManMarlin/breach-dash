import csv, hashlib, io, json, requests, datetime as dt, utils

def run(portal):
    text = requests.get(portal["url"], timeout=30).text
    for row in csv.DictReader(io.StringIO(text)):
        row["_portal"] = portal["id"]
        row["records"]  = int(row.get("Individuals Affected", "0").replace(",", "") or 0)
        utils.insert_row(row)
