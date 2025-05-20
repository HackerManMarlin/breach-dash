import hashlib, json, os, requests, datetime as dt

SUPA = os.environ["SUPABASE_URL"]
KEY  = os.environ["SUPABASE_KEY"]
HDR  = {"apikey":KEY, "Authorization":f"Bearer {KEY}"}

def insert_row(row):
    row["hash"] = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
    row["ingested_at"] = dt.datetime.utcnow().isoformat()

    # exact-once insert
    r = requests.post(f"{SUPA}/rest/v1/breach_raw?on_conflict=hash", headers=HDR,
                      json=[row], params={"select":"hash"})
    if not r.ok:
        print("supabase error", r.text)
    else:
        print(f"Successfully inserted breach: {row.get('entity', 'Unknown entity')}")
