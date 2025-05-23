import os, utils, datetime as dt
from firecrawl import FirecrawlApp

def run(portal):
    print(f"Running Firecrawl scraper for {portal['id']}...")

    if portal["id"] == "privacy_rights":
        # The Privacy Rights Clearinghouse website now uses Tableau visualizations
        # We need to use a different approach to extract the data

        # For now, we'll use the historical data available on Tableau Public
        # This is a temporary solution until we implement a proper Tableau scraper
        tableau_url = "https://public.tableau.com/views/DataBreachChronologyFeatures/Above-the-ScrollSummaryMULTILAYOUT"

        try:
            # Initialize the FirecrawlApp with the API key
            api_key = os.environ.get("FIRECRAWL_API_KEY")
            if not api_key:
                raise ValueError("FIRECRAWL_API_KEY environment variable is not set")

            app = FirecrawlApp(api_key=api_key)

            # Use Firecrawl to extract data from the Tableau visualization
            # This will use AI to interpret the visualization and extract structured data
            extract_config = {
                "prompt": "Extract all data breach records from the Tableau visualization. Each record should include the organization name, breach date, date made public, number of records, type of breach, organization type, state, and source URL if available. The data is in a Tableau visualization titled 'Data Breach Chronology'.",
                "system_prompt": "You are a data extraction specialist. Extract structured data from the Privacy Rights Clearinghouse data breach database Tableau visualization. Be precise and thorough. Focus on extracting the most recent breach records shown in the visualization.",
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
                urls=[tableau_url],
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
                print(f"Inserted {len(breaches)} records from {portal['id']} Tableau visualization")
            else:
                print(f"No data extracted from {portal['id']} Tableau visualization")

                # If extraction fails, try to use the deep research capability
                try:
                    print("Attempting deep research on Privacy Rights Clearinghouse data breaches...")

                    # Use Firecrawl's deep research capability to find and extract breach data
                    research_results = app.deep_research(
                        query="Extract the most recent data breaches from Privacy Rights Clearinghouse",
                        max_depth=3,
                        time_limit=180,
                        max_urls=10
                    )

                    if research_results and research_results.get("finalAnalysis"):
                        # Extract structured data from the research results
                        analysis = research_results.get("finalAnalysis", "")

                        # Use the extract method to parse the analysis into structured data
                        structured_data = app.extract(
                            text=analysis,
                            prompt="Extract all data breach records mentioned in the text. Each record should include the organization name, breach date, date made public, number of records, type of breach, organization type, state, and source URL if available.",
                            system_prompt="You are a data extraction specialist. Extract structured data about data breaches from the provided text. Be precise and thorough.",
                            schema=extract_config["schema"]
                        )

                        if structured_data and len(structured_data) > 0:
                            breaches = structured_data[0].get("data", [])
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
                            print(f"Inserted {len(breaches)} records from {portal['id']} using deep research")
                        else:
                            print(f"No structured data extracted from deep research results")
                    else:
                        print(f"Deep research did not yield useful results")
                except Exception as e3:
                    print(f"Deep research method failed for Privacy Rights Clearinghouse: {str(e3)}")
        except Exception as e:
            print(f"Error processing Privacy Rights Clearinghouse data: {str(e)}")
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
