import os, utils, json, datetime as dt, csv, io
from firecrawl import FirecrawlApp
import requests

def run(portal):
    print(f"Running Firecrawl scraper for {portal['id']}...")

    if portal["id"] == "privacy_rights":
        # The Privacy Rights Clearinghouse website now uses Tableau visualizations
        # and offers sample data for download. We'll download the sample CSV file.
        sample_csv_url = "https://cdn.shopify.com/s/files/1/0571/5489/5955/files/Data_Breach_Chronology_sample.csv?v=1737963802"

        try:
            # Download the sample CSV file
            response = requests.get(sample_csv_url, timeout=30)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Parse the CSV data
            csv_data = response.text
            reader = csv.DictReader(io.StringIO(csv_data))

            # Process each row in the CSV
            count = 0
            for row in reader:
                # Map CSV fields to our database schema
                breach_data = {
                    "entity": row.get("organization_name", ""),
                    "breach_date": row.get("breach_date", ""),
                    "notice_date": row.get("reported_date", ""),
                    "records": int(row.get("total_affected", "0").replace(",", "") or 0),
                    "breach_type": row.get("breach_type", ""),
                    "entity_type": row.get("organization_type", ""),
                    "state": row.get("state", ""),
                    "notice_url": row.get("notification_url", ""),
                    "_portal": portal["id"],
                    "raw": json.dumps(row)  # Store the original row data
                }

                utils.insert_row(breach_data)
                count += 1

            print(f"Inserted {count} records from {portal['id']} sample CSV")

        except Exception as e:
            print(f"Error processing Privacy Rights Clearinghouse data: {str(e)}")

            # Fallback to the old method if the CSV download fails
            try:
                # Initialize the FirecrawlApp with the API key
                api_key = os.environ.get("FIRECRAWL_API_KEY")
                if not api_key:
                    raise ValueError("FIRECRAWL_API_KEY environment variable is not set")

                app = FirecrawlApp(api_key=api_key)

                # Scrape the Privacy Rights Clearinghouse data breaches page
                app.scrape_url(
                    url=portal["url"],
                    formats=["html"],
                    only_main_content=True
                )

                # Extract structured data using the extract method
                extract_config = {
                    "prompt": "Extract all data breach records from the page. Look for any tables, visualizations, or structured data about breaches. Each record should include the organization name, breach date, date made public, number of records, type of breach, organization type, state, and source URL if available.",
                    "system_prompt": "You are a data extraction specialist. Extract structured data from the Privacy Rights Clearinghouse data breach database. Be precise and thorough. The data may be in Tableau visualizations or other formats.",
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity": {"type": "string"},
                                "breach_date": {"type": "string"},
                                "notice_date": {"type": "string"},
                                "records": {"type": "integer"},
                                "breach_type": {"type": "string"},
                                "entity_type": {"type": "string"},
                                "state": {"type": "string"},
                                "notice_url": {"type": "string"}
                            },
                            "required": ["entity", "breach_date", "notice_date", "records", "breach_type", "entity_type", "state"]
                        }
                    }
                }

                extracted = app.extract(
                    urls=[portal["url"]],
                    prompt=extract_config["prompt"],
                    system_prompt=extract_config["system_prompt"],
                    schema=extract_config["schema"]
                )

                # Process the extracted data
                if extracted and len(extracted) > 0:
                    breaches = extracted[0].get("data", [])
                    for breach in breaches:
                        row = {
                            "entity": breach.get("entity", ""),
                            "breach_date": breach.get("breach_date", ""),
                            "notice_date": breach.get("notice_date", ""),
                            "records": breach.get("records", 0),
                            "breach_type": breach.get("breach_type", ""),
                            "entity_type": breach.get("entity_type", ""),
                            "state": breach.get("state", ""),
                            "notice_url": breach.get("notice_url", ""),
                            "_portal": portal["id"]
                        }
                        utils.insert_row(row)
                    print(f"Inserted {len(breaches)} records from {portal['id']} using fallback method")
                else:
                    print(f"No data extracted from {portal['id']} using fallback method")
            except Exception as e2:
                print(f"Fallback method also failed for Privacy Rights Clearinghouse: {str(e2)}")
    else:
        # For other sites that might use Firecrawl in the future
        try:
            # Initialize the FirecrawlApp with the API key
            api_key = os.environ.get("FIRECRAWL_API_KEY")
            if not api_key:
                raise ValueError("FIRECRAWL_API_KEY environment variable is not set")

            app = FirecrawlApp(api_key=api_key)

            # Scrape the URL
            app.scrape_url(
                url=portal["url"],
                formats=["html"],
                only_main_content=True
            )

            # Process the result based on the portal's specific requirements
            # This is a placeholder for future implementations
            print(f"Generic Firecrawl scraper for {portal['id']} not yet implemented")
        except Exception as e:
            print(f"Error in generic Firecrawl scraper for {portal['id']}: {str(e)}")
