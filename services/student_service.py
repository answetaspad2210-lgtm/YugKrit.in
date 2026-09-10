"""
YugKrit - Student service.

The single most important rule in this whole application:

    A student is uniquely identified by (institution_id, registration_number).

`find_or_invite_student()` is the ONLY function that should ever be used to
attach a student to a project team. It guarantees no duplicate profiles are
ever created.
"""

from database.database import db
from database.models import StudentProfile
from utils.validators import validate_registration_number, validate_email, ValidationError


def find_student(institution_id, registration_number):
    reg_no = validate_registration_number(registration_number)
    return StudentProfile.query.filter_by(
        institution_id=institution_id, registration_number=reg_no
    ).first()


def find_or_invite_student(institution_id, registration_number, full_name, college_email,
                            department=None, course=None, year=None):
    """Look up a student by (institution_id, registration_number).
    If found -> return existing profile (LINK, never duplicate).
    If not found -> create an INVITED profile that becomes ACTIVE once the
    student logs in / registers using the same institution + reg number.
    """
    reg_no = validate_registration_number(registration_number)
    email = validate_email(college_email)

    existing = StudentProfile.query.filter_by(
        institution_id=institution_id, registration_number=reg_no
    ).first()
    if existing:
        return existing, False  # False = not newly created

    student = StudentProfile(
        institution_id=institution_id,
        registration_number=reg_no,
        full_name=full_name.strip(),
        college_email=email,
        department=department,
        course=course,
        year=year,
        status="INVITED",
    )
    db.session.add(student)
    db.session.commit()
    return student, True  # True = newly created / invited


def activate_student_on_registration(user, institution_id, registration_number):
    """Called when a student completes registration/login. Links their User
    account to any pre-existing invited profile, or creates a fresh one."""
    reg_no = validate_registration_number(registration_number)
    profile = StudentProfile.query.filter_by(
        institution_id=institution_id, registration_number=reg_no
    ).first()

    if profile:
        if profile.user_id and profile.user_id != user.id:
            raise ValidationError("This registration number is already linked to another account.",
                                   code="STUDENT_ALREADY_LINKED")
        profile.user_id = user.id
        profile.status = "ACTIVE"
        db.session.commit()
        return profile

    profile = StudentProfile(
        user_id=user.id,
        institution_id=institution_id,
        registration_number=reg_no,
        full_name=user.full_name,
        college_email=user.email,
        status="ACTIVE",
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def get_growth_profile(student):
    """Compute the permanent Innovation Growth Profile shown on the student
    dashboard, derived entirely from relationships (never duplicated data)."""
    memberships = student.team_memberships
    projects = [m.team.project for m in memberships]
    completed_projects = [p for p in projects if p.status in ("COMPLETED", "VERIFIED")]

    people_impacted = 0
    for p in completed_projects:
        if p.impact:
            people_impacted += p.impact.people_impacted or 0

    return {
        "projects_completed": len(completed_projects),
        "problems_addressed": len({p.challenge_id for p in completed_projects}),
        "solutions_proposed": len(projects),
        "certificates": len(student.certificates),
        "skills_count": len(student.skills),
        "people_impacted": people_impacted,
        "skills": [s.skill_name for s in student.skills],
        "projects": projects,
        "achievements": student.achievements,
        "certificates_list": student.certificates,
    }
