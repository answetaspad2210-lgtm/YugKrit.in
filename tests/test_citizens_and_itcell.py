"""Tests for the Citizen dashboard (Aadhaar identity) and Government IT Cell
head-of-platform role."""

import pytest
from database.database import db
from services import auth_service, citizen_service


def test_aadhaar_is_never_stored_in_full(app):
    with app.app_context():
        user = auth_service.create_user("Aadhaar Test", "aadhaar1@test.local", "Demo@123", "CITIZEN")
        profile = citizen_service.register_citizen(user, "123456789012")
        assert profile.aadhaar_last4 == "9012"
        assert len(profile.aadhaar_hash) == 64  # sha256 hex digest length
        assert "123456789012" not in profile.aadhaar_hash
        assert profile.masked_aadhaar() == "XXXX-XXXX-9012"
        assert profile.verification_status == "PENDING"


def test_duplicate_aadhaar_is_rejected(app):
    with app.app_context():
        from utils.validators import ValidationError

        user1 = auth_service.create_user("First", "first@test.local", "Demo@123", "CITIZEN")
        citizen_service.register_citizen(user1, "111122223333")

        user2 = auth_service.create_user("Second", "second@test.local", "Demo@123", "CITIZEN")
        with pytest.raises(ValidationError):
            citizen_service.register_citizen(user2, "111122223333")


def test_invalid_aadhaar_format_rejected(app):
    with app.app_context():
        from utils.validators import ValidationError

        user = auth_service.create_user("Bad Aadhaar", "bad@test.local", "Demo@123", "CITIZEN")
        with pytest.raises(ValidationError):
            citizen_service.register_citizen(user, "12345")  # too short


def test_it_cell_can_verify_citizen(app):
    with app.app_context():
        it_cell_user = auth_service.create_user("IT Cell Officer", "itcell1@test.local", "Demo@123",
                                                   "GOVT_IT_CELL_ADMIN")
        citizen_user = auth_service.create_user("Citizen X", "citizenx@test.local", "Demo@123", "CITIZEN")
        profile = citizen_service.register_citizen(citizen_user, "444455556666")

        citizen_service.verify_citizen(profile, it_cell_user, approve=True)
        assert profile.verification_status == "VERIFIED"
        assert profile.verified_by_id == it_cell_user.id


def test_unverified_citizen_cannot_post_problem(app, client):
    with app.app_context():
        user = auth_service.create_user("Unverified Citizen", "unverified@test.local", "Demo@123", "CITIZEN")
        citizen_service.register_citizen(user, "777788889999")

    client.post("/auth/login", data={"email": "unverified@test.local", "password": "Demo@123"})
    resp = client.get("/dashboard/citizen/post-problem", follow_redirects=True)
    assert resp.status_code == 200
    assert b"must be verified" in resp.data


def test_verified_citizen_can_post_problem(app, client):
    with app.app_context():
        it_cell_user = auth_service.create_user("IT Cell Officer 2", "itcell2@test.local", "Demo@123",
                                                   "GOVT_IT_CELL_ADMIN")
        citizen_user = auth_service.create_user("Verified Citizen", "verified@test.local", "Demo@123", "CITIZEN")
        profile = citizen_service.register_citizen(citizen_user, "222233334444")
        citizen_service.verify_citizen(profile, it_cell_user, approve=True)

    client.post("/auth/login", data={"email": "verified@test.local", "password": "Demo@123"})
    resp = client.post("/dashboard/citizen/post-problem", data={
        "title": "Broken drainage", "description": "Water logging near the market.",
        "category": "Water & Sanitation", "address": "Market Road",
        "district": "Test District", "state": "Test State",
        "affected_population": "200", "urgency": "HIGH",
    }, follow_redirects=True)
    assert resp.status_code == 200

    from database.models import Challenge
    with app.app_context():
        challenge = Challenge.query.filter_by(title="Broken drainage").first()
        assert challenge is not None
        assert challenge.submitted_by_citizen_id is not None
        assert challenge.submitted_by_org_id is None


def test_it_cell_has_platform_wide_permissions(app):
    from database.models import Role
    with app.app_context():
        role = Role.query.filter_by(name="GOVT_IT_CELL_ADMIN").first()
        assert role is not None
        codes = {p.code for p in role.permissions}
        assert "citizen.verify" in codes
        assert "organization.verify" in codes
        assert "challenge.verify" in codes
        assert "project.approve" in codes


def test_it_cell_can_access_shared_government_pages(app, client):
    with app.app_context():
        auth_service.create_user("IT Cell Officer 3", "itcell3@test.local", "Demo@123", "GOVT_IT_CELL_ADMIN")

    client.post("/auth/login", data={"email": "itcell3@test.local", "password": "Demo@123"})
    resp = client.get("/dashboard/government/challenges")
    assert resp.status_code == 200
    resp2 = client.get("/dashboard/it-cell/")
    assert resp2.status_code == 200


def test_ulb_and_ngo_share_same_role_and_dashboard(app, client):
    from database.models import Organization, ULB

    with app.app_context():
        ulb_org = Organization(name="Test ULB Merge", org_type="ULB", status="VERIFIED")
        ngo_org = Organization(name="Test NGO Merge", org_type="ULB", status="VERIFIED")
        db.session.add_all([ulb_org, ngo_org])
        db.session.flush()
        db.session.add(ULB(organization_id=ulb_org.id, category="ULB", authorized_officer="Officer A"))
        db.session.add(ULB(organization_id=ngo_org.id, category="NGO", authorized_officer="Officer B"))
        db.session.commit()

        ulb_user = auth_service.create_user("ULB User", "ulbuser@test.local", "Demo@123", "ULB_ADMIN",
                                              organization_id=ulb_org.id)
        ngo_user = auth_service.create_user("NGO User", "ngouser@test.local", "Demo@123", "ULB_ADMIN",
                                              organization_id=ngo_org.id)
        assert ulb_user.role_name() == ngo_user.role_name() == "ULB_ADMIN"

    client.post("/auth/login", data={"email": "ngouser@test.local", "password": "Demo@123"})
    resp = client.get("/dashboard/ulb/")
    assert resp.status_code == 200
