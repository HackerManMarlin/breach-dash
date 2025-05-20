import requests, os, utils, time, hashlib, json

def run(portal):
    res = requests.post(
        f"https://api.apify.com/v2/acts/{portal['actor']}/runs?token={os.getenv('APIFY_TOKEN')}",
        json={"memory":1024,"timeout":1200,"input":{}}
    ).json()
    # wait for run to finish (simplest path)
    run_id = res["data"]["id"]
    while True:
        r = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}?token={os.getenv('APIFY_TOKEN')}").json()
        if r["data"]["status"] in ("SUCCEEDED","FAILED"): break
        time.sleep(10)
    if r["data"]["status"] != "SUCCEEDED": return
    items = requests.get(f"https://api.apify.com/v2/datasets/{r['data']['defaultDatasetId']}/items?clean=true").json()
    for row in items: utils.insert_row(row)
