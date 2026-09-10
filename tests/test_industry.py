"""End-to-end tests for the Industry participant workflow."""

from database.database import db
from database.models import (
    Organization, ULB, University, IndustryProfile, IndustryCollaboration,
    IndustryCollaborationRequest, Notification,
)
from services import auth_service, challenge_service, project_service


def _organization(name, org_type):
    organization = Organization(name=name, org_type=org_type, status="VERIFIED",
                                 state="Jharkhand", district="Ranchi")
    db.session.add(organization)
    db.session.flush()
    return organization


def test_industry_proposal_is_approved_and_linked_to_project(app, client):
    with app.app_context():
        gov_org = _organization("Government Test Office", "GOVERNMENT")
        gov_user = auth_service.create_user("Gov", "industry-gov@test.local", "Demo@123",
                                            "GOVERNMENT_ADMIN", organization_id=gov_org.id)
        ulb_org = _organization("Water ULB", "ULB")
        db.session.add(ULB(organization_id=ulb_org.id, authorized_officer="Officer"))
        uni_org = _organization("Test University", "UNIVERSITY")
        university = University(organization_id=uni_org.id, rep_name="Dean")
        db.session.add(university)
        db.session.flush()
        uni_user = auth_service.create_user("Dean", "industry-uni@test.local", "Demo@123",
                                            "UNIVERSITY_ADMIN", organization_id=uni_org.id)
        uni_user_id = uni_user.id
        industry_org = _organization("WaterTech Partner", "INDUSTRY")
        industry = IndustryProfile(organization_id=industry_org.id, organization_type="Technology Provider",
                                   sector="Water Management", expertise="IoT, water monitoring",
                                   technologies="Sensors, analytics", contact_person="Partner")
        db.session.add(industry)
        db.session.flush()
        industry_user = auth_service.create_user("Partner", "industry@test.local", "Demo@123",
                                                 "INDUSTRY", organization_id=industry_org.id)
        db.session.commit()

        challenge = challenge_service.create_challenge(ulb_org, {
            "title": "Village water monitoring", "description": "Sensor-based water quality reporting",
            "category": "Water & Sanitation", "subcategory": "Drinking water",
            "affected_population": 500, "urgency": "HIGH", "district": "Ranchi", "state": "Jharkhand",
        })
        challenge_service.verify_challenge(challenge, gov_user, approve=True)
        project = project_service.create_project(challenge, university, None, {
            "name": "Water Monitoring Project", "objective": "Deploy sensors",
        })
        project_id = project.id
        challenge_id = challenge.id

    client.post("/auth/login", data={"email": "industry@test.local", "password": "Demo@123"})
    dashboard_response = client.get("/industry/dashboard")
    assert dashboard_response.status_code == 200
    response = client.post(f"/industry/challenges/{challenge_id}/collaborate", data={
        "project_id": project_id, "support_types": ["Technical Mentorship", "Hardware"],
        "description": "Provide sensors and technical mentoring.", "expected_duration": "6 months",
    })
    assert response.status_code == 302

    with app.app_context():
        proposal = IndustryCollaborationRequest.query.one()
        proposal_id = proposal.id
        assert proposal.status == "REQUESTED"
        assert Notification.query.filter_by(user_id=uni_user_id).count() == 1

    client.post("/auth/logout")
    client.post("/auth/login", data={"email": "industry-uni@test.local", "password": "Demo@123"})
    response = client.post(f"/dashboard/university/collaboration-requests/{proposal_id}/review", data={
        "decision": "approve", "project_id": project_id, "review_note": "Approved for the student team.",
    })
    assert response.status_code == 302

    with app.app_context():
        collaboration = IndustryCollaboration.query.one()
        assert collaboration.project_id == project_id
        assert collaboration.status == "ACTIVE"
        assert IndustryCollaborationRequest.query.one().status == "ACTIVE"
        assert Notification.query.filter_by(title="Collaboration approved").count() == 1


def test_non_industry_cannot_access_industry_dashboard(app, client):
    with app.app_context():
        user = auth_service.create_user("Citizen", "industry-citizen@test.local", "Demo@123", "CITIZEN")
    client.post("/auth/login", data={"email": "industry-citizen@test.local", "password": "Demo@123"})
    response = client.get("/industry/dashboard")
    assert response.status_code == 302
