"""Tests for role-based access control."""

from services import auth_service


def _make_users(app):
    with app.app_context():
        auth_service.create_user("Gov User", "gov@test.local", "Demo@123", "GOVERNMENT_ADMIN")
        auth_service.create_user("Uni User", "uni@test.local", "Demo@123", "UNIVERSITY_ADMIN")


def test_university_admin_cannot_access_government_dashboard(app, client):
    _make_users(app)
    client.post("/auth/login", data={"email": "uni@test.local", "password": "Demo@123"})
    resp = client.get("/dashboard/government/", follow_redirects=True)
    assert resp.status_code == 200


def test_government_admin_can_access_government_dashboard(app, client):
    _make_users(app)
    client.post("/auth/login", data={"email": "gov@test.local", "password": "Demo@123"})
    resp = client.get("/dashboard/government/")
    assert resp.status_code == 200


def test_unauthenticated_user_redirected_to_login(client):
    resp = client.get("/dashboard/student/")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


def test_role_permissions_are_seeded(app):
    from database.models import Role
    with app.app_context():
        gov_role = Role.query.filter_by(name="GOVERNMENT_ADMIN").first()
        assert gov_role is not None
        codes = {p.code for p in gov_role.permissions}
        assert "challenge.verify" in codes
        assert "organization.verify" in codes
