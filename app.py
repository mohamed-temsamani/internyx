import json
import os
import re
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "internships.json"

CAREER_PATHS = [
    {
        "id": "tech",
        "field": "Computer Science",
        "emoji": "💻",
        "marketGrowth": "+27% YoY",
        "steps": [
            {"role": "Internship", "level": "Year 1–2", "salary": "3–5k MAD", "skills": ["HTML/CSS", "Git", "JavaScript"]},
            {"role": "Junior Developer", "level": "0–2 years", "salary": "8–14k MAD", "skills": ["React", "APIs", "SQL"]},
            {"role": "Mid Engineer", "level": "3–5 years", "salary": "15–25k MAD", "skills": ["System design", "TypeScript", "Cloud"]},
            {"role": "Senior / Lead", "level": "5+ years", "salary": "28–45k MAD", "skills": ["Architecture", "Mentorship", "Strategy"]},
        ],
        "cities": [{"name": "Casablanca", "demand": "Very high"}, {"name": "Rabat", "demand": "High"}, {"name": "Tangier", "demand": "Growing"}],
    },
    {
        "id": "data",
        "field": "Data & AI",
        "emoji": "📊",
        "marketGrowth": "+34% YoY",
        "steps": [
            {"role": "Data Intern", "level": "Year 2–3", "salary": "3–4k MAD", "skills": ["Excel", "SQL", "Python"]},
            {"role": "Data Analyst", "level": "0–2 years", "salary": "9–15k MAD", "skills": ["Power BI", "Statistics", "SQL"]},
            {"role": "Data Scientist", "level": "2–5 years", "salary": "16–28k MAD", "skills": ["ML", "Python", "Deep Learning"]},
            {"role": "Lead / Head of Data", "level": "5+ years", "salary": "30–50k MAD", "skills": ["Strategy", "MLOps", "Team leadership"]},
        ],
        "cities": [{"name": "Casablanca", "demand": "Very high"}, {"name": "Rabat", "demand": "High"}],
    },
    {
        "id": "design",
        "field": "Design & UX",
        "emoji": "🎨",
        "marketGrowth": "+18% YoY",
        "steps": [
            {"role": "Design Intern", "level": "Year 2–3", "salary": "3–4k MAD", "skills": ["Figma", "Sketching", "Research"]},
            {"role": "Junior Designer", "level": "0–2 years", "salary": "8–13k MAD", "skills": ["UI", "Prototyping", "Design systems"]},
            {"role": "Product Designer", "level": "2–5 years", "salary": "15–25k MAD", "skills": ["UX research", "Strategy", "Workshops"]},
            {"role": "Design Lead", "level": "5+ years", "salary": "26–40k MAD", "skills": ["Leadership", "Vision", "Hiring"]},
        ],
        "cities": [{"name": "Casablanca", "demand": "High"}, {"name": "Marrakech", "demand": "Growing"}],
    },
]

PROFILE = {
    "initials": "YE",
    "name": "Yahya raihan",
    "subtitle": "Computer Science · 2nd year · ENSIAS",
    "location": "Rabat, Morocco",
    "education": "ENSIAS · Class of 2027",
    "email": "yahya.raihan@um5.ac.ma",
    "about": "2nd-year CS student passionate about web development and human-centered design. Looking for a 3-month internship to apply React and TypeScript skills on a real product. Trilingual: Arabic, French, English.",
    "skills": [
        {"name": "React", "level": 85}, {"name": "TypeScript", "level": 78}, {"name": "Python", "level": 65},
        {"name": "SQL", "level": 72}, {"name": "Figma", "level": 60}, {"name": "Communication (FR/EN/AR)", "level": 90},
    ],
    "projects": [
        {"name": "Souk Connect", "desc": "Marketplace for Moroccan artisans, built with Next.js.", "tag": "Web"},
        {"name": "Tariq Reader", "desc": "AI-powered Arabic news summarizer.", "tag": "AI"},
    ],
    "experience": [
        {"company": "ENSIAS Coding Club", "role": "Web team member", "period": "2024 — Present"},
        {"company": "Le Reflet", "role": "Volunteer · Tutor", "period": "Summer 2024"},
    ],
    "factors": [
        {"label": "Profile completeness", "value": 92, "status": "good"},
        {"label": "CV uploaded & parsed", "value": 100, "status": "good"},
        {"label": "Projects added (2/4)", "value": 50, "status": "warn"},
        {"label": "Skills assessed (6/10)", "value": 60, "status": "warn"},
        {"label": "Mock interview", "value": 0, "status": "todo"},
        {"label": "Recommendations (1/2)", "value": 50, "status": "warn"},
    ],
}

# Load internships once at startup from the JSON file
def _load_internships() -> list[dict[str, Any]]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

INTERNSHIPS: list[dict[str, Any]] = _load_internships()


# ── Session-based helpers (replaces SQLite) ───────────────────────────────────

def is_saved(internship_id: str) -> bool:
    return internship_id in session.get("saved", [])


def has_applied(internship_id: str) -> bool:
    return internship_id in session.get("applied", {})


def save_internship_to_session(internship_id: str) -> None:
    saved = session.get("saved", [])
    if internship_id not in saved:
        saved.append(internship_id)
    session["saved"] = saved


def apply_to_session(internship_id: str, name: str, email: str, note: str) -> None:
    applied = session.get("applied", {})
    applied[internship_id] = {"name": name, "email": email, "note": note}
    session["applied"] = applied


# ── Data helpers ──────────────────────────────────────────────────────────────

def stipend_value(stipend: str) -> int:
    digits = re.sub(r"\D", "", stipend or "")
    return int(digits) if digits else 0


def posted_days(posted: str) -> int:
    number_match = re.search(r"\d+", posted or "")
    n = int(number_match.group(0)) if number_match else 0
    if "week" in posted:
        return n * 7
    if "month" in posted:
        return n * 30
    return n


def get_internships(
    q: str = "",
    fields: list[str] | None = None,
    durations: list[str] | None = None,
    modes: list[str] | None = None,
    cities: list[str] | None = None,
    sort: str = "match",
) -> list[dict[str, Any]]:
    fields = fields or []
    durations = durations or []
    modes = modes or []
    cities = cities or []
    q_lower = q.lower().strip()

    def matches(item: dict[str, Any]) -> bool:
        haystack = " ".join([
            item["role"], item["company"], item["field"],
            item["location"], item["remote"], item["description"],
            *item["skills"],
        ]).lower()
        if q_lower and q_lower not in haystack:
            return False
        if fields and item["field"] not in fields:
            return False
        if durations and item["duration"] not in durations:
            return False
        if modes and item["remote"] not in modes:
            return False
        if cities and item["location"] not in cities:
            return False
        return True

    filtered = [i for i in INTERNSHIPS if matches(i)]
    if sort == "recent":
        filtered.sort(key=lambda i: posted_days(i["posted"]))
    elif sort == "stipend":
        filtered.sort(key=lambda i: stipend_value(i["stipend"]), reverse=True)
    else:
        filtered.sort(key=lambda i: i["match"], reverse=True)
    return filtered


def get_internship(internship_id: str) -> dict[str, Any] | None:
    return next((i for i in INTERNSHIPS if i["id"] == internship_id), None)


# ── App factory ───────────────────────────────────────────────────────────────

def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    if test_config:
        app.config.update(test_config)

    @app.template_filter("gradient")
    def gradient_filter(value: str) -> str:
        mapping = {
            "from-primary to-clay": "gradient-primary-clay",
            "from-zellige to-success": "gradient-zellige-success",
            "from-clay to-warning": "gradient-clay-warning",
            "from-primary to-warning": "gradient-primary-warning",
            "from-zellige to-clay": "gradient-zellige-clay",
            "from-warning to-clay": "gradient-warning-clay",
        }
        return mapping.get(value, "gradient-primary")

    @app.context_processor
    def inject_globals() -> dict[str, Any]:
        return {
            "nav_items": [
                ("dashboard", "Dashboard"),
                ("about", "About Us"),
                ("internships", "Internships"),
                ("career_paths", "Career Paths"),
            ],
            "profile": PROFILE,
        }

    @app.route("/")
    def dashboard():
        recommended = get_internships(sort="match")[:3]
        return render_template("dashboard.html", recommended=recommended, title="Dashboard — Internyx")

    @app.route("/about")
    def about():
        return render_template("about.html", title="About — Internyx")

    @app.route("/internships")
    def internships():
        selected_fields = request.args.getlist("field")
        selected_durations = request.args.getlist("duration")
        selected_modes = request.args.getlist("remote")
        selected_cities = request.args.getlist("city")
        q = request.args.get("q", "").strip()
        sort = request.args.get("sort", "match")
        listings = get_internships(
            q=q,
            fields=selected_fields,
            durations=selected_durations,
            modes=selected_modes,
            cities=selected_cities,
            sort=sort,
        )
        options = {
            "fields": sorted({i["field"] for i in INTERNSHIPS} | {"Finance"}),
            "durations": ["1 month", "2 months", "3 months"],
            "modes": ["Remote", "Hybrid", "On-site"],
            "cities": ["Casablanca", "Rabat", "Marrakech", "Tangier", "Fès", "Agadir"],
        }
        active_count = len(selected_fields) + len(selected_durations) + len(selected_modes) + len(selected_cities)
        return render_template(
            "internships.html",
            title="Internships — Internyx",
            internships=listings,
            total=len(INTERNSHIPS) * 40,
            q=q,
            sort=sort,
            selected_fields=selected_fields,
            selected_durations=selected_durations,
            selected_modes=selected_modes,
            selected_cities=selected_cities,
            options=options,
            active_count=active_count,
        )

    @app.route("/internships/<internship_id>")
    def internship_detail(internship_id: str):
        internship = get_internship(internship_id)
        if not internship:
            abort(404)
        quality = [
            {"label": "Mentorship", "value": 4.7},
            {"label": "Learning", "value": 4.5},
            {"label": "Fairness", "value": 4.8},
            {"label": "Work-life", "value": 4.3},
        ]
        overall = round(sum(q["value"] for q in quality) / len(quality), 1)
        return render_template(
            "internship_detail.html",
            title=f"{internship['role']} at {internship['company']} — Internyx",
            i=internship,
            quality=quality,
            overall=overall,
            saved=is_saved(internship_id),
            applied=has_applied(internship_id),
        )

    @app.post("/internships/<internship_id>/save")
    def save_internship(internship_id: str):
        if not get_internship(internship_id):
            abort(404)
        save_internship_to_session(internship_id)
        flash("Internship saved!", "success")
        return redirect(url_for("internship_detail", internship_id=internship_id))

    @app.post("/internships/<internship_id>/apply")
    def apply_internship(internship_id: str):
        if not get_internship(internship_id):
            abort(404)
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        note = request.form.get("note", "").strip()
        if not name or not email:
            flash("Name and email are required.", "error")
            return redirect(url_for("internship_detail", internship_id=internship_id))
        apply_to_session(internship_id, name, email, note)
        flash("Application submitted! Good luck 🎉", "success")
        return redirect(url_for("internship_detail", internship_id=internship_id))

    @app.route("/career-paths")
    def career_paths():
        path_id = request.args.get("path", CAREER_PATHS[0]["id"])
        active_path = next((p for p in CAREER_PATHS if p["id"] == path_id), CAREER_PATHS[0])
        top_skills = list({s for step in active_path["steps"] for s in step["skills"]})[:8]
        return render_template(
            "career_paths.html",
            title="Career Paths — Internyx",
            paths=CAREER_PATHS,
            active_path=active_path,
            top_skills=top_skills,
        )

    @app.route("/profile")
    def profile_page():
        applied_ids = session.get("applied", {})
        saved_ids = session.get("saved", [])
        applications = [i for i in INTERNSHIPS if i["id"] in applied_ids]
        saved = [i for i in INTERNSHIPS if i["id"] in saved_ids]
        return render_template(
            "profile.html",
            title="Profile — Internyx",
            applications=applications,
            saved=saved,
        )

    @app.errorhandler(404)
    def not_found(error: Exception):
        return render_template("404.html", title="Not found — Internyx"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)