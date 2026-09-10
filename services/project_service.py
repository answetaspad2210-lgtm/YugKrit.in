"""YugKrit - Project / team / milestone service."""

from database.database import db
from database.models import (
    Project, ProjectTeam, ProjectTeamMember, Milestone, ProjectImpact
)
from utils.helpers import generate_code
from services.audit_service import log_action
from services.notification_service import notify
from services import student_service, achievement_service

DEFAULT_MILESTONES = [
    "Problem Research", "Solution Design", "Prototype", "Testing",
    "Community Validation", "Pilot", "Implementation", "Final Submission",
]


def create_project(challenge, university, faculty, data):
    project = Project(
        project_code=generate_code("PRJ"),
        name=data["name"],
        objective=data.get("objective"),
        description=data.get("description"),
        expected_outcome=data.get("expected_outcome"),
        challenge_id=challenge.id,
        university_id=university.id,
        faculty_mentor_id=faculty.id if faculty else None,
        start_date=data.get("start_date"),
        expected_completion=data.get("expected_completion"),
        status="PLANNING",
    )
    db.session.add(project)
    db.session.flush()

    for i, title in enumerate(DEFAULT_MILESTONES):
        db.session.add(Milestone(project_id=project.id, title=title, sequence=i, status="NOT_STARTED"))

    db.session.add(ProjectImpact(project_id=project.id, people_impacted=0))

    challenge.status = "IN_PROGRESS"
    db.session.commit()
    return project


def create_team(project, team_name, members_data):
    """members_data: list of dicts with full_name, college_email,
    registration_number, role_in_team. Uses find_or_invite_student so no
    duplicate student profiles are ever created."""
    team = ProjectTeam(project_id=project.id, team_name=team_name)
    db.session.add(team)
    db.session.flush()

    created_count = 0
    for m in members_data:
        student, is_new = student_service.find_or_invite_student(
            institution_id=project.university_id,
            registration_number=m["registration_number"],
            full_name=m["full_name"],
            college_email=m["college_email"],
        )
        if is_new:
            created_count += 1
        member = ProjectTeamMember(team_id=team.id, student_id=student.id,
                                    role_in_team=m.get("role_in_team", "Developer"))
        db.session.add(member)
        if student.user:
            notify(student.user, "Added to a project", f'You were added to "{project.name}".',
                   link=f"/dashboard/student/projects/{project.id}")

    db.session.commit()
    return team, created_count


def update_milestone_status(milestone, new_status, comment=None, actor=None):
    previous = milestone.status
    milestone.status = new_status
    if comment:
        milestone.reviewer_comment = comment
    db.session.commit()
    if actor:
        log_action(actor, "MILESTONE_UPDATE", "Milestone", milestone.id, previous, new_status)

    _recalculate_progress(milestone.project)

    if new_status == "COMPLETED":
        all_done = all(m.status == "COMPLETED" for m in milestone.project.milestones)
        if all_done:
            complete_project(milestone.project, actor)
    return milestone


def _recalculate_progress(project):
    stage_map = {
        "Problem Research": "research_progress",
        "Solution Design": "design_progress",
        "Prototype": "prototype_progress",
        "Testing": "testing_progress",
        "Community Validation": "validation_progress",
    }
    status_pct = {
        "NOT_STARTED": 0, "IN_PROGRESS": 40, "SUBMITTED": 70,
        "UNDER_REVIEW": 80, "APPROVED": 90, "CHANGES_REQUESTED": 50, "COMPLETED": 100,
    }
    for m in project.milestones:
        field = stage_map.get(m.title)
        if field:
            setattr(project, field, status_pct.get(m.status, 0))
    db.session.commit()


def complete_project(project, actor=None):
    """Marks a project COMPLETED and triggers the downstream automation:
    achievements -> student profile update -> certificate eligibility."""
    project.status = "COMPLETED"
    db.session.commit()
    if actor:
        log_action(actor, "PROJECT_COMPLETE", "Project", project.id, "IN_PROGRESS", "COMPLETED")
    achievement_service.generate_achievements_for_project(project)
    return project
