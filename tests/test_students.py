"""Tests for the student identity system (institution + registration number)."""

from database.database import db
from services import student_service


def _make_university(name="Dedup University"):
    from database.models import Organization, University
    org = Organization(name=name, org_type="UNIVERSITY", status="VERIFIED")
    db.session.add(org)
    db.session.flush()
    uni = University(organization_id=org.id, rep_name="Rep")
    db.session.add(uni)
    db.session.commit()
    return uni


def test_find_or_invite_creates_once(app):
    with app.app_context():
        uni = _make_university()
        student, is_new = student_service.find_or_invite_student(
            uni.id, "DEDUP2026CS001", "Test Student", "test@dedup.edu")
        assert is_new is True
        assert student.status == "INVITED"


def test_duplicate_registration_number_is_rejected_at_db_level(app):
    """The (institution_id, registration_number) unique constraint must hold
    even if application code is bypassed."""
    with app.app_context():
        from database.models import StudentProfile
        from sqlalchemy.exc import IntegrityError

        uni = _make_university()
        db.session.add(StudentProfile(
            institution_id=uni.id, registration_number="DUP2026CS001",
            full_name="First", college_email="first@dedup.edu"))
        db.session.commit()

        db.session.add(StudentProfile(
            institution_id=uni.id, registration_number="DUP2026CS001",
            full_name="Second (duplicate attempt)", college_email="second@dedup.edu"))
        try:
            db.session.commit()
            assert False, "Expected IntegrityError for duplicate registration number"
        except IntegrityError:
            db.session.rollback()


def test_same_registration_number_different_institution_is_allowed(app):
    with app.app_context():
        uni1 = _make_university("University One")
        uni2 = _make_university("University Two")

        s1, _ = student_service.find_or_invite_student(uni1.id, "SAME001", "Student One", "one@a.edu")
        s2, _ = student_service.find_or_invite_student(uni2.id, "SAME001", "Student Two", "two@b.edu")
        assert s1.id != s2.id
