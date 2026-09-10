"""Tests for challenge submission and government verification."""

from database.database import db
from services import auth_service, challenge_service


def _make_ulb_org():
    from database.models import Organization, ULB
    org = Organization(name="Test ULB", org_type="ULB", status="VERIFIED")
    db.session.add(org)
    db.session.flush()
    db.session.add(ULB(organization_id=org.id, authorized_officer="Officer"))
    db.session.commit()
    return org


def test_create_challenge_runs_ai_analysis(app):
    with app.app_context():
        org = _make_ulb_org()
        challenge = challenge_service.create_challenge(org, {
            "title": "Water logging near Central Park",
            "description": "Severe water logging affecting daily commute.",
            "category": "Water & Sanitation",
            "affected_population": 1200,
            "urgency": "HIGH",
            "district": "Lucknow", "state": "UP",
        })
        assert challenge.status == "SUBMITTED"
        assert challenge.priority_score > 0
        assert challenge.ai_analysis is not None
        assert challenge.ai_analysis.human_review_required is True


def test_government_verify_and_reject(app):
    with app.app_context():
        org = _make_ulb_org()
        gov_user = auth_service.create_user("Gov", "gov2@test.local", "Demo@123", "GOVERNMENT_ADMIN")
        challenge = challenge_service.create_challenge(org, {
            "title": "Broken streetlights", "description": "Multiple streetlights broken.",
            "category": "Urban Infrastructure", "affected_population": 500, "urgency": "MEDIUM",
        })
        challenge_service.verify_challenge(challenge, gov_user, approve=True)
        assert challenge.status == "VERIFIED"

        challenge2 = challenge_service.create_challenge(org, {
            "title": "Another problem", "description": "Desc", "category": "General",
            "affected_population": 10, "urgency": "LOW",
        })
        challenge_service.verify_challenge(challenge2, gov_user, approve=False, reason="Insufficient evidence")
        assert challenge2.status == "REJECTED"
