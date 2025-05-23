import os, utils, json, requests, subprocess, tempfile

def run(portal):
    """
    Scraper for Tableau visualizations using Puppeteer to extract live data.
    This is compatible with GitHub Actions and doesn't require Firecrawl.
    """
    print(f"Running Tableau scraper for {portal['id']}...")

    if portal["id"] == "privacy_rights":
        # The Privacy Rights Clearinghouse website uses Tableau visualizations
        # We'll use Puppeteer to extract data from the visualization

        try:
            # Create a temporary JavaScript file for Puppeteer
            with tempfile.NamedTemporaryFile(suffix='.js', delete=False, mode='w') as f:
                js_content = """
                const puppeteer = require('puppeteer');

                (async () => {
                    // Launch the browser
                    const browser = await puppeteer.launch({
                        headless: true,
                        args: ['--no-sandbox', '--disable-setuid-sandbox']
                    });

                    try {
                        // Open a new page
                        const page = await browser.newPage();

                        // Navigate to the Tableau Public page that has the "Download" button
                        // This is the page that shows the data breach chronology
                        await page.goto('https://public.tableau.com/app/profile/privacy.rights.clearinghouse/viz/DataBreachChronologyFeatures/DataBreachChronology', {
                            waitUntil: 'networkidle2',
                            timeout: 60000
                        });

                        console.log('Page loaded');

                        // Wait for the visualization to load
                        await page.waitForSelector('canvas', { timeout: 60000 });

                        console.log('Canvas found');

                        // Wait a bit for the visualization to fully render
                        await page.waitForTimeout(5000);

                        // Find and click the "Download" button
                        const downloadButton = await page.waitForSelector('button[aria-label="Download"]', { timeout: 30000 });
                        await downloadButton.click();

                        console.log('Download button clicked');

                        // Wait for the download menu to appear and click "Data"
                        const dataOption = await page.waitForSelector('button[data-tb-test-id="DownloadData-Button"]', { timeout: 30000 });
                        await dataOption.click();

                        console.log('Data option clicked');

                        // Wait for the data dialog to appear
                        await page.waitForSelector('div[data-tb-test-id="DataDownloadDialog-Dialog"]', { timeout: 30000 });

                        // Click the "Full Data" tab
                        const fullDataTab = await page.waitForSelector('button[data-tb-test-id="FullDataTab"]', { timeout: 30000 });
                        await fullDataTab.click();

                        console.log('Full Data tab clicked');

                        // Wait for the data to load
                        await page.waitForTimeout(2000);

                        // Extract the data from the table
                        const data = await page.evaluate(() => {
                            const rows = Array.from(document.querySelectorAll('table.datatable tbody tr'));
                            const headers = Array.from(document.querySelectorAll('table.datatable thead th')).map(th => th.textContent.trim());

                            return rows.map(row => {
                                const cells = Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim());
                                const rowData = {};

                                headers.forEach((header, index) => {
                                    rowData[header] = cells[index] || '';
                                });

                                return rowData;
                            });
                        });

                        console.log('Data extracted:', JSON.stringify(data));

                        // Output the data as JSON
                        console.log('DATA_START');
                        console.log(JSON.stringify(data));
                        console.log('DATA_END');

                    } catch (error) {
                        console.error('Error:', error);
                    } finally {
                        // Close the browser
                        await browser.close();
                    }
                })();
                """
                f.write(js_content)
                js_file_path = f.name

            print(f"Created temporary JavaScript file: {js_file_path}")

            # Run the Puppeteer script
            try:
                # Check if we're running in GitHub Actions
                is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'

                # Set up the command to run the Puppeteer script
                if is_github_actions:
                    # In GitHub Actions, Node.js and Puppeteer are pre-installed
                    cmd = ['node', js_file_path]
                else:
                    # Locally, we need to use npx to run Puppeteer
                    cmd = ['npx', 'puppeteer', 'run', js_file_path]

                # Run the command and capture the output
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()

                # Check if the process was successful
                if process.returncode != 0:
                    print(f"Error running Puppeteer script: {stderr}")
                    raise Exception(f"Puppeteer script failed with exit code {process.returncode}")

                # Extract the data from the output
                data_start = stdout.find('DATA_START')
                data_end = stdout.find('DATA_END')

                if data_start != -1 and data_end != -1:
                    data_json = stdout[data_start + len('DATA_START'):data_end].strip()
                    data = json.loads(data_json)

                    # Process the data
                    count = 0
                    for row in data:
                        # Map fields to our database schema
                        breach_data = {
                            "entity": row.get("Organization", ""),
                            "breach_date": row.get("Breach Date", ""),
                            "notice_date": row.get("Notice Date", ""),
                            "records": int(row.get("Records", "0").replace(",", "") or 0),
                            "breach_type": row.get("Type", ""),
                            "entity_type": row.get("Organization Type", ""),
                            "state": row.get("State", ""),
                            "notice_url": row.get("URL", ""),
                            "_portal": portal["id"],
                            "raw": json.dumps(row)  # Store the original row data
                        }

                        utils.insert_row(breach_data)
                        count += 1

                    print(f"Inserted {count} records from {portal['id']} live data")
                else:
                    print(f"Failed to extract data from Puppeteer output")
                    raise Exception("Data markers not found in Puppeteer output")

            except Exception as e:
                print(f"Error running Puppeteer script: {str(e)}")

                # Fallback to the sample CSV if Puppeteer fails
                print("Falling back to sample CSV data...")
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

                    print(f"Inserted {count} records from {portal['id']} sample CSV (fallback)")
                else:
                    print(f"Failed to get sample CSV data: {csv_response.status_code}")

            # Clean up the temporary file
            os.unlink(js_file_path)

        except Exception as e:
            print(f"Error processing Privacy Rights Clearinghouse Tableau data: {str(e)}")
    else:
        print(f"No Tableau scraper implemented for {portal['id']}")
