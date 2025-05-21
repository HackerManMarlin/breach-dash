import csv, hashlib, io, json, requests, datetime as dt
from . import utils

def run(portal):
    print(f"Fetching CSV for portal: {portal['id']} from URL: {portal['url']}")
    try:
        response = requests.get(portal["url"], timeout=30)
        response.raise_for_status()  # Raise an exception for HTTP errors
        text = response.text
        print(f"Successfully fetched CSV for {portal['id']}. Content length: {len(text)}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching CSV for {portal['id']}: {e}")
        return # Stop processing this portal if fetch fails

    reader = csv.DictReader(io.StringIO(text))
    rows_processed = 0
    for row in reader:
        row["_portal"] = portal["id"]
        # Ensure 'Individuals Affected' exists or provide a default before stripping commas
        individuals_affected_str = row.get("Individuals Affected", "0")
        if individuals_affected_str is None or individuals_affected_str.strip() == "": # Handle None or empty string
            individuals_affected_str = "0"
        row["records"]  = int(individuals_affected_str.replace(",", ""))
        # Log a more specific field if available, like 'Name of Covered Entity' for HHS
        entity_name = row.get('Name of Covered Entity', row.get('entity', 'Unknown Entity')) # Try common entity fields
        print(f"Processing row for {portal['id']}: {entity_name}")
        utils.insert_row(row)
        rows_processed += 1
    print(f"Finished processing {portal['id']}. Total rows processed: {rows_processed}")
