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
                const https = require('https');

                // Function to download data directly using Node.js https module
                function downloadCSV(url) {
                    return new Promise((resolve, reject) => {
                        https.get(url, (response) => {
                            if (response.statusCode !== 200) {
                                reject(new Error(`Failed to download CSV: ${response.statusCode}`));
                                return;
                            }

                            let data = '';
                            response.on('data', (chunk) => {
                                data += chunk;
                            });

                            response.on('end', () => {
                                resolve(data);
                            });
                        }).on('error', (err) => {
                            reject(err);
                        });
                    });
                }

                // Function to parse CSV data
                function parseCSV(csvText) {
                    const lines = csvText.split('\\n');
                    if (lines.length < 2) {
                        return [];
                    }

                    // Parse headers
                    const headers = lines[0].split(',').map(header =>
                        header.trim().replace(/^"(.*)"$/, '$1')
                    );

                    // Parse data rows
                    const results = [];
                    for (let i = 1; i < lines.length; i++) {
                        const line = lines[i].trim();
                        if (!line) continue;

                        // Simple CSV parsing (doesn't handle all edge cases but works for basic CSV)
                        const values = line.split(',').map(value =>
                            value.trim().replace(/^"(.*)"$/, '$1')
                        );

                        const row = {};
                        headers.forEach((header, index) => {
                            if (index < values.length) {
                                row[header] = values[index];
                            }
                        });

                        results.push(row);
                    }

                    return results;
                }

                (async () => {
                    try {
                        console.log('Starting Privacy Rights Clearinghouse data extraction');

                        // Try direct download first - this is the most reliable method
                        try {
                            // This URL pattern works for many Tableau Public visualizations
                            const csvUrl = 'https://public.tableau.com/views/DataBreachChronologyFeatures/DataBreachChronology.csv';
                            console.log('Attempting direct CSV download from:', csvUrl);

                            const csvData = await downloadCSV(csvUrl);
                            console.log('CSV downloaded successfully, length:', csvData.length);

                            if (csvData && csvData.length > 0) {
                                const parsedData = parseCSV(csvData);
                                console.log('Parsed CSV data, row count:', parsedData.length);

                                if (parsedData.length > 0) {
                                    console.log('DATA_START');
                                    console.log(JSON.stringify(parsedData));
                                    console.log('DATA_END');
                                    return;
                                }
                            }
                        } catch (directDownloadError) {
                            console.error('Direct CSV download failed:', directDownloadError.message);
                        }

                        // If direct download fails, try using a browser
                        console.log('Falling back to browser-based extraction');
                        const browser = await puppeteer.launch({
                            headless: true,
                            args: ['--no-sandbox', '--disable-setuid-sandbox']
                        });

                        const page = await browser.newPage();

                        // Try to download the CSV using the browser
                        await page.goto('https://public.tableau.com/views/DataBreachChronologyFeatures/DataBreachChronology.csv', {
                            waitUntil: 'networkidle2',
                            timeout: 60000
                        });

                        // Get the page content (should be CSV)
                        const content = await page.content();
                        const csvMatch = content.match(/<pre[^>]*>(.*?)<\\/pre>/s);

                        if (csvMatch && csvMatch[1]) {
                            const csvData = csvMatch[1];
                            console.log('CSV extracted from browser, length:', csvData.length);

                            const parsedData = parseCSV(csvData);
                            console.log('Parsed CSV data, row count:', parsedData.length);

                            if (parsedData.length > 0) {
                                console.log('DATA_START');
                                console.log(JSON.stringify(parsedData));
                                console.log('DATA_END');
                            } else {
                                console.error('Failed to parse CSV data');
                            }
                        } else {
                            console.error('Failed to extract CSV from browser response');
                        }

                        await browser.close();
                    } catch (error) {
                        console.error('Error in data extraction:', error);
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

                # Print the output for debugging
                print("Puppeteer stdout:")
                print(stdout)
                print("Puppeteer stderr:")
                print(stderr)

                # Check if the process was successful
                if process.returncode != 0:
                    print(f"Error running Puppeteer script: {stderr}")
                    raise Exception(f"Puppeteer script failed with exit code {process.returncode}")

                # Extract the data from the output
                data_start = stdout.find('DATA_START')
                data_end = stdout.find('DATA_END')

                if data_start != -1 and data_end != -1:
                    data_json = stdout[data_start + len('DATA_START'):data_end].strip()
                    print(f"Found data JSON: {data_json[:100]}...")  # Print the first 100 chars
                    data = json.loads(data_json)

                    # Process the data
                    count = 0
                    for row in data:
                        # Map fields to our database schema
                        # Note: Only include fields that exist in the database schema

                        # Handle date formatting - ensure it's in YYYY-MM-DD format
                        notice_date = row.get("Notice Date", "")
                        if notice_date and notice_date.strip():
                            # Try to parse and format the date
                            try:
                                # Handle various date formats
                                import re
                                from datetime import datetime

                                # Remove any time component
                                notice_date = notice_date.split()[0]

                                # Try to detect the format
                                if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', notice_date):
                                    # MM/DD/YYYY or M/D/YYYY format
                                    parts = notice_date.split('/')
                                    if len(parts) == 3:
                                        month, day, year = parts
                                        if len(year) == 2:
                                            year = '20' + year  # Assume 20xx for 2-digit years
                                        notice_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                elif re.match(r'^\d{1,2}-\d{1,2}-\d{2,4}$', notice_date):
                                    # MM-DD-YYYY or M-D-YYYY format
                                    parts = notice_date.split('-')
                                    if len(parts) == 3:
                                        month, day, year = parts
                                        if len(year) == 2:
                                            year = '20' + year  # Assume 20xx for 2-digit years
                                        notice_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                                # Validate the date format
                                datetime.strptime(notice_date, '%Y-%m-%d')
                            except Exception as e:
                                print(f"Error parsing date '{notice_date}': {str(e)}")
                                notice_date = None
                        else:
                            notice_date = None

                        breach_data = {
                            "entity": row.get("Organization", ""),
                            "records": int(row.get("Records", "0").replace(",", "") or 0),
                            "notice_url": row.get("URL", ""),
                            "_portal": portal["id"],
                            "raw": json.dumps(row)  # Store the original row data
                        }

                        # Only add notice_date if it's valid
                        if notice_date:
                            breach_data["notice_date"] = notice_date

                        utils.insert_row(breach_data)
                        count += 1

                    print(f"Inserted {count} records from {portal['id']} live data")
                else:
                    print(f"Failed to extract data from Puppeteer output")
                    print(f"stdout length: {len(stdout)}")
                    print(f"DATA_START index: {data_start}")
                    print(f"DATA_END index: {data_end}")
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
                        # Note: Only include fields that exist in the database schema

                        # Handle date formatting - ensure it's in YYYY-MM-DD format
                        notice_date = row.get("reported_date", "")
                        if notice_date and notice_date.strip():
                            # Try to parse and format the date
                            try:
                                # Handle various date formats
                                import re
                                from datetime import datetime

                                # Remove any time component
                                notice_date = notice_date.split()[0]

                                # Try to detect the format
                                if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', notice_date):
                                    # MM/DD/YYYY or M/D/YYYY format
                                    parts = notice_date.split('/')
                                    if len(parts) == 3:
                                        month, day, year = parts
                                        if len(year) == 2:
                                            year = '20' + year  # Assume 20xx for 2-digit years
                                        notice_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                elif re.match(r'^\d{1,2}-\d{1,2}-\d{2,4}$', notice_date):
                                    # MM-DD-YYYY or M-D-YYYY format
                                    parts = notice_date.split('-')
                                    if len(parts) == 3:
                                        month, day, year = parts
                                        if len(year) == 2:
                                            year = '20' + year  # Assume 20xx for 2-digit years
                                        notice_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                                # Validate the date format
                                datetime.strptime(notice_date, '%Y-%m-%d')
                            except Exception as e:
                                print(f"Error parsing date '{notice_date}': {str(e)}")
                                notice_date = None
                        else:
                            notice_date = None

                        breach_data = {
                            "entity": row.get("organization_name", ""),
                            "records": int(row.get("total_affected", "0").replace(",", "") or 0),
                            "notice_url": row.get("notification_url", ""),
                            "_portal": portal["id"],
                            "raw": json.dumps(row)  # Store the original row data
                        }

                        # Only add notice_date if it's valid
                        if notice_date:
                            breach_data["notice_date"] = notice_date

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
