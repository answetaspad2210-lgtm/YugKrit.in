"""Industry / organization collaboration portal."""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import or_

from database.database import db
from database.models import (
    Challenge, IndustryProfile, IndustryMentor, IndustryCollaborationRequest,
    IndustryCollaboration, IndustryFunding, IndustryResourceOffer, Project,
    University, PilotProject,
)
from services.audit_service import log_action
from services.notification_service import notify
from utils.decorators import role_required, get_current_user

industry_bp = Blueprint("industry", __name__, template_folder="../templates/industry")

INDUSTRY_ROLES = ("INDUSTRY",)
ORGANIZATION_TYPES = ("Industry", "Startup", "MSME", "CSR Organization", "Research Institution",
                      "Innovation Hub", "Technology Provider", "Other")
SECTORS = ("IT & Software", "Artificial Intelligence", "Electronics", "Manufacturing", "Automotive",
           "Aerospace", "Energy", "Renewable Energy", "Agriculture Technology", "Healthcare",
           "Construction", "Infrastructure", "Water Management", "Waste Management",
           "Environmental Technology", "Transportation", "FinTech", "Education Technology",
           "Robotics", "IoT", "Telecommunications", "Biotechnology", "Other")
SUPPORT_TYPES = ("Technical Mentorship", "Funding", "CSR Support", "Hardware", "Software",
                 "Prototype Development", "Testing", "Data/Technology", "Pilot Implementation",
                 "Internship", "Employment", "Technology Transfer")


def _industry():
    user = get_current_user()
    return IndustryProfile.query.filter_by(organization_id=user.organization_id).first() if user else None


def _tags(value):
    return {tag.strip().lower() for tag in (value or "").replace(";", ",").split(",") if tag.strip()}


def _recommendation(challenge, profile):
    profile_tags = _tags(",".join([profile.sector or "", profile.sub_sector or "", profile.expertise or "",
                                   profile.technologies or "", profile.services or "", profile.csr_focus_areas or ""]))
    challenge_tags = _tags(",".join([challenge.category.name if challenge.category else "",
                                      challenge.subcategory or "", challenge.required_skills or "",
                                      challenge.location.state if challenge.location else ""]))
    matches = profile_tags & challenge_tags
    score = min(95, 35 + len(matches) * 12)
    if challenge.location and profile.organization.state and challenge.location.state == profile.organization.state:
        score = min(100, score + 5)
    reasons = [f"matches {', '.join(sorted(matches))}"] if matches else ["fits the platform's verified societal challenge domains"]
    if challenge.location and profile.organization.state and challenge.location.state == profile.organization.state:
        reasons.append("is in your organization's state")
    return score, "Recommended because the organization " + " and ".join(reasons) + "."


@industry_bp.route("/register", methods=["GET", "POST"])
def register():
    from services import auth_service, otp_service
    from routes.auth_routes import _start_signup_verification
    from utils.validators import validate_passwords_match, validate_phone_required, ValidationError
    from database.models import Organization

    if request.method == "POST":
        f = request.form
        try:
            validate_passwords_match(f.get("password", ""), f.get("confirm_password", ""))
            phone = validate_phone_required(f.get("phone", ""))
            if f.get("organization_type") not in ORGANIZATION_TYPES or f.get("sector") not in SECTORS:
                raise ValidationError("Select a valid organization type and industry sector.", code="INVALID_PROFILE")
            organization = Organization(
                name=f["organization_name"], org_type="INDUSTRY", official_email=f["official_email"],
                phone=phone, website=f.get("website"), address=f.get("location"),
                district=f.get("district"), state=f.get("state"), status="PENDING",
            )
            db.session.add(organization)
            db.session.flush()
            profile = IndustryProfile(
                organization_id=organization.id, organization_type=f["organization_type"],
                sector=f["sector"], sub_sector=f.get("sub_sector"), organization_size=f.get("organization_size"),
                description=f.get("description"), expertise=f.get("expertise"),
                technologies=f.get("technologies"), services=f.get("services"),
                csr_focus_areas=f.get("csr_focus_areas"), available_resources=f.get("available_resources"),
                contact_person=f["contact_person"],
            )
            db.session.add(profile)
            db.session.commit()
            user = auth_service.create_user(f["contact_person"], f["official_email"], f["password"],
                                            "INDUSTRY", organization_id=organization.id, phone=phone)
            return _start_signup_verification(user)
        except (ValidationError, KeyError) as exc:
            db.session.rollback()
            flash(getattr(exc, "message", "Please complete all required fields."), "danger")
        except Exception:
            db.session.rollback()
            flash("Registration failed. Please check the form and try again.", "danger")
    return render_template("industry/register.html", organization_types=ORGANIZATION_TYPES, sectors=SECTORS)


@industry_bp.route("/login")
def login():
    return redirect(url_for("auth.login", next=url_for("industry.dashboard")))


@industry_bp.route("/")
@industry_bp.route("/dashboard")
@role_required(*INDUSTRY_ROLES)
def dashboard():
    profile = _industry()
    requests = IndustryCollaborationRequest.query.filter_by(industry_id=profile.id).order_by(
        IndustryCollaborationRequest.created_at.desc()).all() if profile else []
    collaborations = IndustryCollaboration.query.filter_by(industry_id=profile.id).order_by(
        IndustryCollaboration.created_at.desc()).all() if profile else []
    recommendations = _recommended_challenges(profile, 6) if profile else []
    stats = {
        "relevant_challenges": len(recommendations),
        "active_collaborations": len([c for c in collaborations if c.status == "ACTIVE"]),
        "pending_requests": len([r for r in requests if r.status in ("REQUESTED", "UNDER_REVIEW")]),
        "active_mentorships": len([c for c in collaborations if c.status == "ACTIVE" and "mentorship" in c.role.lower()]),
        "funded_projects": IndustryFunding.query.filter_by(industry_id=profile.id, status="RELEASED").count() if profile else 0,
        "pilot_projects": PilotProject.query.filter_by(industry_id=profile.id).count() if profile else 0,
        "completed_collaborations": len([c for c in collaborations if c.status == "COMPLETED"]),
    }
    return render_template("industry/dashboard.html", profile=profile, stats=stats,
                           recommendations=recommendations, requests=requests[:8], collaborations=collaborations)


def _recommended_challenges(profile, limit=None):
    challenges = Challenge.query.filter(Challenge.status.in_(["VERIFIED", "ASSIGNED", "IN_PROGRESS"])).all()
    values = []
    for challenge in challenges:
        score, reason = _recommendation(challenge, profile)
        values.append({"challenge": challenge, "score": score, "reason": reason})
    values.sort(key=lambda item: (item["score"], item["challenge"].priority_score), reverse=True)
    return values[:limit] if limit else values


@industry_bp.route("/challenges")
@role_required(*INDUSTRY_ROLES)
def recommendations():
    profile = _industry()
    return render_template("industry/challenges.html", profile=profile,
                           recommendations=_recommended_challenges(profile) if profile else [])


@industry_bp.route("/projects")
@role_required(*INDUSTRY_ROLES)
def projects():
    profile = _industry()
    project_list = Project.query.join(IndustryCollaboration).filter(
        IndustryCollaboration.industry_id == profile.id).all() if profile else []
    return render_template("industry/projects.html", projects=project_list)


@industry_bp.route("/challenges/<int:challenge_id>/collaborate", methods=["GET", "POST"])
@role_required(*INDUSTRY_ROLES)
def collaborate(challenge_id):
    profile = _industry()
    challenge = Challenge.query.get_or_404(challenge_id)
    project_id = request.args.get("project_id", type=int) or request.form.get("project_id", type=int)
    project = db.session.get(Project, project_id) if project_id else None
    if request.method == "POST":
        support_types = request.form.getlist("support_types")
        if not support_types or not request.form.get("description", "").strip():
            flash("Select at least one support type and describe your proposal.", "warning")
            return render_template("industry/collaborate.html", challenge=challenge, project=project,
                                   support_types=SUPPORT_TYPES)
        if IndustryCollaborationRequest.query.filter_by(industry_id=profile.id, challenge_id=challenge.id,
                                                        project_id=project_id).filter(
                                                            IndustryCollaborationRequest.status.in_(["REQUESTED", "UNDER_REVIEW", "APPROVED", "ACTIVE"])
                                                        ).first():
            flash("A collaboration proposal already exists for this problem.", "info")
            return redirect(url_for("industry.dashboard"))
        proposal = IndustryCollaborationRequest(
            industry_id=profile.id, challenge_id=challenge.id, project_id=project_id,
            university_id=project.university_id if project else challenge.assigned_university_id,
            proposal_type=request.form.get("proposal_type", "Industry collaboration"),
            support_types=", ".join(support_types), description=request.form["description"],
            estimated_contribution=request.form.get("estimated_contribution"),
            expected_duration=request.form.get("expected_duration"), experts=request.form.get("experts"),
            budget=request.form.get("budget") or None,
        )
        db.session.add(proposal)
        db.session.commit()
        if proposal.university:
            for user in proposal.university.organization.users:
                notify(user, "Industry collaboration request", f"{profile.organization.name} proposed support for {challenge.title}.",
                       link=f"/dashboard/university/collaboration-requests/{proposal.id}")
        log_action(get_current_user(), "COLLABORATION_REQUEST", "IndustryCollaborationRequest", proposal.id,
                   None, "REQUESTED")
        flash("Collaboration proposal submitted for university review.", "success")
        return redirect(url_for("industry.dashboard"))
    return render_template("industry/collaborate.html", challenge=challenge, project=project,
                           support_types=SUPPORT_TYPES)


@industry_bp.route("/profile", methods=["GET", "POST"])
@role_required(*INDUSTRY_ROLES)
def profile():
    industry = _industry()
    if request.method == "POST":
        f = request.form
        industry.sub_sector = f.get("sub_sector")
        industry.expertise = f.get("expertise")
        industry.technologies = f.get("technologies")
        industry.services = f.get("services")
        industry.csr_focus_areas = f.get("csr_focus_areas")
        industry.available_resources = f.get("available_resources")
        industry.description = f.get("description")
        db.session.commit()
        flash("Organization capability profile updated.", "success")
        return redirect(url_for("industry.profile"))
    return render_template("industry/profile.html", industry=industry)


@industry_bp.route("/mentors", methods=["GET", "POST"])
@role_required(*INDUSTRY_ROLES)
def mentors():
    industry = _industry()
    if request.method == "POST":
        mentor = IndustryMentor(industry_id=industry.id, name=request.form["name"],
                                designation=request.form.get("designation"), expertise=request.form.get("expertise"),
                                experience=request.form.get("experience"), skills=request.form.get("skills"),
                                contact=request.form.get("contact"))
        db.session.add(mentor)
        db.session.commit()
        log_action(get_current_user(), "INDUSTRY_MENTOR_ADDED", "IndustryMentor", mentor.id, None, "ACTIVE")
        flash("Industry mentor added.", "success")
        return redirect(url_for("industry.mentors"))
    return render_template("industry/mentors.html", industry=industry)


@industry_bp.route("/funding", methods=["GET", "POST"])
@role_required(*INDUSTRY_ROLES)
def funding():
    industry = _industry()
    projects = Project.query.join(IndustryCollaboration).filter(IndustryCollaboration.industry_id == industry.id).all()
    if request.method == "POST":
        proposal = IndustryFunding(industry_id=industry.id, project_id=int(request.form["project_id"]),
                                   amount=request.form.get("amount") or None, purpose=request.form["purpose"],
                                   expected_outcome=request.form.get("expected_outcome"),
                                   duration=request.form.get("duration"), terms=request.form.get("terms"))
        db.session.add(proposal)
        db.session.commit()
        flash("Funding proposal submitted for review.", "success")
        return redirect(url_for("industry.funding"))
    proposals = IndustryFunding.query.filter_by(industry_id=industry.id).order_by(IndustryFunding.created_at.desc()).all()
    return render_template("industry/funding.html", projects=projects, proposals=proposals)
