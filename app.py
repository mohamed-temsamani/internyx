import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "internships.json"
DATABASE = BASE_DIR / "instance" / "internyx.sqlite"

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
    "name": "Yasmine El Amrani",
    "subtitle": "Computer Science · 3rd year · ENSIAS",
    "location": "Rabat, Morocco",
    "education": "ENSIAS · Class of 2027",
    "email": "yasmine.elamrani@um5.ac.ma",
    "about": "3rd-year CS student passionate about web development and human-centered design. Looking for a 3-month internship to apply React and TypeScript skills on a real product. Trilingual: Arabic, French, English.",
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


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"), DATABASE=str(DATABASE))
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    @app.before_request
    def bootstrap_database() -> None:
        init_db_if_needed()

    @app.teardown_appcontext
    def close_db(error: Exception | None = None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.template_filter("json_loads")
    def json_loads_filter(value: str) -> Any:
        return json.loads(value) if value else []

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
        return {"nav_items": [("dashboard", "Dashboard"), ("about", "About Us"), ("internships", "Internships"), ("career_paths", "Career Paths")], "profile": PROFILE}

    @app.route("/")
    def dashboard():
        internships = get_internships(sort="match")
        recommended = internships[:3]
        return render_template("dashboard.html", internships=internships, recommended=recommended, title="Dashboard — Internyx")

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
        listings = get_internships(q=q, fields=selected_fields, durations=selected_durations, modes=selected_modes, cities=selected_cities, sort=sort)
        all_items = get_internships()
        options = {
            "fields": sorted({i["field"] for i in all_items} | {"Finance"}),
            "durations": ["1 month", "2 months", "3 months"],
            "modes": ["Remote", "Hybrid", "On-site"],
            "cities": ["Casablanca", "Rabat", "Marrakech", "Tangier", "Fès", "Agadir"],
        }
        active_count = len(selected_fields) + len(selected_durations) + len(selected_modes) + len(selected_cities)
        return render_template(
            "internships.html",
            title="Internships — Internyx",
            internships=listings,
            total=len(all_items) * 40,
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
        saved = is_saved(internship_id)
        applied = has_applied(internship_id)
        return render_template("internship_detail.html", title=f"{internship['role']} at {internship['company']} — Internyx", i=internship, quality=quality, overall=overall, saved=saved, applied=applied)

    @app.post("/internships/<internship_id>/save")
    def save_internship(internship_id: str):
        if not get_internship(internship_id):
            abort(404)
        db = get_db()
        db.execute("INSERT OR IGNORE INTO saved_internships (internship_id) VALUES (?)", (internship_id,))
        db.commit()
        flash("Internship saved to your profile.", "success")
        return redirect(url_for("internship_detail", internship_id=internship_id))

    @app.post("/internships/<internship_id>/apply")
    def apply_internship(internship_id: str):
        if not get_internship(internship_id):
            abort(404)
        name = request.form.get("name", PROFILE["name"]).strip() or PROFILE["name"]
        email = request.form.get("email", PROFILE["email"]).strip() or PROFILE["email"]
        note = request.form.get("note", "").strip()
        db = get_db()
        db.execute(
            "INSERT OR IGNORE INTO applications (internship_id, applicant_name, email, note) VALUES (?, ?, ?, ?)",
            (internship_id, name, email, note),
        )
        db.commit()
        flash("Application submitted successfully.", "success")
        return redirect(url_for("internship_detail", internship_id=internship_id))

    @app.route("/career-paths")
    def career_paths():
        active_id = request.args.get("path", CAREER_PATHS[0]["id"])
        active_path = next((p for p in CAREER_PATHS if p["id"] == active_id), CAREER_PATHS[0])
        skills = []
        for step in active_path["steps"]:
            for skill in step["skills"]:
                if skill not in skills:
                    skills.append(skill)
        return render_template("career_paths.html", title="Career Paths — Internyx", paths=CAREER_PATHS, active_path=active_path, top_skills=skills[:6])

    @app.route("/profile")
    def profile_page():
        db = get_db()
        applications = db.execute(
            """
            SELECT internships.id, internships.role, internships.company, internships.location, applications.created_at
            FROM applications
            JOIN internships ON internships.id = applications.internship_id
            ORDER BY applications.created_at DESC
            """
        ).fetchall()
        saved = db.execute(
            """
            SELECT internships.id, internships.role, internships.company, internships.location, saved_internships.created_at
            FROM saved_internships
            JOIN internships ON internships.id = saved_internships.internship_id
            ORDER BY saved_internships.created_at DESC
            """
        ).fetchall()
        return render_template("profile.html", title="Profile — Internyx", applications=[dict(a) for a in applications], saved=[dict(s) for s in saved])

    @app.errorhandler(404)
    def not_found(error: Exception):
        return render_template("404.html", title="Not found — Internyx"), 404

    return app


def get_db() -> sqlite3.Connection:
    db = g.get("db")
    if db is None:
        db = sqlite3.connect(current_app_database())
        db.row_factory = sqlite3.Row
        g.db = db
    return db


def current_app_database() -> str:
    from flask import current_app
    return current_app.config["DATABASE"]


def init_db_if_needed() -> None:
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS internships (
            id TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            company TEXT NOT NULL,
            logo TEXT NOT NULL,
            logoBg TEXT NOT NULL,
            location TEXT NOT NULL,
            remote TEXT NOT NULL,
            duration TEXT NOT NULL,
            field TEXT NOT NULL,
            skills TEXT NOT NULL,
            match INTEGER NOT NULL,
            posted TEXT NOT NULL,
            stipend TEXT NOT NULL,
            description TEXT NOT NULL,
            longDescription TEXT NOT NULL,
            responsibilities TEXT NOT NULL,
            requirements TEXT NOT NULL,
            niceToHave TEXT NOT NULL,
            perks TEXT NOT NULL,
            startDate TEXT NOT NULL,
            openings TEXT NOT NULL,
            teamSize TEXT NOT NULL,
            aboutCompany TEXT NOT NULL,
            applicationProcess TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            internship_id TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (internship_id) REFERENCES internships(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            internship_id TEXT NOT NULL UNIQUE,
            applicant_name TEXT NOT NULL,
            email TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (internship_id) REFERENCES internships(id)
        )
        """
    )
    count = db.execute("SELECT COUNT(*) FROM internships").fetchone()[0]
    if count == 0:
        seed_internships(db)
    db.commit()


def seed_internships(db: sqlite3.Connection) -> None:
    internships = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    for i in internships:
        db.execute(
            """
            INSERT INTO internships (
                id, role, company, logo, logoBg, location, remote, duration, field, skills, match,
                posted, stipend, description, longDescription, responsibilities, requirements, niceToHave,
                perks, startDate, openings, teamSize, aboutCompany, applicationProcess
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                i["id"], i["role"], i["company"], i["logo"], i["logoBg"], i["location"], i["remote"], i["duration"], i["field"], json.dumps(i["skills"]), i["match"],
                i["posted"], i["stipend"], i["description"], i["longDescription"], json.dumps(i["responsibilities"]), json.dumps(i["requirements"]), json.dumps(i["niceToHave"]),
                json.dumps(i["perks"]), i["startDate"], i["openings"], i["teamSize"], i["aboutCompany"], json.dumps(i["applicationProcess"]),
            ),
        )


def row_to_internship(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in ["skills", "responsibilities", "requirements", "niceToHave", "perks", "applicationProcess"]:
        data[key] = json.loads(data[key]) if data.get(key) else []
    return data


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


def get_internships(q: str = "", fields: list[str] | None = None, durations: list[str] | None = None, modes: list[str] | None = None, cities: list[str] | None = None, sort: str = "match") -> list[dict[str, Any]]:
    db = get_db()
    items = [row_to_internship(row) for row in db.execute("SELECT * FROM internships").fetchall()]
    fields = fields or []
    durations = durations or []
    modes = modes or []
    cities = cities or []
    q_lower = q.lower().strip()

    def matches(item: dict[str, Any]) -> bool:
        haystack = " ".join([item["role"], item["company"], item["field"], item["location"], item["remote"], item["description"], *item["skills"]]).lower()
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

    filtered = [i for i in items if matches(i)]
    if sort == "recent":
        filtered.sort(key=lambda i: posted_days(i["posted"]))
    elif sort == "stipend":
        filtered.sort(key=lambda i: stipend_value(i["stipend"]), reverse=True)
    else:
        filtered.sort(key=lambda i: i["match"], reverse=True)
    return filtered


def get_internship(internship_id: str) -> dict[str, Any] | None:
    row = get_db().execute("SELECT * FROM internships WHERE id = ?", (internship_id,)).fetchone()
    return row_to_internship(row) if row else None


def is_saved(internship_id: str) -> bool:
    return get_db().execute("SELECT 1 FROM saved_internships WHERE internship_id = ?", (internship_id,)).fetchone() is not None


def has_applied(internship_id: str) -> bool:
    return get_db().execute("SELECT 1 FROM applications WHERE internship_id = ?", (internship_id,)).fetchone() is not None


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
