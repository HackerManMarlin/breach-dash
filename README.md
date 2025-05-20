# Breach Dashboard

A serverless data breach monitoring dashboard that collects information from various state and federal portals.

## Prerequisites

- GitHub account (public repos) - Actions minutes are unlimited and free on public repos
- Supabase project (Free plan) - 500 MB Postgres + Edge Functions + 5 GB egress per month
- Apify account (Starter = free 30 Compute-Units ≈ 20 browser-hours) - Runs Playwright for JS-heavy portals
- (optional) Slack incoming-webhook URL - To get "≥ 2,500 records" alerts

## Setup Instructions

### 1. Repository Setup

The repository structure is already set up with the following components:
- `scrapers/` - Python scripts for data collection
- `dashboard/` - Simple HTML dashboard
- `.github/workflows/` - GitHub Actions workflow
- `supabase/` - Supabase setup files

### 2. Supabase Setup (Using MCP)

1. Create a free Supabase project (or use an existing one)
2. Note your SUPABASE_URL and service role key (SUPABASE_KEY)
3. The database tables and Edge Functions have been set up automatically using Supabase MCP
4. If you want to modify the Slack notification settings:
   - Go to the SQL Editor in your Supabase dashboard
   - Modify the `notify_big` function to update the webhook URL or threshold

### 3. Apify Setup (for JS-heavy portals)

For portals that require JavaScript rendering (Texas, Oregon, etc.):

1. Create an Apify account
2. Create a new Actor from the Playwright Crawler template
3. Configure it with the appropriate URL and extraction logic
4. Update the `actor` field in `config.yaml` with your actor ID

### 4. GitHub Secrets

Add the following secrets to your GitHub repository:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase service role key
- `APIFY_TOKEN` - Your Apify API token
- `FIRECRAWL_API_KEY` - Your Firecrawl API key for web research
- `SLACK_WEBHOOK` (optional) - Your Slack incoming webhook URL

### 5. GitHub Pages (for Dashboard)

The dashboard is already set up on the gh-pages branch. To enable GitHub Pages:
1. Go to repository Settings → Pages
2. Set Source to "Deploy from a branch"
3. Select the gh-pages branch and / (root) folder
4. Save

Your dashboard will be available at `https://<username>.github.io/breach-dash/`

If you need to update the dashboard:
1. Make changes to the dashboard/index.html file in the main branch
2. Run the following commands to update the gh-pages branch:
   ```bash
   git checkout gh-pages
   git checkout main -- dashboard/index.html
   mv dashboard/index.html .
   git rm -rf dashboard
   git add .
   git commit -m "Update dashboard"
   git push origin gh-pages
   git checkout main
   ```

## How It Works

1. GitHub Actions runs the scraper every 15 minutes
2. Data is collected from various portals (CSV, HTML, JS-heavy sites via Apify)
3. New records are inserted into Supabase
4. The dashboard displays the latest breaches
5. Optional Slack notifications for large breaches (≥ 2,500 records)

## Customization

- Add more portals by updating `scrapers/config.yaml`
- Modify the dashboard in `dashboard/index.html`
- The Edge Function for AI summaries is already set up
  - Uses Firecrawl for web research on breaches
  - Generates comprehensive summaries with impact assessments and recommendations
  - Provides sources for further investigation

### AI-Powered Features

The dashboard now includes advanced AI features:

1. **Web Research**: Automatically searches the web for information about each breach
2. **Impact Assessment**: Analyzes the severity and potential impact of the breach
3. **Personalized Recommendations**: Provides specific recommendations based on breach type
4. **Source Tracking**: Lists sources used in the research for verification
5. **Interactive Dashboard**: Filter breaches by severity, portal, or search terms

## Troubleshooting

### No Data in Dashboard
If your dashboard shows "No breach data available", check the following:

1. **GitHub Actions**: Make sure the GitHub Actions workflow has run successfully
   - Go to the Actions tab in your repository
   - Check if the scrape workflow has run and completed successfully
   - If there are errors, fix them and re-run the workflow

2. **Supabase Connection**: Check if the dashboard can connect to Supabase
   - Open the dashboard and click on "Debug Information"
   - Check the Connection Status and Raw Data Count
   - If there's a connection error, verify your Supabase URL and anon key

3. **Sample Data**: You can add sample data directly to Supabase
   - Go to the Supabase dashboard → Table Editor → breach_raw
   - Click "Insert row" and add some sample data
   - Refresh your dashboard to see if the data appears

### GitHub Pages Not Working
If your GitHub Pages site is not available:

1. Go to repository Settings → Pages
2. Make sure the Source is set to "Deploy from a branch"
3. Select the gh-pages branch and / (root) folder
4. Check the "GitHub Pages" section for any error messages
5. Wait a few minutes for the site to be published

## Cost

All compute is pay-as-you-go or free:
- GitHub Actions (public) – unlimited minutes
- Supabase – 500 MB DB, 5 GB egress
- Apify – 30 CU/month on starter plan
