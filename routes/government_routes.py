"""YugKrit - Government dashboard routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.database import db
from database.models import (
    Challenge, Organization, University, ULB, NGO, Project, AuditLog, ChallengeLocation,
    ChallengeCategory, StudentProfile, CitizenProfile, IndustryProfile,
    IndustryCollaborationRequest, IndustryCollaboration, IndustryFunding
)
from utils.decorators import role_required, get_current_user
from services import challenge_service, verification_service

government_bp = Blueprint("government", __name__, template_folder="../templates/government")

# GOVT_IT_CELL_ADMIN is the platform head-of-office role: it gets full access
# to every existing government page (monitoring, progress tracking, approval
# rights) plus the IT Cell-only pages defined in routes/itcell_routes.py.
GOV_ROLES = ("GOVERNMENT_ADMIN", "GOVERNMENT_OFFICER", "GOVT_IT_CELL_ADMIN")


@government_bp.route("/")
@role_required(*GOV_ROLES)
def overview():
    stats = {
        "total_challenges": Challenge.query.count(),
        "pending_verification": Challenge.query.filter_by(status="SUBMITTED").count(),
        "high_priority": Challenge.query.filter(Challenge.priority_score >= 70).count(),
        "active_projects": Project.query.filter(Project.status.in_(["PLANNING", "IN_PROGRESS"])).count(),
        "completed_projects": Project.query.filter(Project.status.in_(["COMPLETED", "VERIFIED"])).count(),
        "verified_universities": University.query.join(University.organization).filter_by(status="VERIFIED").count(),
        "verified_ulbs_ngos": (ULB.query.join(ULB.organization).filter_by(status="VERIFIED").count()
                                 + NGO.query.join(NGO.organization).filter_by(status="VERIFIED").count()),
        "verified_citizens": CitizenProfile.query.join(CitizenProfile.user).filter_by(is_phone_verified=True).count(),
    }
    recent_challenges = Challenge.query.order_by(Challenge.created_at.desc()).limit(6).all()
    pending_orgs = Organization.query.filter(Organization.status.in_(["PENDING", "UNDER_REVIEW"])).limit(5).all()
    return render_template("government/overview.html", stats=stats,
                            recent_challenges=recent_challenges, pending_orgs=pending_orgs)


@government_bp.route("/challenges")
@role_required(*GOV_ROLES)
def challenges():
    q = Challenge.query
    status = request.args.get("status")
    category = request.args.get("category")
    search = request.args.get("q")
    if status:
        q = q.filter_by(status=status)
    if category:
        q = q.join(ChallengeCategory).filter(ChallengeCategory.name == category)
    if search:
        q = q.filter(Challenge.title.ilike(f"%{search}%"))
    challenge_list = q.order_by(Challenge.created_at.desc()).all()
    categories = ChallengeCategory.query.all()
    return render_template("government/challenges.html", challenges=challenge_list, categories=categories,
                            status=status, category=category, search=search or "")


@government_bp.route("/challenges/<int:challenge_id>")
@role_required(*GOV_ROLES)
def challenge_detail(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    universities = University.query.join(University.organization).filter_by(status="VERIFIED").all()
    audit = AuditLog.query.filter_by(entity="Challenge", entity_id=challenge_id).order_by(AuditLog.timestamp.desc()).all()
    return render_template("government/challenge_detail.html", challenge=challenge,
                            universities=universities, audit=audit)


@government_bp.route("/challenges/<int:challenge_id>/verify", methods=["POST"])
@role_required(*GOV_ROLES)
def verify_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    approve = request.form.get("decision") == "approve"
    reason = request.form.get("reason")
    challenge_service.verify_challenge(challenge, get_current_user(), approve=approve, reason=reason)
    flash(f"Challenge {'verified' if approve else 'rejected'}.", "success" if approve else "warning")
    return redirect(url_for("government.challenge_detail", challenge_id=challenge_id))


@government_bp.route("/challenges/<int:challenge_id>/assign", methods=["POST"])
@role_required(*GOV_ROLES)
def assign_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    university_id = request.form.get("university_id")
    challenge_service.assign_challenge(challenge, get_current_user(),
                                        university_id=int(university_id) if university_id else None,
                                        problem_owner_org_id=challenge.submitted_by_org_id)
    flash("Challenge assigned to university.", "success")
    return redirect(url_for("government.challenge_detail", challenge_id=challenge_id))


@government_bp.route("/universities")
@role_required(*GOV_ROLES)
def universities():
    unis = University.query.join(University.organization).all()
    return render_template("government/universities.html", universities=unis)


@government_bp.route("/ulbs-ngos")
@role_required(*GOV_ROLES)
def ulbs_ngos():
    ulbs = ULB.query.join(ULB.organization).filter(ULB.category == "ULB").all()
    ngos_merged = ULB.query.join(ULB.organization).filter(ULB.category == "NGO").all()
    ngos_legacy = NGO.query.join(NGO.organization).all()  # pre-merge accounts, kept for compatibility
    return render_template("government/ulbs_ngos.html", ulbs=ulbs, ngos_merged=ngos_merged, ngos_legacy=ngos_legacy)


@government_bp.route("/students")
@role_required(*GOV_ROLES)
def students():
    q = StudentProfile.query
    search = request.args.get("q")
    if search:
        q = q.filter(StudentProfile.full_name.ilike(f"%{search}%"))
    student_list = q.order_by(StudentProfile.created_at.desc()).limit(300).all()
    return render_template("government/students.html", students=student_list, search=search or "")


@government_bp.route("/organizations/<int:org_id>/verify", methods=["POST"])
@role_required(*GOV_ROLES)
def verify_organization(org_id):
    org = Organization.query.get_or_404(org_id)
    decision = request.form.get("decision")
    reason = request.form.get("reason")
    status_map = {"approve": "VERIFIED", "reject": "REJECTED", "review": "UNDER_REVIEW"}
    verification_service.set_organization_status(org, get_current_user(), status_map.get(decision, "UNDER_REVIEW"), reason)
    flash(f"Organization status updated to {status_map.get(decision)}.", "success")
    return redirect(request.referrer or url_for("government.universities"))


@government_bp.route("/projects")
@role_required(*GOV_ROLES)
def projects():
    project_list = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("government/projects.html", projects=project_list)


@government_bp.route("/industry")
@role_required(*GOV_ROLES)
def industry_monitoring():
    industries = IndustryProfile.query.join(IndustryProfile.organization).order_by(IndustryProfile.created_at.desc()).all()
    requests = IndustryCollaborationRequest.query.order_by(IndustryCollaborationRequest.created_at.desc()).all()
    collaborations = IndustryCollaboration.query.order_by(IndustryCollaboration.created_at.desc()).all()
    funding = IndustryFunding.query.order_by(IndustryFunding.created_at.desc()).all()
    return render_template("government/industry.html", industries=industries, requests=requests,
                           collaborations=collaborations, funding=funding)


@government_bp.route("/approvals")
@role_required(*GOV_ROLES)
def approvals():
    pending_orgs = Organization.query.filter(Organization.status.in_(["PENDING", "UNDER_REVIEW"])).all()
    pending_challenges = Challenge.query.filter_by(status="SUBMITTED").all()
    return render_template("government/approvals.html", pending_orgs=pending_orgs,
                            pending_challenges=pending_challenges)


@government_bp.route("/map")
@role_required(*GOV_ROLES)
def map_view():
    state = request.args.get("state", "")
    query = ChallengeLocation.query.filter(ChallengeLocation.latitude.isnot(None))
    if state:
        query = query.filter(ChallengeLocation.state == state)
    locations = query.all()
    states = [row[0] for row in db.session.query(ChallengeLocation.state).distinct().order_by(ChallengeLocation.state).all() if row[0]]
    return render_template("government/map.html", locations=locations, states=states, selected_state=state)


@government_bp.route("/analytics")
@role_required(*GOV_ROLES)
def analytics():
    from sqlalchemy import func
    by_category = (db.session.query(ChallengeCategory.name, func.count(Challenge.id))
                    .join(Challenge, Challenge.category_id == ChallengeCategory.id)
                    .group_by(ChallengeCategory.name).all())
    by_status = (db.session.query(Challenge.status, func.count(Challenge.id)).group_by(Challenge.status).all())
    return render_template("government/analytics.html", by_category=by_category, by_status=by_status)


@government_bp.route("/audit")
@role_required("GOVERNMENT_ADMIN", "GOVT_IT_CELL_ADMIN")
def audit_trail():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template("government/audit.html", logs=logs)


@government_bp.route("/settings")
@role_required(*GOV_ROLES)
def settings():
    return render_template("government/settings.html")
