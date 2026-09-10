"""Integration checks for the shared challenge lifecycle across portals."""

from database.database import db
from database.models import Challenge, Organization, University, ULB, UniversityApplication, Notification
from services import auth_service, challenge_service


def test_challenge_lifecycle_notifies_originating_portal(app):
    with app.app_context():
        org = Organization(name="Cross Portal ULB", org_type="ULB", status="VERIFIED")
        db.session.add(org)
        db.session.flush()
        db.session.add(ULB(organization_id=org.id, authorized_officer="Officer"))
        ulb_user = auth_service.create_user("ULB Officer", "cross-ulb@test.local", "Demo@123",
                                            "ULB_ADMIN", organization_id=org.id)
        gov_user = auth_service.create_user("Gov Officer", "cross-gov@test.local", "Demo@123",
                                            "GOVERNMENT_ADMIN")
        challenge = challenge_service.create_challenge(org, {
            "title": "Cross portal water issue", "description": "Shared lifecycle test",
            "category": "Water & Sanitation", "affected_population": 100,
            "urgency": "HIGH", "district": "Ranchi", "state": "Jharkhand",
        })

        challenge_service.verify_challenge(challenge, gov_user, approve=True)
        challenge_service.assign_challenge(challenge, gov_user)

        notifications = Notification.query.filter_by(user_id=ulb_user.id).all()
        assert challenge.status == "VERIFIED"
        assert any("Challenge review completed" == note.title for note in notifications)
        assert all(note.link.startswith("/dashboard/") for note in notifications if note.link)


def test_university_cannot_apply_twice_to_one_challenge(app, client):
    with app.app_context():
        org = Organization(name="Application University", org_type="UNIVERSITY", status="VERIFIED")
        db.session.add(org)
        db.session.flush()
        university = University(organization_id=org.id, rep_name="Rep")
        db.session.add(university)
        ulb_org = Organization(name="Application ULB", org_type="ULB", status="VERIFIED")
        db.session.add(ulb_org)
        db.session.flush()
        db.session.add(ULB(organization_id=ulb_org.id, authorized_officer="Officer"))
        db.session.commit()
        uni_user = auth_service.create_user("University Admin", "application-uni@test.local", "Demo@123",
                                            "UNIVERSITY_ADMIN", organization_id=org.id)
        gov_user = auth_service.create_user("Application Gov", "application-gov@test.local", "Demo@123",
                                            "GOVERNMENT_ADMIN")
        challenge = challenge_service.create_challenge(ulb_org, {
            "title": "Application dedupe issue", "description": "Apply once",
            "category": "General Societal Challenge", "affected_population": 50,
            "urgency": "MEDIUM",
        })
        challenge_service.verify_challenge(challenge, gov_user, approve=True)
        challenge_id = challenge.id

    client.post("/auth/login", data={"email": "application-uni@test.local", "password": "Demo@123"})
    first = client.post(f"/dashboard/university/challenges/{challenge_id}/apply", data={"pitch": "First"})
    second = client.post(f"/dashboard/university/challenges/{challenge_id}/apply", data={"pitch": "Second"})

    with app.app_context():
        assert first.status_code == 302
        assert second.status_code == 302
        assert UniversityApplication.query.filter_by(challenge_id=challenge_id).count() == 1
