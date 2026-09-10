"""Tests for project creation, team building, and milestone -> achievement -> certificate flow."""

from datetime import date
from database.database import db
from services import auth_service, challenge_service, project_service


def _setup_project():
    from database.models import Organization, University, ULB, Faculty

    ulb_org = Organization(name="ULB", org_type="ULB", status="VERIFIED")
    uni_org = Organization(name="Uni", org_type="UNIVERSITY", status="VERIFIED")
    db.session.add_all([ulb_org, uni_org])
    db.session.flush()
    db.session.add(ULB(organization_id=ulb_org.id, authorized_officer="Officer"))
    university = University(organization_id=uni_org.id, rep_name="Rep")
    db.session.add(university)
    db.session.commit()

    gov_user = auth_service.create_user("Gov", "gov3@test.local", "Demo@123", "GOVERNMENT_ADMIN")
    faculty_user = auth_service.create_user("Fac", "fac3@test.local", "Demo@123", "FACULTY",
                                              organization_id=uni_org.id)
    faculty = Faculty(user_id=faculty_user.id, university_id=university.id, department="CS")
    db.session.add(faculty)
    db.session.commit()

    challenge = challenge_service.create_challenge(ulb_org, {
        "title": "Test Challenge", "description": "Desc", "category": "General",
        "affected_population": 100, "urgency": "MEDIUM",
    })
    challenge_service.verify_challenge(challenge, gov_user, approve=True)
    challenge_service.assign_challenge(challenge, gov_user, university_id=university.id)

    project = project_service.create_project(challenge, university, faculty, {
        "name": "Test Project", "start_date": date(2026, 1, 1),
    })
    return project, university


def test_team_creation_links_and_never_duplicates(app):
    with app.app_context():
        project, university = _setup_project()
        members = [
            {"full_name": "Student A", "college_email": "a@uni.edu",
             "registration_number": "UNI2026CS001", "role_in_team": "Team Leader"},
        ]
        team1, new_count1 = project_service.create_team(project, "Team 1", members)
        assert new_count1 == 1

        team2, new_count2 = project_service.create_team(project, "Team 2", members)
        assert new_count2 == 0

        from database.models import StudentProfile
        count = StudentProfile.query.filter_by(
            institution_id=university.id, registration_number="UNI2026CS001").count()
        assert count == 1


def test_milestone_completion_triggers_achievements_and_certificates(app):
    with app.app_context():
        project, university = _setup_project()
        members = [
            {"full_name": "Student B", "college_email": "b@uni.edu",
             "registration_number": "UNI2026CS002", "role_in_team": "Developer"},
        ]
        project_service.create_team(project, "Team 1", members)

        for m in project.milestones:
            project_service.update_milestone_status(m, "COMPLETED")

        db.session.refresh(project)
        assert project.status == "COMPLETED"

        from database.models import StudentAchievement, Certificate
        assert StudentAchievement.query.count() > 0
        assert Certificate.query.count() == 1
