import csv
import json

def process_csv(csv_filepath, json_filepath):
    breaches = []
    # Key fields to extract. Add more as needed.
    # We will try to parse 'total_affected' as an integer.
    # 'information_affected' is a JSON string within the CSV, so it needs special handling if we want to parse it.
    # For now, we'll skip deep parsing of 'information_affected' to keep it simple.
    relevant_fields = {
        "org_name": "org_name",
        "reported_date": "reported_date",
        "breach_date": "breach_date",
        "incident_details": "incident_details",
        "total_affected": "total_affected",
        "organization_type": "organization_type",
        "breach_type": "breach_type",
        "source_url": "source_url",
        "notification_url_original": "notification_url_original"
    }

    try:
        with open(csv_filepath, mode='r', encoding='utf-8') as csvfile:
            # Using DictReader to handle headers automatically
            # Specifying the pipe delimiter
            reader = csv.DictReader(csvfile, delimiter='|')
            for row_number, row in enumerate(reader):
                try:
                    breach_data = {}
                    for json_key, csv_header in relevant_fields.items():
                        value = row.get(csv_header, "").strip()
                        if csv_header == 'total_affected':
                            try:
                                # Convert to int, handle "UNKN" or empty strings
                                breach_data[json_key] = int(value) if value and value.upper() != "UNKN" else None
                            except ValueError:
                                breach_data[json_key] = None # Or some other placeholder like -1 or "Unknown"
                        else:
                            breach_data[json_key] = value if value and value.upper() != "UNKN" else None
                    
                    breaches.append(breach_data)
                except Exception as e:
                    print(f"Error processing row {row_number + 1}: {row}")
                    print(f"Error was: {e}")
                    # Optionally, skip the row or add partial data
                    continue
        
        with open(json_filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(breaches, jsonfile, indent=2)
        print(f"Successfully processed CSV and saved to {json_filepath}")

    except FileNotFoundError:
        print(f"Error: The file {csv_filepath} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    csv_input_path = "/workspace/breach-dash/scrapers/Data_Breach_Chronology_sample.csv"
    json_output_path = "/workspace/breach-dash/dashboard/data/privacyrights_breaches.json"
    process_csv(csv_input_path, json_output_path)
