"""YugKrit - Certificate lookup / public verification service."""

from database.models import Certificate


def get_certificate_by_public_id(certificate_id):
    return Certificate.query.filter_by(certificate_id=certificate_id).first()


def certificate_to_dict(cert):
    return {
        "certificate_id": cert.certificate_id,
        "student_name": cert.student.full_name,
        "project_name": cert.project.name,
        "role": cert.role_in_project,
        "university": cert.project.university.organization.name,
        "faculty_mentor": (cert.project.faculty_mentor.user.full_name
                            if cert.project.faculty_mentor else "N/A"),
        "issued_date": cert.issued_date.strftime("%d %b %Y") if cert.issued_date else "",
        "valid": True,
    }
