from selectolax.parser import HTMLParser
import requests, hashlib, json, datetime as dt
from . import utils

def run(portal):
    response_text = None
    try:
        # Try with SSL verification first
        print(f"Fetching HTML for {portal['id']} from {portal[\'url\']} with SSL verification...")
        response = requests.get(portal["url"], timeout=30, verify=True)
        response.raise_for_status()
        response_text = response.text
        print(f"Successfully fetched HTML for {portal['id']} with SSL verification.")
    except requests.exceptions.SSLError as ssl_err:
        print(f"Warning: SSL verification failed for {portal[\'url\']}: {ssl_err}. Retrying with verify=False.")
        try:
            response = requests.get(portal["url"], timeout=30, verify=False)
            response.raise_for_status()
            response_text = response.text
            print(f"Successfully fetched HTML for {portal['id']} without SSL verification.")
        except requests.exceptions.RequestException as e_no_verify:
            print(f"Error fetching HTML for {portal['id']} from {portal[\'url\']} (even without SSL verify): {e_no_verify}")
            return # Stop processing this portal if fetch fails
    except requests.exceptions.RequestException as e:
        print(f"Error fetching HTML for {portal['id']} from {portal[\'url\']}: {e}")
        return # Stop processing this portal if fetch fails

    if response_text is None:
        print(f"Error: Failed to get response text for {portal['id']}")
        return

    html = HTMLParser(response_text)
    for tr in html.css(portal["selector"]):
        cols = [c.text(strip=True) for c in tr.css("td")]
        if portal["id"] == "privacy_rights":
            # PRC: entity, breach_date, notice_date, records, breach_type, entity_type, state, notice_url
            if len(cols) < 8: continue
            row = {
                "entity": cols[0],
                "breach_date": cols[1],
                "notice_date": cols[2],
                "records": int(cols[3].replace(",", "") or 0),
                "breach_type": cols[4],
                "entity_type": cols[5],
                "state": cols[6],
                "notice_url": tr.css_first("a")['href'] if tr.css_first("a") else None,
                "_portal": portal["id"]
            }
        else:
            if len(cols) < 3: continue
            parsed_records = 0 # Default
            if len(cols) > 2: # Check if cols[2] exists
                try:
                    records_str = cols[2].replace(",", "").strip()
                    if records_str: # Check if not empty
                        parsed_records = int(records_str)
                except ValueError:
                    print(f"Warning: Could not parse records from '{cols[2]}' for {portal['id']}. Using 0.")
            
            row = {
                "notice_date": cols[0] if len(cols) > 0 else "",
                "entity": cols[1] if len(cols) > 1 else "",
                "records": parsed_records,
                "_portal": portal["id"]
            }
        utils.insert_row(row)
