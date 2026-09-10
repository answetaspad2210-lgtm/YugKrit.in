"""Tests for authentication and registration."""


def test_login_page_loads(client):
    resp = client.get("/auth/login")
    assert resp.status_code == 200


def test_student_registration_and_login(app, client):
    from database.database import db
    from database.models import Organization, University

    with app.app_context():
        org = Organization(name="Test University", org_type="UNIVERSITY", status="VERIFIED")
        db.session.add(org)
        db.session.flush()
        uni = University(organization_id=org.id, rep_name="Rep")
        db.session.add(uni)
        db.session.commit()
        uni_id = uni.id

    resp = client.post("/auth/register/student", data={
        "full_name": "Test Student", "college_email": "test@student.edu",
        "institution_id": uni_id, "registration_number": "TST2026CS001",
        "password": "Demo@123",
    }, follow_redirects=True)
    assert resp.status_code == 200

    client.get("/auth/logout")
    resp = client.post("/auth/login", data={"email": "test@student.edu", "password": "Demo@123"},
                        follow_redirects=True)
    assert resp.status_code == 200


def test_invalid_login_shows_error(client):
    resp = client.post("/auth/login", data={"email": "nobody@nowhere.com", "password": "wrong"},
                        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data
