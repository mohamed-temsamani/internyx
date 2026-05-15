# Internyx

Internyx is a Flask internship platform focused on internship opportunities in Morocco. It shows internship cards, detail pages, search, filters, saved internships, applications, and career path content in a beginner-friendly Flask project.

## What the Apify update script does

The script at `scripts/update_internships_apify.py` searches public internship listings related to Morocco using Apify, normalizes the results to match the existing `data/internships.json` format, classifies each internship, extracts skills, removes duplicates, and appends only new scraped internships without deleting your existing manual internships.

## 1. Create an Apify account

1. Go to `https://apify.com/`.
2. Create a free account.
3. Open your Apify console after signing in.

## 2. Get your Apify API token

1. In Apify, open `Settings`.
2. Find the `API & Integrations` or `API tokens` section.
3. Copy your API token.

## 3. Create your `.env` file

Copy `.env.example` to `.env` and update the values:

```bash
copy .env.example .env
```

Windows PowerShell alternative:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```env
APIFY_API_TOKEN=your_real_apify_token
APIFY_ACTOR_ID=apify/google-search-scraper
APIFY_MAX_RESULTS=10
SECRET_KEY=dev-only-change-me
```

`APIFY_ACTOR_ID` is optional. If you leave it blank, the script uses a public search actor by default.

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Run a small test scrape first

Start small so you do not waste Apify credits:

```bash
python scripts/update_internships_apify.py --limit 5 --dry-run
```

This will:

- read your `.env`
- call Apify
- normalize and deduplicate results
- show logs
- avoid writing to `data/internships.json`

## 6. Actually update `internships.json`

When the dry run looks good:

```bash
python scripts/update_internships_apify.py --limit 10
```

## 7. Run Flask

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

The app now reads the latest `data/internships.json` while Flask is running, so new internships should appear without relying on the old startup-only cache. If you do not see changes right away, refresh the page. If needed, restart Flask.

## 8. Schedule automatic updates

### Windows Task Scheduler

1. Open Task Scheduler.
2. Create a basic task.
3. Choose a schedule such as daily.
4. Set the action to run:

```bash
python
```

5. Set the argument to:

```bash
scripts/update_internships_apify.py --limit 5
```

6. Set the start folder to your project root.

### Cron on Linux or macOS

Open your crontab:

```bash
crontab -e
```

Example daily job:

```bash
0 8 * * * cd /path/to/internyx && /usr/bin/python3 scripts/update_internships_apify.py --limit 5
```

## 9. How to avoid wasting Apify credits

- Start with `--limit 5`.
- Use `--dry-run` before writing data.
- Do not run the scraper too often.
- Keep `APIFY_MAX_RESULTS` small while testing.

## 10. Safety note

- Public data only.
- No login cookies.
- No private accounts.
- No bypassing login pages or website restrictions.
- Respect the public websites and the actor you choose.

## 11. Run tests

```bash
pytest
```

## 12. Important note about Apify actor input schema

Different Apify actors use different input field names.

This project defaults to a public search-style actor and builds one `actor_input` dictionary inside `scripts/update_internships_apify.py`. If your chosen actor expects different keys, you may need to adjust:

- `queries`
- `resultsPerPage`
- `maxPagesPerQuery`
- `languageCode`
- any actor-specific filters

The script is already structured so you can update that one `actor_input` block without changing the rest of the pipeline.
