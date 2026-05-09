import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


def test_main_pages_render(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    client = app.test_client()
    for path in ["/", "/about", "/internships", "/career-paths", "/profile"]:
        response = client.get(path)
        assert response.status_code == 200
        assert b"Internyx" in response.data


def test_internship_detail_apply_and_save(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    client = app.test_client()
    detail = client.get("/internships/1")
    assert detail.status_code == 200
    assert b"Frontend Developer Intern" in detail.data

    saved = client.post("/internships/1/save", follow_redirects=True)
    assert saved.status_code == 200
    assert b"Saved" in saved.data

    applied = client.post("/internships/1/apply", data={"name": "Test User", "email": "test@example.com", "note": "Interested"}, follow_redirects=True)
    assert applied.status_code == 200
    assert b"Application submitted" in applied.data


def test_filter_search(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    client = app.test_client()
    response = client.get("/internships?q=Flutter")
    assert response.status_code == 200
    assert b"Mobile Developer Intern" in response.data
    assert b"Frontend Developer Intern" not in response.data
