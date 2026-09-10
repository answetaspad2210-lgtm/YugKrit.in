"""
YugKrit - Government IT Cell routes.

The IT Cell is the head-of-platform role: it monitors and holds validation /
approval rights over every organization type (Government departments,
Universities, ULBs/NGOs), students, and citizens. Most of that oversight is
already implemented on the Government dashboard (challenges, universities,
ULBs/NGOs, students, projects, approvals, map, analytics, audit) — the IT
Cell role is simply granted access to those same routes (see
`GOV_ROLES` in routes/government_routes.py). This blueprint adds the pieces
that are unique to the IT Cell: a platform-wide overview and citizen
identity verification.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.database import db
from database.models import (
    Organization, University, ULB, NGO, StudentProfile, CitizenProfile,
    Challenge, Project, AuditLog
)
from utils.decorators import role_required, get_current_user
from services import citizen_service

itcell_bp = Blueprint("itcell", __name__, template_folder="../templates/itcell")

IT_CELL_ROLE = ("GOVT_IT_CELL_ADMIN",)


@itcell_bp.route("/")
@role_required(*IT_CELL_ROLE)
def overview():
    stats = {
        "government_depts": Organization.query.filter_by(org_type="GOVERNMENT").count(),
        "universities": University.query.count(),
        "universities_verified": University.query.join(University.organization).filter_by(status="VERIFIED").count(),
        "ulbs_ngos": ULB.query.count() + NGO.query.count(),
        "ulbs_ngos_verified": (ULB.query.join(ULB.organization).filter_by(status="VERIFIED").count()
                                 + NGO.query.join(NGO.organization).filter_by(status="VERIFIED").count()),
        "students": StudentProfile.query.count(),
        "citizens": CitizenProfile.query.count(),
        "citizens_verified": CitizenProfile.query.filter_by(verification_status="VERIFIED").count(),
        "total_challenges": Challenge.query.count(),
        "citizen_challenges": Challenge.query.filter(Challenge.submitted_by_citizen_id.isnot(None)).count(),
        "active_projects": Project.query.filter(Project.status.in_(["PLANNING", "IN_PROGRESS"])).count(),
        "completed_projects": Project.query.filter(Project.status.in_(["COMPLETED", "VERIFIED"])).count(),
    }
    pending_orgs_count = Organization.query.filter(Organization.status.in_(["PENDING", "UNDER_REVIEW"])).count()
    pending_challenges_count = Challenge.query.filter_by(status="SUBMITTED").count()

    recent_activity = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template("itcell/overview.html", stats=stats,
                            pending_orgs_count=pending_orgs_count,
                            pending_challenges_count=pending_challenges_count,
                            recent_activity=recent_activity)


@itcell_bp.route("/citizens")
@role_required(*IT_CELL_ROLE)
def citizens():
    status = request.args.get("status")
    q = CitizenProfile.query.join(CitizenProfile.user)
    if status == "VERIFIED":
        q = q.filter_by(is_phone_verified=True)
    elif status == "PENDING":
        q = q.filter_by(is_phone_verified=False)
    citizen_list = q.order_by(CitizenProfile.created_at.desc()).all()
    return render_template("itcell/citizens.html", citizens=citizen_list, status=status or "")


@itcell_bp.route("/citizens/<int:citizen_id>")
@role_required(*IT_CELL_ROLE)
def citizen_detail(citizen_id):
    citizen = CitizenProfile.query.get_or_404(citizen_id)
    submitted = Challenge.query.filter_by(submitted_by_citizen_id=citizen.id).order_by(
        Challenge.created_at.desc()).all()
    return render_template("itcell/citizen_detail.html", citizen=citizen, submitted=submitted)


@itcell_bp.route("/citizen-challenges")
@role_required(*IT_CELL_ROLE)
def citizen_challenges():
    challenges = Challenge.query.filter(Challenge.submitted_by_citizen_id.isnot(None)).order_by(
        Challenge.created_at.desc()).all()
    return render_template("itcell/citizen_challenges.html", challenges=challenges)
