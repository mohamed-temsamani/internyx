# Internyx — Flask / SQLite / Bootstrap Rebuild

This is an independent rebuild of the Internyx internship platform using:

- Frontend: HTML templates + Bootstrap + custom CSS
- Backend: Python Flask
- Database: SQLite

It includes the same core pages and experience from the original version:

- Dashboard
- About
- Internship listings with search, filters, and sorting
- Internship detail pages
- Save internship
- Apply to internship
- Career path explorer
- Student profile with saved internships and applications

## Run locally

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

Windows CMD:

```bash
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Test

```bash
pytest
```

## Database

The SQLite database is created automatically in `instance/internyx.sqlite` on first run. Internship data is seeded from `data/internships.json`.

## Notes

No Lovable platform code, hosting badge, or visible Lovable branding is included in this rebuild.
