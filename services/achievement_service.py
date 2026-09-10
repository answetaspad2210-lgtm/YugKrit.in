"""
YugKrit - Achievement engine.

When a project is marked COMPLETED and verification is done, this module
automatically walks the database relationships (Project -> ProjectTeam ->
ProjectTeamMember -> StudentProfile) and:
  1. Creates an Achievement record per student for this project.
  2. Makes the student eligible for a certificate.
Nothing is manually copied — everything is derived from relationships, so
the Student Growth Profile always reflects the true state of the database.
"""

from database.database import db
from database.models import Achievement, StudentAchievement, Certificate
from utils.helpers import generate_code
from services.notification_service import notify

ACHIEVEMENT_DEFS = {
    "PROJECT_COMPLETED": ("Completed Verified Project", "fa-circle-check"),
    "COMMUNITY_VALIDATED": ("Community Validated Solution", "fa-users"),
    "PROTOTYPE_DEVELOPED": ("Prototype Developed", "fa-flask"),
    "FIELD_IMPLEMENTED": ("Field Implementation", "fa-map-location-dot"),
}


def _get_or_create_achievement_def(code):
    achievement = Achievement.query.filter_by(code=code).first()
    if not achievement:
        title, icon = ACHIEVEMENT_DEFS.get(code, (code.replace("_", " ").title(), "fa-award"))
        achievement = Achievement(code=code, title=title, description=title, icon=icon)
        db.session.add(achievement)
        db.session.flush()
    return achievement


def generate_achievements_for_project(project):
    codes = ["PROJECT_COMPLETED"]
    prototype_milestone = next((m for m in project.milestones if m.title == "Prototype"), None)
    if prototype_milestone and prototype_milestone.status == "COMPLETED":
        codes.append("PROTOTYPE_DEVELOPED")
    validation_milestone = next((m for m in project.milestones if m.title == "Community Validation"), None)
    if validation_milestone and validation_milestone.status == "COMPLETED":
        codes.append("COMMUNITY_VALIDATED")
    implementation_milestone = next((m for m in project.milestones if m.title == "Implementation"), None)
    if implementation_milestone and implementation_milestone.status == "COMPLETED":
        codes.append("FIELD_IMPLEMENTED")

    for team in project.teams:
        for member in team.members:
            student = member.student
            for code in codes:
                achievement_def = _get_or_create_achievement_def(code)
                exists = StudentAchievement.query.filter_by(
                    student_id=student.id, achievement_id=achievement_def.id, project_id=project.id
                ).first()
                if not exists:
                    db.session.add(StudentAchievement(
                        student_id=student.id, achievement_id=achievement_def.id, project_id=project.id
                    ))
            _issue_certificate(student, project, member.role_in_team)
            if student.user:
                notify(student.user, "Achievement unlocked!",
                       f'Your work on "{project.name}" has been added to your innovation profile.',
                       link="/dashboard/student/achievements")
    db.session.commit()


def _issue_certificate(student, project, role_in_team):
    existing = Certificate.query.filter_by(student_id=student.id, project_id=project.id).first()
    if existing:
        return existing
    cert = Certificate(
        certificate_id=generate_code("CERT"),
        student_id=student.id,
        project_id=project.id,
        role_in_project=role_in_team,
    )
    db.session.add(cert)
    db.session.flush()
    if student.user:
        notify(student.user, "Certificate generated",
               f'Your certificate for "{project.name}" is ready.',
               link=f"/verify/certificate/{cert.certificate_id}")
    return cert
