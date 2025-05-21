import os, json, datetime as dt
from . import utils
from firecrawl_mcp import firecrawl_scrape, firecrawl_extract

def run(portal):
    print(f"Running Firecrawl scraper for {portal['id']}...")
    
    if portal["id"] == "privacy_rights":
        # Scrape the Privacy Rights Clearinghouse data breaches page
        result = firecrawl_scrape(
            url=portal["url"],
            formats=["html"],
            onlyMainContent=True
        )
        
        # Extract structured data from the page
        extracted = firecrawl_extract(
            urls=[portal["url"]],
            prompt="Extract all data breach records from the table. Each record should include the organization name, breach date, date made public, number of records, type of breach, organization type, state, and source URL if available.",
            systemPrompt="You are a data extraction specialist. Extract structured data from the Privacy Rights Clearinghouse data breach database table. Be precise and thorough.",
            schema={
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
            print(f"Inserted {len(breaches)} records from {portal['id']}")
        else:
            print(f"No data extracted from {portal['id']}")
    else:
        # For other sites that might use Firecrawl in the future
        result = firecrawl_scrape(
            url=portal["url"],
            formats=["html"],
            onlyMainContent=True
        )
        
        # Process the result based on the portal's specific requirements
        # This is a placeholder for future implementations
        print(f"Generic Firecrawl scraper for {portal['id']} not yet implemented")
