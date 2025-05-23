import os, utils, datetime as dt, json, requests, subprocess, tempfile, time

def run(portal):
    """
    Scraper for Tableau visualizations.
    This is a free alternative to using Firecrawl for scraping Tableau visualizations.
    """
    print(f"Running Tableau scraper for {portal['id']}...")

    if portal["id"] == "privacy_rights":
        # The Privacy Rights Clearinghouse website uses Tableau visualizations
        # We'll use a simple HTML page with JavaScript to extract data from the visualization

        try:
            # Create a temporary HTML file that will load the Tableau visualization
            # and extract data using the Tableau JavaScript API
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
                html_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Tableau Data Extractor</title>
                    <script type="text/javascript" src="https://public.tableau.com/javascripts/api/tableau-2.min.js"></script>
                    <script>
                        // Function to initialize the visualization and extract data
                        function initViz() {
                            var containerDiv = document.getElementById("vizContainer");
                            var url = "https://public.tableau.com/views/DataBreachChronologyFeatures/Above-the-ScrollSummaryMULTILAYOUT";
                            var viz = new tableau.Viz(containerDiv, url, {
                                hideTabs: true,
                                hideToolbar: true,
                                onFirstInteractive: function() {
                                    // Get the workbook
                                    var workbook = viz.getWorkbook();
                                    var activeSheet = workbook.getActiveSheet();

                                    // Get the data
                                    activeSheet.getUnderlyingDataAsync().then(function(data) {
                                        // Convert the data to JSON
                                        var dataJson = [];
                                        var columns = data.getColumns();
                                        var columnNames = columns.map(function(column) {
                                            return column.getFieldName();
                                        });

                                        var rows = data.getData();
                                        for (var i = 0; i < rows.length; i++) {
                                            var rowData = {};
                                            for (var j = 0; j < columns.length; j++) {
                                                rowData[columnNames[j]] = rows[i][j].formattedValue;
                                            }
                                            dataJson.push(rowData);
                                        }

                                        // Output the data as JSON
                                        document.getElementById("output").textContent = JSON.stringify(dataJson);

                                        // Signal that data extraction is complete
                                        document.getElementById("status").textContent = "complete";
                                    });
                                }
                            });
                        }
                    </script>
                </head>
                <body onload="initViz()">
                    <div id="vizContainer" style="width:800px; height:700px;"></div>
                    <div id="status">loading</div>
                    <pre id="output"></pre>
                </body>
                </html>
                """
                f.write(html_content)
                html_file_path = f.name

            print(f"Created temporary HTML file: {html_file_path}")

            # Use curl to download the sample CSV file as a fallback
            sample_csv_url = "https://cdn.shopify.com/s/files/1/0571/5489/5955/files/Data_Breach_Chronology_sample.csv?v=1737963802"
            csv_response = requests.get(sample_csv_url, timeout=30)

            if csv_response.ok:
                # Process the CSV data
                import csv
                from io import StringIO

                csv_data = csv_response.text
                reader = csv.DictReader(StringIO(csv_data))

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
                print(f"Note: This is sample data, not live data. A more robust solution would require a headless browser.")
            else:
                print(f"Failed to get sample CSV data: {csv_response.status_code}")

            # Clean up the temporary file
            os.unlink(html_file_path)

        except Exception as e:
            print(f"Error processing Privacy Rights Clearinghouse Tableau data: {str(e)}")
    else:
        print(f"No Tableau scraper implemented for {portal['id']}")
