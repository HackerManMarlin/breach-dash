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
- `SLACK_WEBHOOK` (optional) - Your Slack incoming webhook URL

### 5. GitHub Pages (for Dashboard)

Enable GitHub Pages for your repository:
1. Go to repository Settings → Pages
2. Set Source to "Deploy from a branch"
3. Select the main branch and /dashboard folder
4. Save

Your dashboard will be available at `https://<username>.github.io/breach-dash/`

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
  - You can modify it in the Supabase dashboard under Edge Functions > enrich
  - Implement your preferred AI integration (e.g., OpenAI, Claude) in the Edge Function

## Cost

All compute is pay-as-you-go or free:
- GitHub Actions (public) – unlimited minutes
- Supabase – 500 MB DB, 5 GB egress
- Apify – 30 CU/month on starter plan
