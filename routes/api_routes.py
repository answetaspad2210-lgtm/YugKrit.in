"""
YugKrit - JSON REST API.

These endpoints mirror the server-rendered routes so the same backend can
power future mobile apps or a JS-heavy frontend. All responses follow:

    { "success": true, "data": ... }
    { "success": false, "error": { "code": ..., "message": ... } }
"""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Blueprint, request, session
from database.database import db
from database.models import (
    Challenge, University, ULB, Project, StudentProfile, Milestone,
    StudentAchievement, AuditLog, ChallengeCategory, IndustryProfile,
    IndustryCollaborationRequest
)
from utils.decorators import login_required, role_required, get_current_user
from utils.helpers import api_success, api_error
from utils.validators import ValidationError
from services import auth_service, challenge_service, project_service, certificate_service
from services.notification_service import notify

api_bp = Blueprint("api", __name__)


def _reverse_from_nominatim(latitude, longitude):
    query = urlencode({
        "format": "jsonv2", "lat": latitude, "lon": longitude,
        "zoom": 10, "addressdetails": 1,
    })
    upstream = Request(
        f"https://nominatim.openstreetmap.org/reverse?{query}",
        headers={"User-Agent": "YugKrit/1.0 civic-impact-platform"},
    )
    with urlopen(upstream, timeout=6) as response:
        payload = json.loads(response.read().decode("utf-8"))
    address = payload.get("address", {})
    return {
        "display_name": payload.get("display_name", ""),
        "city": address.get("city") or address.get("town") or address.get("village") or address.get("municipality") or "",
        "district": address.get("state_district") or address.get("county") or "",
        "state": address.get("state", ""),
    }


def _reverse_from_bigdatacloud(latitude, longitude):
    query = urlencode({
        "latitude": latitude, "longitude": longitude, "localityLanguage": "en",
    })
    upstream = Request(
        f"https://api.bigdatacloud.net/data/reverse-geocode-client?{query}",
        headers={"User-Agent": "YugKrit/1.0 civic-impact-platform"},
    )
    with urlopen(upstream, timeout=6) as response:
        payload = json.loads(response.read().decode("utf-8"))
    informative = payload.get("localityInfo", {}).get("informative", [])
    return {
        "display_name": ", ".join(item.get("name", "") for item in informative[:3] if item.get("name")),
        "city": payload.get("city") or payload.get("locality") or "",
        "district": payload.get("locality") or payload.get("principalSubdivision") or "",
        "state": payload.get("principalSubdivision") or "",
    }


@api_bp.route("/location/reverse", methods=["GET"])
def reverse_location():
    """Resolve browser coordinates without exposing third-party geocoding details to the client."""
    try:
        latitude = float(request.args["lat"])
        longitude = float(request.args["lng"])
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("Coordinates out of range")
        try:
            values = _reverse_from_nominatim(latitude, longitude)
            if any(values.values()):
                return api_success(values)
        except (TimeoutError, OSError, json.JSONDecodeError):
            pass
        try:
            return api_success(_reverse_from_bigdatacloud(latitude, longitude))
        except (TimeoutError, OSError, json.JSONDecodeError):
            return api_success({"display_name": "", "city": "", "district": "", "state": ""})
    except (KeyError, ValueError, TimeoutError, OSError, json.JSONDecodeError):
        return api_success({"display_name": "", "city": "", "district": "", "state": ""})


# --- Auth ---
@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or request.form
    try:
        user = auth_service.authenticate(data.get("email"), data.get("password"))
        session.clear()
        session["user_id"] = user.id
        return api_success({"user_id": user.id, "role": user.role_name()}, "Logged in")
    except ValidationError as e:
        return api_error(e.message, e.code, 401)


@api_bp.route("/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return api_success(message="Logged out")


@api_bp.route("/auth/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or request.form
    try:
        user = auth_service.create_user(data["full_name"], data["email"], data["password"], data["role"])
        return api_success({"user_id": user.id}, "Registered", 201)
    except (ValidationError, KeyError) as e:
        return api_error(getattr(e, "message", "Missing field(s)"), getattr(e, "code", "VALIDATION_ERROR"))


# --- Challenges ---
@api_bp.route("/challenges", methods=["GET"])
def list_challenges():
    q = Challenge.query
    status = request.args.get("status")
    if status:
        q = q.filter_by(status=status)
    challenges = q.order_by(Challenge.created_at.desc()).limit(100).all()
    return api_success([_challenge_dict(c) for c in challenges])


@api_bp.route("/challenges/<int:challenge_id>", methods=["GET"])
def get_challenge(challenge_id):
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return api_error("Challenge not found", "NOT_FOUND", 404)
    return api_success(_challenge_dict(challenge, detail=True))


@api_bp.route("/challenges", methods=["POST"])
@role_required("ULB_ADMIN", "NGO_ADMIN")
def create_challenge_api():
    data = request.get_json(silent=True) or request.form
    user = get_current_user()
    try:
        challenge = challenge_service.create_challenge(user.organization, data)
        return api_success(_challenge_dict(challenge), "Challenge submitted", 201)
    except (ValidationError, KeyError) as e:
        return api_error(getattr(e, "message", "Invalid data"), status=400)


@api_bp.route("/challenges/<int:challenge_id>/verify", methods=["POST"])
@role_required("GOVERNMENT_ADMIN", "GOVERNMENT_OFFICER", "GOVT_IT_CELL_ADMIN")
def verify_challenge_api(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    data = request.get_json(silent=True) or request.form
    approve = data.get("approve", True) in (True, "true", "1", 1)
    challenge_service.verify_challenge(challenge, get_current_user(), approve=approve, reason=data.get("reason"))
    return api_success(_challenge_dict(challenge), "Updated")


@api_bp.route("/challenges/<int:challenge_id>/assign", methods=["POST"])
@role_required("GOVERNMENT_ADMIN", "GOVERNMENT_OFFICER", "GOVT_IT_CELL_ADMIN")
def assign_challenge_api(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    data = request.get_json(silent=True) or request.form
    challenge_service.assign_challenge(challenge, get_current_user(),
                                        university_id=data.get("university_id"))
    return api_success(_challenge_dict(challenge), "Assigned")


def _challenge_dict(c, detail=False):
    base = {
        "id": c.id, "code": c.challenge_code, "title": c.title,
        "category": c.category.name if c.category else None,
        "status": c.status, "priority_score": c.priority_score, "urgency": c.urgency,
        "affected_population": c.affected_population,
    }
    if detail:
        base.update({
            "description": c.description,
            "address": c.location.address if c.location else None,
            "district": c.location.district if c.location else None,
            "state": c.location.state if c.location else None,
            "latitude": c.location.latitude if c.location else None,
            "longitude": c.location.longitude if c.location else None,
            "assigned_university": c.assigned_university.organization.name if c.assigned_university else None,
        })
    return base


# --- Industry ---
@api_bp.route("/industry/recommendations", methods=["GET"])
@role_required("INDUSTRY")
def industry_recommendations_api():
    from routes.industry_routes import _industry, _recommended_challenges
    profile = _industry()
    values = _recommended_challenges(profile) if profile else []
    return api_success([{"challenge": _challenge_dict(item["challenge"], detail=True),
                         "match_score": item["score"], "reason": item["reason"]} for item in values])


@api_bp.route("/industry/collaboration-requests", methods=["GET", "POST"])
@role_required("INDUSTRY")
def industry_collaboration_requests_api():
    from routes.industry_routes import _industry
    profile = _industry()
    if request.method == "GET":
        requests = IndustryCollaborationRequest.query.filter_by(industry_id=profile.id).order_by(
            IndustryCollaborationRequest.created_at.desc()).all()
        return api_success([{"id": item.id, "challenge_id": item.challenge_id, "project_id": item.project_id,
                             "status": item.status, "support_types": item.support_types} for item in requests])
    data = request.get_json(silent=True) or request.form
    challenge = Challenge.query.get_or_404(data.get("challenge_id"))
    project = Project.query.get(data.get("project_id")) if data.get("project_id") else None
    support_types = data.get("support_types", [])
    if isinstance(support_types, str):
        support_types = [value.strip() for value in support_types.split(",") if value.strip()]
    if challenge.status not in ("VERIFIED", "ASSIGNED", "IN_PROGRESS") or not support_types or not data.get("description"):
        return api_error("A verified challenge, support types, and description are required.", "VALIDATION_ERROR")
    proposal = IndustryCollaborationRequest(
        industry_id=profile.id, challenge_id=challenge.id, project_id=project.id if project else None,
        university_id=project.university_id if project else challenge.assigned_university_id,
        proposal_type=data.get("proposal_type", "Industry collaboration"),
        support_types=", ".join(support_types), description=data["description"],
        estimated_contribution=data.get("estimated_contribution"), expected_duration=data.get("expected_duration"),
        experts=data.get("experts"), budget=data.get("budget") or None,
    )
    db.session.add(proposal)
    db.session.commit()
    if proposal.university:
        for user in proposal.university.organization.users:
            notify(user, "Industry collaboration request", f"{profile.organization.name} proposed support for {challenge.title}.",
                   link=f"/dashboard/university/collaboration-requests/{proposal.id}")
    return api_success({"id": proposal.id, "status": proposal.status}, "Proposal submitted", 201)


# --- Universities / ULBs ---
@api_bp.route("/universities", methods=["GET"])
def list_universities():
    unis = University.query.join(University.organization).all()
    return api_success([{"id": u.id, "name": u.organization.name, "status": u.organization.status} for u in unis])


@api_bp.route("/ulbs", methods=["GET"])
def list_ulbs():
    ulbs = ULB.query.join(ULB.organization).all()
    return api_success([{"id": u.id, "name": u.organization.name, "status": u.organization.status} for u in ulbs])


# --- Students ---
@api_bp.route("/students/<int:student_id>", methods=["GET"])
@login_required
def get_student(student_id):
    from services.student_service import get_growth_profile
    student = StudentProfile.query.get_or_404(student_id)
    growth = get_growth_profile(student)
    return api_success({
        "id": student.id, "name": student.full_name, "institution": student.institution.organization.name,
        "projects_completed": growth["projects_completed"], "certificates": growth["certificates"],
        "skills": growth["skills"],
    })


# --- Projects ---
@api_bp.route("/projects", methods=["GET"])
@login_required
def list_projects():
    projects = Project.query.order_by(Project.created_at.desc()).limit(100).all()
    return api_success([{"id": p.id, "code": p.project_code, "name": p.name, "status": p.status} for p in projects])


@api_bp.route("/projects/<int:project_id>", methods=["GET"])
@login_required
def get_project(project_id):
    p = Project.query.get_or_404(project_id)
    return api_success({
        "id": p.id, "name": p.name, "status": p.status,
        "challenge": p.challenge.title, "university": p.university.organization.name,
        "progress": {
            "research": p.research_progress, "design": p.design_progress,
            "prototype": p.prototype_progress, "testing": p.testing_progress,
            "validation": p.validation_progress,
        },
    })


@api_bp.route("/milestones/<int:milestone_id>/submit", methods=["POST"])
@role_required("STUDENT")
def submit_milestone(milestone_id):
    m = Milestone.query.get_or_404(milestone_id)
    project_service.update_milestone_status(m, "SUBMITTED", actor=get_current_user())
    return api_success(message="Milestone submitted for review")


@api_bp.route("/milestones/<int:milestone_id>/approve", methods=["POST"])
@role_required("FACULTY", "UNIVERSITY_ADMIN")
def approve_milestone(milestone_id):
    m = Milestone.query.get_or_404(milestone_id)
    project_service.update_milestone_status(m, "COMPLETED", actor=get_current_user())
    return api_success(message="Milestone approved")


# --- Achievements / Certificates ---
@api_bp.route("/achievements/<int:student_id>", methods=["GET"])
@login_required
def get_achievements(student_id):
    items = StudentAchievement.query.filter_by(student_id=student_id).all()
    return api_success([{"title": a.achievement.title, "project": a.project.name if a.project else None}
                         for a in items])


@api_bp.route("/certificates/<certificate_id>", methods=["GET"])
def get_certificate(certificate_id):
    cert = certificate_service.get_certificate_by_public_id(certificate_id)
    if not cert:
        return api_error("Certificate not found", "NOT_FOUND", 404)
    return api_success(certificate_service.certificate_to_dict(cert))


@api_bp.route("/certificates/<certificate_id>/verify", methods=["GET"])
def verify_certificate_api(certificate_id):
    cert = certificate_service.get_certificate_by_public_id(certificate_id)
    if not cert:
        return api_success({"valid": False})
    return api_success(certificate_service.certificate_to_dict(cert))


# --- Notifications ---
@api_bp.route("/notifications", methods=["GET"])
@login_required
def get_notifications():
    from database.models import Notification
    user = get_current_user()
    notes = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(30).all()
    return api_success([{"id": n.id, "title": n.title, "message": n.message, "is_read": n.is_read,
                          "link": n.link} for n in notes])


@api_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def read_notification(notification_id):
    from services.notification_service import mark_read
    mark_read(get_current_user(), notification_id)
    return api_success(message="Marked read")


# --- Analytics / Audit ---
@api_bp.route("/analytics", methods=["GET"])
@role_required("GOVERNMENT_ADMIN", "GOVERNMENT_OFFICER", "UNIVERSITY_ADMIN")
def analytics_api():
    from sqlalchemy import func
    by_category = dict(db.session.query(ChallengeCategory.name, func.count(Challenge.id))
                        .join(Challenge, Challenge.category_id == ChallengeCategory.id)
                        .group_by(ChallengeCategory.name).all())
    by_status = dict(db.session.query(Challenge.status, func.count(Challenge.id)).group_by(Challenge.status).all())
    return api_success({"by_category": by_category, "by_status": by_status})


@api_bp.route("/audit", methods=["GET"])
@role_required("GOVERNMENT_ADMIN")
def audit_api():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return api_success([{"action": l.action, "entity": l.entity, "entity_id": l.entity_id,
                          "role": l.role_name, "timestamp": l.timestamp.isoformat()} for l in logs])
