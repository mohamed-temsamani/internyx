import json
import os
import re
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "internships.json"
DEFAULT_LOGO_GRADIENT = "from-primary to-clay"
DEFAULT_PERKS = [
    "Real internship experience",
    "Mentorship opportunity",
    "Public listing source",
]
DEFAULT_APPLICATION_PROCESS = [
    {"step": "Apply", "desc": "Apply through the source link or the company careers page."},
    {"step": "Review", "desc": "Company review of your profile and CV."},
    {"step": "Interview", "desc": "Short interview if your profile matches the role."},
]
PREFERRED_CITIES = [
    "Casablanca",
    "Rabat",
    "Marrakech",
    "Tangier",
    "Fes",
    "Agadir",
    "Meknes",
    "Oujda",
    "Tetouan",
    "Kenitra",
    "Mohammedia",
]

CAREER_PATHS = [
    {
        "id": "tech",
        "field": "Computer Science",
        "emoji": "💻",
        "marketGrowth": "+27% YoY",
        "steps": [
            {"role": "Internship", "level": "Year 1-2", "salary": "3-5k MAD", "skills": ["HTML/CSS", "Git", "JavaScript"]},
            {"role": "Junior Developer", "level": "0-2 years", "salary": "8-14k MAD", "skills": ["React", "APIs", "SQL"]},
            {"role": "Mid Engineer", "level": "3-5 years", "salary": "15-25k MAD", "skills": ["System design", "TypeScript", "Cloud"]},
            {"role": "Senior / Lead", "level": "5+ years", "salary": "28-45k MAD", "skills": ["Architecture", "Mentorship", "Strategy"]},
        ],
        "cities": [{"name": "Casablanca", "demand": "Very high"}, {"name": "Rabat", "demand": "High"}, {"name": "Tangier", "demand": "Growing"}],
    },
    {
        "id": "data",
        "field": "Data & AI",
        "emoji": "📊",
        "marketGrowth": "+34% YoY",
        "steps": [
            {"role": "Data Intern", "level": "Year 2-3", "salary": "3-4k MAD", "skills": ["Excel", "SQL", "Python"]},
            {"role": "Data Analyst", "level": "0-2 years", "salary": "9-15k MAD", "skills": ["Power BI", "Statistics", "SQL"]},
            {"role": "Data Scientist", "level": "2-5 years", "salary": "16-28k MAD", "skills": ["ML", "Python", "Deep Learning"]},
            {"role": "Lead / Head of Data", "level": "5+ years", "salary": "30-50k MAD", "skills": ["Strategy", "MLOps", "Team leadership"]},
        ],
        "cities": [{"name": "Casablanca", "demand": "Very high"}, {"name": "Rabat", "demand": "High"}],
    },
    {
        "id": "design",
        "field": "Design & UX",
        "emoji": "🎨",
        "marketGrowth": "+18% YoY",
        "steps": [
            {"role": "Design Intern", "level": "Year 2-3", "salary": "3-4k MAD", "skills": ["Figma", "Sketching", "Research"]},
            {"role": "Junior Designer", "level": "0-2 years", "salary": "8-13k MAD", "skills": ["UI", "Prototyping", "Design systems"]},
            {"role": "Product Designer", "level": "2-5 years", "salary": "15-25k MAD", "skills": ["UX research", "Strategy", "Workshops"]},
            {"role": "Design Lead", "level": "5+ years", "salary": "26-40k MAD", "skills": ["Leadership", "Vision", "Hiring"]},
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
        {"name": "React", "level": 85},
        {"name": "TypeScript", "level": 78},
        {"name": "Python", "level": 65},
        {"name": "SQL", "level": 72},
        {"name": "Figma", "level": 60},
        {"name": "Communication (FR/EN/AR)", "level": 90},
    ],
    "projects": [
        {"name": "Souk Connect", "desc": "Marketplace for Moroccan artisans, built with Next.js.", "tag": "Web"},
        {"name": "Tariq Reader", "desc": "AI-powered Arabic news summarizer.", "tag": "AI"},
    ],
    "experience": [
        {"company": "ENSIAS Coding Club", "role": "Web team member", "period": "2024 - Present"},
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


def load_internships() -> list[dict[str, Any]]:
    """Load the latest internships from disk every time we need them."""
    if not DATA_FILE.exists():
        return []

    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(raw, list):
        return []

    return [hydrate_internship(item) for item in raw if isinstance(item, dict)]


def hydrate_internship(item: dict[str, Any]) -> dict[str, Any]:
    role = str(item.get("role") or item.get("title") or "Internship Opportunity").strip()
    company = str(item.get("company") or "Company not specified").strip()
    field = str(item.get("field") or "Other").strip()
    skills = item.get("skills") if isinstance(item.get("skills"), list) else []
    responsibilities = item.get("responsibilities") if isinstance(item.get("responsibilities"), list) else []
    requirements = item.get("requirements") if isinstance(item.get("requirements"), list) else []
    nice_to_have = item.get("niceToHave") if isinstance(item.get("niceToHave"), list) else []
    perks = item.get("perks") if isinstance(item.get("perks"), list) else []
    application_process = item.get("applicationProcess")

    normalized_process = []
    if isinstance(application_process, list):
        for step in application_process:
            if isinstance(step, dict):
                normalized_process.append(
                    {
                        "step": str(step.get("step") or "Step").strip(),
                        "desc": str(step.get("desc") or step.get("description") or "").strip(),
                    }
                )
            elif isinstance(step, str) and step.strip():
                normalized_process.append({"step": step.strip(), "desc": ""})

    return {
        **item,
        "id": str(item.get("id") or "").strip(),
        "role": role,
        "company": company,
        "logo": str(item.get("logo") or company[:3].upper() or "INT").strip(),
        "logoBg": str(item.get("logoBg") or DEFAULT_LOGO_GRADIENT).strip(),
        "location": str(item.get("location") or "Morocco").strip(),
        "remote": str(item.get("remote") or "On-site").strip(),
        "duration": str(item.get("duration") or "3 months").strip(),
        "field": field,
        "skills": [str(skill).strip() for skill in skills if str(skill).strip()] or ["Communication", "Microsoft Office"],
        "match": int(item.get("match") or 65),
        "posted": str(item.get("posted") or "Recently posted").strip(),
        "stipend": str(item.get("stipend") or "Not specified").strip(),
        "description": str(item.get("description") or "Explore this internship opportunity in Morocco.").strip(),
        "longDescription": str(item.get("longDescription") or item.get("description") or "More information is available on the original listing.").strip(),
        "responsibilities": [str(value).strip() for value in responsibilities if str(value).strip()],
        "requirements": [str(value).strip() for value in requirements if str(value).strip()],
        "niceToHave": [str(value).strip() for value in nice_to_have if str(value).strip()],
        "perks": [str(value).strip() for value in perks if str(value).strip()] or DEFAULT_PERKS.copy(),
        "aboutCompany": str(item.get("aboutCompany") or f"{company} is listed as a public internship source in Morocco.").strip(),
        "applicationProcess": normalized_process or DEFAULT_APPLICATION_PROCESS.copy(),
        "openings": item.get("openings") or 1,
        "startDate": str(item.get("startDate") or "Not specified").strip(),
        "teamSize": str(item.get("teamSize") or "Not specified").strip(),
        "sourceUrl": str(item.get("sourceUrl") or item.get("url") or "").strip(),
    }


# Session-based helpers
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


# Data helpers
def stipend_value(stipend: str) -> int:
    digits = re.sub(r"\D", "", stipend or "")
    return int(digits) if digits else 0


def posted_days(posted: str) -> int:
    posted_lower = (posted or "").lower()
    if "recent" in posted_lower or "today" in posted_lower:
        return 0

    number_match = re.search(r"\d+", posted_lower)
    n = int(number_match.group(0)) if number_match else 0
    if "week" in posted_lower:
        return n * 7
    if "month" in posted_lower:
        return n * 30
    return n


def get_internships(
    q: str = "",
    fields: list[str] | None = None,
    durations: list[str] | None = None,
    modes: list[str] | None = None,
    cities: list[str] | None = None,
    selected_skills: list[str] | None = None,
    sort: str = "match",
) -> list[dict[str, Any]]:
    internships = load_internships()
    fields = fields or []
    durations = durations or []
    modes = modes or []
    cities = cities or []
    selected_skills = selected_skills or []
    q_lower = q.lower().strip()
    selected_skill_set = {skill.lower().strip() for skill in selected_skills if skill.strip()}

    def matches(item: dict[str, Any]) -> bool:
        haystack = " ".join(
            [
                str(item.get("role", "")),
                str(item.get("company", "")),
                str(item.get("field", "")),
                str(item.get("location", "")),
                str(item.get("remote", "")),
                str(item.get("description", "")),
                " ".join(str(skill) for skill in item.get("skills", [])),
            ]
        ).lower()
        if q_lower and q_lower not in haystack:
            return False
        if fields and item.get("field") not in fields:
            return False
        if durations and item.get("duration") not in durations:
            return False
        if modes and item.get("remote") not in modes:
            return False
        if cities and item.get("location") not in cities:
            return False
        if selected_skill_set:
            item_skills = {str(skill).lower().strip() for skill in item.get("skills", [])}
            if not item_skills.intersection(selected_skill_set):
                return False
        return True

    filtered = [item for item in internships if matches(item)]
    if sort == "recent":
        filtered.sort(key=lambda internship: posted_days(str(internship.get("posted", ""))))
    elif sort == "stipend":
        filtered.sort(key=lambda internship: stipend_value(str(internship.get("stipend", ""))), reverse=True)
    else:
        filtered.sort(key=lambda internship: int(internship.get("match") or 0), reverse=True)
    return filtered


def get_internship(internship_id: str) -> dict[str, Any] | None:
    return next((item for item in load_internships() if item.get("id") == internship_id), None)


def build_filter_options(internships: list[dict[str, Any]]) -> dict[str, list[str]]:
    fields = sorted({str(item.get("field") or "Other") for item in internships})
    durations = sorted({str(item.get("duration") or "3 months") for item in internships})
    modes = sorted({str(item.get("remote") or "On-site") for item in internships})
    skills = sorted({str(skill) for item in internships for skill in item.get("skills", []) if str(skill).strip()})

    known_cities = {city for city in PREFERRED_CITIES}
    cities_from_data = {
        str(item.get("location") or "").strip()
        for item in internships
        if str(item.get("location") or "").strip() and str(item.get("location") or "").strip() != "Morocco"
    }
    cities = [city for city in PREFERRED_CITIES if city in cities_from_data or city in known_cities]
    extra_cities = sorted(city for city in cities_from_data if city not in cities)

    return {
        "fields": fields,
        "durations": durations,
        "modes": modes,
        "cities": cities + extra_cities,
        "skills": skills,
    }


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
        return render_template("dashboard.html", recommended=recommended, title="Dashboard - Internyx")

    @app.route("/about")
    def about():
        return render_template("about.html", title="About - Internyx")

    @app.route("/internships")
    def internships():
        all_internships = load_internships()
        selected_fields = request.args.getlist("field")
        selected_durations = request.args.getlist("duration")
        selected_modes = request.args.getlist("remote")
        selected_cities = request.args.getlist("city")
        selected_skills = request.args.getlist("skill")
        q = request.args.get("q", "").strip()
        sort = request.args.get("sort", "match")
        listings = get_internships(
            q=q,
            fields=selected_fields,
            durations=selected_durations,
            modes=selected_modes,
            cities=selected_cities,
            selected_skills=selected_skills,
            sort=sort,
        )
        options = build_filter_options(all_internships)
        active_count = (
            len(selected_fields)
            + len(selected_durations)
            + len(selected_modes)
            + len(selected_cities)
            + len(selected_skills)
        )
        return render_template(
            "internships.html",
            title="Internships - Internyx",
            internships=listings,
            total=len(all_internships) * 40,
            q=q,
            sort=sort,
            selected_fields=selected_fields,
            selected_durations=selected_durations,
            selected_modes=selected_modes,
            selected_cities=selected_cities,
            selected_skills=selected_skills,
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
            title=f"{internship.get('role', 'Internship')} at {internship.get('company', 'Company not specified')} - Internyx",
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
        flash("Application submitted! Good luck.", "success")
        return redirect(url_for("internship_detail", internship_id=internship_id))

    @app.route("/career-paths")
    def career_paths():
        path_id = request.args.get("path", CAREER_PATHS[0]["id"])
        active_path = next((p for p in CAREER_PATHS if p["id"] == path_id), CAREER_PATHS[0])
        top_skills = list({s for step in active_path["steps"] for s in step["skills"]})[:8]
        return render_template(
            "career_paths.html",
            title="Career Paths - Internyx",
            paths=CAREER_PATHS,
            active_path=active_path,
            top_skills=top_skills,
        )

    @app.route("/profile")
    def profile_page():
        internships = load_internships()
        applied_ids = session.get("applied", {})
        saved_ids = session.get("saved", [])
        applications = [item for item in internships if item.get("id") in applied_ids]
        saved = [item for item in internships if item.get("id") in saved_ids]
        return render_template(
            "profile.html",
            title="Profile - Internyx",
            applications=applications,
            saved=saved,
        )

    @app.route("/profile/edit")
    def edit_profile_page():
        return render_template(
            "edit_profile.html",
            title="Edit Profile - Internyx",
        )

    @app.post("/profile/update")
    def update_profile():
        PROFILE["name"] = request.form.get("name", "").strip() or PROFILE["name"]
        PROFILE["subtitle"] = request.form.get("subtitle", "").strip() or PROFILE["subtitle"]
        PROFILE["location"] = request.form.get("location", "").strip() or PROFILE["location"]
        PROFILE["education"] = request.form.get("education", "").strip() or PROFILE["education"]
        PROFILE["email"] = request.form.get("email", "").strip() or PROFILE["email"]
        PROFILE["about"] = request.form.get("about", "").strip() or PROFILE["about"]
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile_page"))

    @app.errorhandler(404)
    def not_found(error: Exception):
        return render_template("404.html", title="Not found - Internyx"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
