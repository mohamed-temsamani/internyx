import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from apify_client import ApifyClient
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "internships.json"
DEFAULT_ACTOR_ID = "apify/google-search-scraper"
DEFAULT_MAX_RESULTS = 10
DEFAULT_DESCRIPTION = "Public internship listing found for students looking for opportunities in Morocco."
GRADIENTS = [
    "from-primary to-clay",
    "from-zellige to-success",
    "from-clay to-warning",
    "from-primary to-warning",
    "from-zellige to-clay",
    "from-warning to-clay",
]
SEARCH_QUERIES = [
    "stage informatique Maroc",
    "stage développeur web Maroc",
    "stage data analyst Maroc",
    "stage finance Maroc",
    "stage marketing Maroc",
    "stage cybersécurité Maroc",
    "stage design UX UI Maroc",
    "internship software engineer Morocco",
    "site:rekrute.com stage Maroc",
    "site:emploi.ma stage Maroc",
    "site:linkedin.com/jobs stage Maroc",
]
MOROCCAN_CITIES = [
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
CITY_ALIASES = {
    "casablanca": "Casablanca",
    "rabat": "Rabat",
    "marrakech": "Marrakech",
    "marrakesh": "Marrakech",
    "tanger": "Tangier",
    "tangier": "Tangier",
    "fes": "Fes",
    "fès": "Fes",
    "agadir": "Agadir",
    "meknes": "Meknes",
    "meknès": "Meknes",
    "oujda": "Oujda",
    "tetouan": "Tetouan",
    "tétouan": "Tetouan",
    "kenitra": "Kenitra",
    "kénitra": "Kenitra",
    "mohammedia": "Mohammedia",
}
CONTROLLED_SKILLS = [
    "Python",
    "SQL",
    "React",
    "JavaScript",
    "TypeScript",
    "HTML",
    "CSS",
    "Flask",
    "Django",
    "Laravel",
    "PHP",
    "Java",
    "Node.js",
    "Git",
    "API",
    "Excel",
    "Power BI",
    "Tableau",
    "Machine Learning",
    "Data Analysis",
    "Cybersecurity",
    "Network Security",
    "SOC",
    "Finance",
    "Accounting",
    "Audit",
    "Marketing",
    "SEO",
    "Social Media",
    "Communication",
    "Figma",
    "Adobe XD",
    "Photoshop",
    "Illustrator",
    "UX",
    "UI",
    "Project Management",
    "Logistics",
    "Sales",
    "Microsoft Office",
]
SKILL_KEYWORDS = {
    "Python": ["python", "pandas", "numpy"],
    "SQL": ["sql"],
    "React": ["react"],
    "JavaScript": ["javascript"],
    "TypeScript": ["typescript"],
    "HTML": ["html"],
    "CSS": ["css"],
    "Flask": ["flask"],
    "Django": ["django"],
    "Laravel": ["laravel"],
    "PHP": ["php"],
    "Java": ["java"],
    "Node.js": ["node", "node.js"],
    "Git": ["git"],
    "API": ["api", "rest"],
    "Excel": ["excel"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "Machine Learning": ["machine learning", "ml"],
    "Data Analysis": ["data analysis", "analytics", "analyst"],
    "Cybersecurity": ["cybersecurity", "cyber security", "security"],
    "Network Security": ["network security", "firewall"],
    "SOC": ["soc", "siem"],
    "Finance": ["finance", "financial analysis", "budget", "tresorerie", "trésorerie"],
    "Accounting": ["accounting", "comptabilite", "comptabilité"],
    "Audit": ["audit"],
    "Marketing": ["marketing", "campaign", "brand"],
    "SEO": ["seo"],
    "Social Media": ["social media", "community manager"],
    "Communication": ["communication"],
    "Figma": ["figma"],
    "Adobe XD": ["adobe xd"],
    "Photoshop": ["photoshop"],
    "Illustrator": ["illustrator"],
    "UX": [" ux ", "user experience", "wireframe", "prototype", "prototyping"],
    "UI": [" ui ", "user interface"],
    "Project Management": ["project management", "operations"],
    "Logistics": ["logistics", "supply chain", "procurement", "achat"],
    "Sales": ["sales", "commercial"],
    "Microsoft Office": ["microsoft office", "word", "powerpoint"],
}
FIELD_KEYWORDS = {
    "Computer Science": [
        "developer",
        "software",
        "web",
        "frontend",
        "backend",
        "full stack",
        "javascript",
        "react",
        "node",
        "laravel",
        "php",
        "django",
        "flask",
        "java",
        "git",
        "api",
        "html",
        "css",
        "typescript",
    ],
    "Data & AI": [
        "data analyst",
        "data science",
        "ai",
        "artificial intelligence",
        "machine learning",
        "python",
        "sql",
        "power bi",
        "tableau",
        "statistics",
        "analytics",
        "excel",
        "pandas",
        "numpy",
    ],
    "Cybersecurity": [
        "cybersecurity",
        "cyber security",
        "security",
        "soc",
        "phishing",
        "network security",
        "ethical hacking",
        "risk",
        "iso 27001",
        "firewall",
        "pentest",
        "siem",
    ],
    "Finance": [
        "finance",
        "accounting",
        "audit",
        "contrôle de gestion",
        "controle de gestion",
        "comptabilité",
        "comptabilite",
        "financial analysis",
        "budget",
        "excel",
        "fiscalité",
        "tresorerie",
    ],
    "Marketing": [
        "marketing",
        "digital marketing",
        "social media",
        "seo",
        "content",
        "communication",
        "brand",
        "campaign",
        "ads",
        "community manager",
    ],
    "Design & UX": [
        "design",
        "ui",
        "ux",
        "figma",
        "adobe xd",
        "photoshop",
        "illustrator",
        "graphic design",
        "product design",
        "wireframe",
        "prototype",
    ],
    "Business / Management": [
        "business",
        "management",
        "project management",
        "operations",
        "hr",
        "human resources",
        "supply chain",
        "logistics",
        "commercial",
        "sales",
        "achat",
        "procurement",
    ],
}


def normalize_compare(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def safe_load_internships() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        print(f"[info] {DATA_FILE} does not exist yet. Starting from an empty list.")
        return []

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"[warning] {DATA_FILE} is not valid JSON. Starting from an empty list to avoid crashing.")
        return []
    except OSError as exc:
        print(f"[warning] Could not read {DATA_FILE}: {exc}")
        return []

    if not isinstance(data, list):
        print(f"[warning] {DATA_FILE} did not contain a JSON list. Starting from an empty list.")
        return []

    return [item for item in data if isinstance(item, dict)]


def save_internships(data: list[dict[str, Any]]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def pick_first(item: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def shorten_text(value: str, max_length: int = 180) -> str:
    value = clean_text(value)
    if len(value) <= max_length:
        return value
    shortened = value[: max_length - 3].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."


def make_company_logo(company: str) -> str:
    letters = re.findall(r"[A-Za-z0-9]", company.upper())
    return "".join(letters[:3]) or "INT"


def detect_city(*values: str) -> str:
    combined = " ".join(values).lower()
    for alias, city in CITY_ALIASES.items():
        if alias in combined:
            return city
    return "Morocco"


def detect_remote_mode(*values: str) -> str:
    combined = " ".join(values).lower()
    if "hybrid" in combined:
        return "Hybrid"
    if any(keyword in combined for keyword in ["remote", "à distance", "distance", "work from home"]):
        return "Remote"
    return "On-site"


def detect_duration(*values: str) -> str:
    combined = " ".join(values).lower()
    month_match = re.search(r"(\d+)\s*(month|months|mois)", combined)
    if month_match:
        number = month_match.group(1)
        return f"{number} month" if number == "1" else f"{number} months"

    if "summer" in combined or "été" in combined:
        return "2 months"
    return "3 months"


def extract_source_name(source_url: str, item: dict[str, Any]) -> str:
    direct_source = pick_first(item, ["source", "sourceWebsite", "website"])
    if direct_source:
        return clean_text(direct_source)

    hostname = urlparse(source_url).netloc.lower().replace("www.", "")
    return hostname or "public web listing"


def build_stable_id(role: str, company: str, source_url: str) -> str:
    seed = f"{role}|{company}|{source_url}".encode("utf-8")
    digest = hashlib.sha1(seed).hexdigest()[:12]
    return f"apify-{digest}"


def choose_logo_gradient(stable_id: str) -> str:
    index = int(hashlib.sha1(stable_id.encode("utf-8")).hexdigest(), 16) % len(GRADIENTS)
    return GRADIENTS[index]


def extract_skills(text: str) -> list[str]:
    normalized = f" {normalize_compare(text)} "
    found: list[str] = []
    for skill in CONTROLLED_SKILLS:
        keywords = SKILL_KEYWORDS.get(skill, [skill.lower()])
        if any(keyword in normalized for keyword in keywords):
            found.append(skill)

    if "sql" in normalized and "SQL" not in found:
        found.append("SQL")

    if not found:
        return ["Communication", "Microsoft Office"]

    return found


def classify_internship(title: str, description: str) -> tuple[str, list[str], int]:
    combined = f"{title} {description}".lower()
    normalized = f" {clean_text(combined)} "
    field_scores: dict[str, int] = {}

    for field, keywords in FIELD_KEYWORDS.items():
        field_scores[field] = sum(1 for keyword in keywords if keyword in normalized)

    finance_terms = ["finance", "accounting", "audit", "contrôle de gestion", "controle de gestion", "comptabilité", "comptabilite"]
    if any(term in normalized for term in finance_terms):
        field = "Finance"
    else:
        best_field = max(field_scores, key=field_scores.get)
        field = best_field if field_scores[best_field] > 0 else "Business / Management"

    skills = extract_skills(normalized)
    keyword_match_count = field_scores.get(field, 0)
    if field == "Finance" and any(term in normalized for term in finance_terms):
        keyword_match_count = max(keyword_match_count, 2)

    match_score = 65 + min(30, keyword_match_count * 5 + len(skills) * 3)
    return field, skills, int(match_score)


def generate_responsibilities(field: str, description: str, skills: list[str]) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", clean_text(description))
    bullets = [sentence for sentence in sentences if 35 <= len(sentence) <= 140][:3]
    if bullets:
        return bullets

    defaults = {
        "Computer Science": [
            "Support the team in building and improving software features.",
            "Test and document the work delivered during the internship.",
            "Collaborate with mentors on product or engineering tasks.",
        ],
        "Data & AI": [
            "Help clean, analyze, and report on business or product data.",
            "Support dashboard updates and basic data validation work.",
            "Present insights clearly to the team with mentor guidance.",
        ],
        "Cybersecurity": [
            "Support security monitoring and documentation tasks.",
            "Help review incidents, alerts, or policy-related findings.",
            "Work with mentors on secure practices and reporting.",
        ],
        "Finance": [
            "Support reporting, reconciliations, or budget follow-up tasks.",
            "Help organize financial documents and basic analysis work.",
            "Prepare clear updates for the finance team with mentor support.",
        ],
        "Marketing": [
            "Support campaign planning and content coordination tasks.",
            "Track results and summarize performance with the team.",
            "Help prepare communication materials for public channels.",
        ],
        "Design & UX": [
            "Support design research, wireframes, and interface updates.",
            "Collaborate on prototypes and design handoff tasks.",
            "Help document feedback and improve user flows.",
        ],
    }
    return defaults.get(
        field,
        [
            "Support day-to-day internship tasks with guidance from the team.",
            "Help document progress and communicate clearly with mentors.",
            f"Apply and strengthen skills such as {', '.join(skills[:3])}.",
        ],
    )


def generate_requirements(field: str, skills: list[str]) -> list[str]:
    base = [
        f"Interest in {field} and willingness to learn in a professional setting.",
        "Good communication skills and ability to work with a team.",
    ]
    if skills:
        base.insert(0, f"Exposure to {', '.join(skills[:3])}.")
    return base


def generate_nice_to_have(field: str, skills: list[str]) -> list[str]:
    extras = [skill for skill in CONTROLLED_SKILLS if skill not in skills]
    field_hints = {
        "Computer Science": ["Git", "API", "JavaScript"],
        "Data & AI": ["SQL", "Excel", "Power BI"],
        "Cybersecurity": ["SOC", "Network Security", "Communication"],
        "Finance": ["Excel", "Accounting", "Audit"],
        "Marketing": ["SEO", "Social Media", "Communication"],
        "Design & UX": ["Figma", "UI", "UX"],
        "Business / Management": ["Project Management", "Communication", "Microsoft Office"],
    }
    preferred = field_hints.get(field, extras[:3])
    return [skill for skill in preferred if skill not in skills][:3]


def normalize_apify_item(item: dict[str, Any]) -> dict[str, Any] | None:
    title = clean_text(pick_first(item, ["title", "name", "jobTitle", "positionName"]))
    company = clean_text(pick_first(item, ["company", "companyName", "organization"]))
    location_raw = clean_text(pick_first(item, ["location", "address", "city"]))
    description = clean_text(pick_first(item, ["description", "text", "snippet", "content"]))
    source_url = clean_text(pick_first(item, ["url", "link", "pageUrl"]))
    posted = clean_text(pick_first(item, ["postedAt", "posted", "date", "publishedAt"]))

    if not title or not source_url:
        return None

    company = company or "Company not specified"
    location = detect_city(location_raw, description, title, source_url)
    remote = detect_remote_mode(location_raw, description, title)
    duration = detect_duration(description, title)
    field, skills, match_score = classify_internship(title, description)
    source_name = extract_source_name(source_url, item)
    stable_id = build_stable_id(title, company, source_url)
    long_description = description or DEFAULT_DESCRIPTION

    return {
        "id": stable_id,
        "role": title,
        "company": company,
        "logo": make_company_logo(company),
        "logoBg": choose_logo_gradient(stable_id),
        "location": location,
        "remote": remote,
        "duration": duration,
        "field": field,
        "skills": skills,
        "match": match_score,
        "posted": posted or "Recently posted",
        "stipend": "Not specified",
        "description": shorten_text(long_description, 180),
        "longDescription": long_description,
        "responsibilities": generate_responsibilities(field, long_description, skills),
        "requirements": generate_requirements(field, skills),
        "niceToHave": generate_nice_to_have(field, skills),
        "perks": [
            "Real internship experience",
            "Mentorship opportunity",
            "Public listing source",
        ],
        "aboutCompany": f"{company} appears in a public internship listing sourced from {source_name}.",
        "applicationProcess": [
            {"step": "Apply", "desc": "Apply through source link."},
            {"step": "Review", "desc": "Company review."},
            {"step": "Interview", "desc": "Interview."},
        ],
        "openings": 1,
        "startDate": "Not specified",
        "teamSize": "Not specified",
        "sourceUrl": source_url,
    }

def infer_company_from_url(source_url: str) -> str:
    hostname = urlparse(source_url).netloc.lower().replace("www.", "")
    if not hostname:
        return ""

    domain_name = hostname.split(".")[0]
    known_sources = {
        "rekrute": "Rekrute",
        "emploi": "Emploi.ma",
        "linkedin": "LinkedIn",
        "indeed": "Indeed",
        "glassdoor": "Glassdoor",
    }

    return known_sources.get(domain_name, domain_name.replace("-", " ").title())


def get_query_text(item: dict[str, Any]) -> str:
    for key in ["searchQuery", "query", "searchTerm", "searchTerms"]:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            text = pick_first(value, ["term", "query", "searchTerm", "text"])
            if text:
                return text
    return ""


def flatten_apify_results(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    The Apify Google Search Scraper returns one dataset item per search page.
    The real Google results are usually inside item["organicResults"].

    This function converts:
    [
      {"searchQuery": "...", "organicResults": [{title, url, description}, ...]}
    ]

    into:
    [
      {title, url, description, company, searchQuery},
      ...
    ]
    """
    candidates: list[dict[str, Any]] = []

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        query_text = get_query_text(item)
        found_nested_results = False

        for nested_key in ["organicResults", "paidResults"]:
            nested_results = item.get(nested_key)

            if isinstance(nested_results, list):
                found_nested_results = True
                for result in nested_results:
                    if not isinstance(result, dict):
                        continue

                    candidate = dict(result)

                    title = pick_first(candidate, ["title", "name", "jobTitle", "positionName"])
                    source_url = pick_first(candidate, ["url", "link", "pageUrl"])
                    description = pick_first(candidate, ["description", "snippet", "text", "content"])

                    candidate["title"] = title
                    candidate["url"] = source_url
                    candidate["description"] = description
                    candidate["searchQuery"] = query_text

                    if not candidate.get("company"):
                        candidate["company"] = infer_company_from_url(source_url)

                    if title and source_url:
                        candidates.append(candidate)

        # If the actor ever returns direct job objects instead of nested Google results,
        # keep supporting that too.
        if not found_nested_results:
            candidate = dict(item)
            title = pick_first(candidate, ["title", "name", "jobTitle", "positionName"])
            source_url = pick_first(candidate, ["url", "link", "pageUrl"])
            description = pick_first(candidate, ["description", "snippet", "text", "content"])

            candidate["title"] = title
            candidate["url"] = source_url
            candidate["description"] = description
            candidate["searchQuery"] = query_text

            if not candidate.get("company"):
                candidate["company"] = infer_company_from_url(source_url)

            if title and source_url:
                candidates.append(candidate)

    return candidates

def merge_internships(existing: list[dict[str, Any]], new_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, int]:
    merged = list(existing)
    existing_source_urls = {
        normalize_compare(str(item.get("sourceUrl", "")))
        for item in existing
        if normalize_compare(str(item.get("sourceUrl", "")))
    }
    existing_role_company = {
        (normalize_compare(str(item.get("role", item.get("title", "")))), normalize_compare(str(item.get("company", ""))))
        for item in existing
    }

    added = 0
    skipped = 0
    for item in new_items:
        source_url_key = normalize_compare(str(item.get("sourceUrl", "")))
        role_company_key = (
            normalize_compare(str(item.get("role", ""))),
            normalize_compare(str(item.get("company", ""))),
        )

        if source_url_key and source_url_key in existing_source_urls:
            skipped += 1
            continue

        if role_company_key in existing_role_company:
            skipped += 1
            continue

        merged.append(item)
        added += 1
        if source_url_key:
            existing_source_urls.add(source_url_key)
        existing_role_company.add(role_company_key)

    return merged, added, skipped


def build_actor_input(queries: list[str], limit: int) -> dict[str, Any]:
    # This input is for the official Apify actor:
    # apify/google-search-scraper
    #
    # The actor expects search queries as one text value with each query
    # separated by a new line, similar to how the Apify website input box works.
    actor_input = {
        "queries": "\n".join(queries),
        "maxPagesPerQuery": 1,
        "resultsPerPage": 10,
        "countryCode": "ma",
        "languageCode": "fr",
        "mobileResults": False,
        "includeUnfilteredResults": False,
        "saveHtml": False,
        "saveHtmlToKeyValueStore": False,
    }
    return actor_input


def run_apify_search(limit: int) -> list[dict[str, Any]]:
    load_dotenv()
    token = os.getenv("APIFY_API_TOKEN", "").strip()
    if not token:
        raise RuntimeError("APIFY_API_TOKEN is missing. Add it to your .env file before running the script.")

    actor_id = os.getenv("APIFY_ACTOR_ID", "").strip() or DEFAULT_ACTOR_ID
    client = ApifyClient(token)
    actor_input = build_actor_input(SEARCH_QUERIES, limit)

    print(f"[info] Using actor: {actor_id}")
    print(f"[info] Queries: {len(SEARCH_QUERIES)}")
    print(f"[info] Requested limit per query: {limit}")

    run = client.actor(actor_id).call(run_input=actor_input)
    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise RuntimeError("Apify run finished but no dataset was returned.")

    print(f"[info] Reading dataset: {dataset_id}")
    items = list(client.dataset(dataset_id).iterate_items())
    print(f"[info] Retrieved {len(items)} raw items from Apify.")
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update Internyx internships using public Apify search results.")
    parser.add_argument("--limit", type=int, help="Maximum results to request per search query.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing internships.json.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv()

    env_limit = os.getenv("APIFY_MAX_RESULTS", str(DEFAULT_MAX_RESULTS)).strip()
    limit = args.limit or int(env_limit or DEFAULT_MAX_RESULTS)

    print("[info] Loading existing internships...")
    existing = safe_load_internships()
    print(f"[info] Existing internships found: {len(existing)}")

    try:
        raw_items = run_apify_search(limit=limit)
    except Exception as exc:
        print(f"[error] Could not fetch data from Apify: {exc}")
        return 1

    candidate_items = flatten_apify_results(raw_items)
    print(f"[info] Candidate listings after flattening search results: {len(candidate_items)}")

    normalized_items: list[dict[str, Any]] = []
    rejected = 0
    for raw_item in candidate_items:
        if not isinstance(raw_item, dict):
            rejected += 1
            continue
        normalized = normalize_apify_item(raw_item)
        if not normalized:
            rejected += 1
            continue
        normalized_items.append(normalized)

    print(f"[info] Normalized internships: {len(normalized_items)}")
    print(f"[info] Rejected raw items: {rejected}")

    merged, added, skipped = merge_internships(existing, normalized_items)
    print(f"[info] New internships to add: {added}")
    print(f"[info] Duplicates skipped: {skipped}")
    print(f"[info] Final internship count would be: {len(merged)}")

    if args.dry_run:
        print("[info] Dry run enabled. No files were changed.")
        return 0

    save_internships(merged)
    print(f"[success] Updated {DATA_FILE} with {added} new internships.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
