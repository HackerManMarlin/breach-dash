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
        # Call the Edge Function to enrich the data with AI summaries
        try:
            enrich_url = f"{SUPA}/functions/v1/enrich"
            enrich_response = requests.post(enrich_url, headers=HDR, json=row)
            if not enrich_response.ok:
                print(f"enrich function error: {enrich_response.text}")
        except Exception as e:
            print(f"enrich function exception: {str(e)}")
