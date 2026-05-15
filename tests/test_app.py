import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module


@pytest.fixture()
def client_with_temp_data(tmp_path, monkeypatch):
    source_data = json.loads((Path(__file__).resolve().parents[1] / "data" / "internships.json").read_text(encoding="utf-8"))
    temp_data_file = tmp_path / "internships.json"
    temp_data_file.write_text(json.dumps(source_data, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.setattr(app_module, "DATA_FILE", temp_data_file)

    app = app_module.create_app({"TESTING": True})
    return app.test_client(), temp_data_file


def test_main_pages_render(client_with_temp_data):
    client, _ = client_with_temp_data
    for path in ["/", "/about", "/internships", "/career-paths", "/profile"]:
        response = client.get(path)
        assert response.status_code == 200
        assert b"Internyx" in response.data


def test_internship_detail_apply_and_save(client_with_temp_data):
    client, _ = client_with_temp_data

    detail = client.get("/internships/1")
    assert detail.status_code == 200
    assert b"Frontend Developer Intern" in detail.data

    saved = client.post("/internships/1/save", follow_redirects=True)
    assert saved.status_code == 200
    assert b"Saved" in saved.data

    applied = client.post(
        "/internships/1/apply",
        data={"name": "Test User", "email": "test@example.com", "note": "Interested"},
        follow_redirects=True,
    )
    assert applied.status_code == 200
    assert b"Application submitted" in applied.data


def test_search_field_and_skill_filters(client_with_temp_data):
    client, _ = client_with_temp_data

    search_response = client.get("/internships?q=Flutter")
    assert search_response.status_code == 200
    assert b"Mobile Developer Intern" in search_response.data
    assert b"Frontend Developer Intern" not in search_response.data

    field_response = client.get("/internships?field=Marketing")
    assert field_response.status_code == 200
    assert b"Marketing Intern" in field_response.data
    assert b"Frontend Developer Intern" not in field_response.data

    skill_response = client.get("/internships?skill=SQL")
    assert skill_response.status_code == 200
    assert b"Data Analyst Intern" in skill_response.data
    assert b"Marketing Intern" not in skill_response.data


def test_internships_route_reads_latest_json(client_with_temp_data):
    client, temp_data_file = client_with_temp_data

    updated_data = json.loads(temp_data_file.read_text(encoding="utf-8"))
    updated_data.append(
        {
            "id": "apify-test-1",
            "role": "Cybersecurity Intern",
            "company": "Public Listing Co",
            "logo": "PLC",
            "logoBg": "from-primary to-clay",
            "location": "Rabat",
            "remote": "Hybrid",
            "duration": "3 months",
            "field": "Cybersecurity",
            "skills": ["Cybersecurity", "SOC"],
            "match": 83,
            "posted": "Recently posted",
            "stipend": "Not specified",
            "description": "Assist with security monitoring and incident reporting.",
            "longDescription": "Assist with security monitoring and incident reporting for a public internship listing.",
            "responsibilities": ["Assist with security monitoring."],
            "requirements": ["Interest in cybersecurity."],
            "niceToHave": ["Communication"],
            "perks": ["Real internship experience"],
            "aboutCompany": "Public Listing Co is shown from a public source.",
            "applicationProcess": [{"step": "Apply", "desc": "Apply through source link."}],
            "openings": 1,
            "startDate": "Not specified",
            "teamSize": "Not specified",
            "sourceUrl": "https://example.com/cybersecurity-intern",
        }
    )
    temp_data_file.write_text(json.dumps(updated_data, ensure_ascii=False, indent=2), encoding="utf-8")

    response = client.get("/internships?skill=SOC")
    assert response.status_code == 200
    assert b"Cybersecurity Intern" in response.data
