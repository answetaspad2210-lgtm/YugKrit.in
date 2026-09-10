"""YugKrit - ULB / NGO dashboard routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.models import Challenge, CommunityValidation, Project
from database.database import db
from utils.decorators import role_required, get_current_user
from services import challenge_service
from utils.helpers import save_uploaded_file
from database.models import ChallengeEvidence

ulb_bp = Blueprint("ulb", __name__, template_folder="../templates/ulb")

ULB_ROLES = ("ULB_ADMIN", "NGO_ADMIN")


@ulb_bp.route("/")
@role_required(*ULB_ROLES)
def overview():
    user = get_current_user()
    org_id = user.organization_id
    my_challenges = Challenge.query.filter_by(submitted_by_org_id=org_id).all()
    stats = {
        "submitted": len(my_challenges),
        "verified": len([c for c in my_challenges if c.status not in ("SUBMITTED", "REJECTED")]),
        "active_projects": Project.query.join(Challenge).filter(
            Challenge.submitted_by_org_id == org_id, Project.status.in_(["PLANNING", "IN_PROGRESS"])).count(),
        "solutions_validated": Project.query.join(Challenge).filter(
            Challenge.submitted_by_org_id == org_id, Project.status.in_(["COMPLETED", "VERIFIED"])).count(),
        "communities_impacted": sum((p.impact.people_impacted or 0)
                                     for p in Project.query.join(Challenge).filter(
                                         Challenge.submitted_by_org_id == org_id).all() if p.impact),
    }
    return render_template("ulb/overview.html", my_challenges=my_challenges[:5], stats=stats)


@ulb_bp.route("/submit-challenge", methods=["GET", "POST"])
@role_required(*ULB_ROLES)
def submit_challenge():
    user = get_current_user()
    if request.method == "POST":
        f = request.form
        data = {
            "title": f["title"], "description": f.get("description"),
            "category": f.get("category"), "subcategory": f.get("subcategory"),
            "affected_population": f.get("affected_population"), "urgency": f.get("urgency", "MEDIUM"),
            "current_situation": f.get("current_situation"), "supporting_info": f.get("supporting_info"),
            "address": f.get("address"), "district": f.get("district"), "state": f.get("state"),
            "latitude": f.get("latitude"), "longitude": f.get("longitude"),
        }
        challenge = challenge_service.create_challenge(user.organization, data)

        for file in request.files.getlist("evidence"):
            if file and file.filename:
                name, path, size = save_uploaded_file(file, subfolder="challenges")
                ext = name.rsplit(".", 1)[1].lower() if name else ""
                evidence_type = "PHOTO" if ext in ("jpg", "jpeg", "png") else (
                    "VIDEO" if ext == "mp4" else "DOCUMENT")
                db.session.add(ChallengeEvidence(challenge_id=challenge.id, evidence_type=evidence_type,
                                                  file_name=name, file_path=path))
        db.session.commit()

        flash("Challenge submitted successfully. Government will review it shortly.", "success")
        return redirect(url_for("ulb.my_challenges"))
    return render_template("ulb/submit_challenge.html")


@ulb_bp.route("/my-challenges")
@role_required(*ULB_ROLES)
def my_challenges():
    user = get_current_user()
    challenges = Challenge.query.filter_by(submitted_by_org_id=user.organization_id).order_by(
        Challenge.created_at.desc()).all()
    return render_template("ulb/my_challenges.html", challenges=challenges)


@ulb_bp.route("/challenges/<int:challenge_id>")
@role_required(*ULB_ROLES)
def challenge_detail(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    if challenge.submitted_by_org_id != get_current_user().organization_id:
        flash("You do not have access to this challenge.", "danger")
        return redirect(url_for("ulb.my_challenges"))
    return render_template("ulb/challenge_detail.html", challenge=challenge)


@ulb_bp.route("/projects")
@role_required(*ULB_ROLES)
def projects():
    user = get_current_user()
    project_list = Project.query.join(Challenge).filter(
        Challenge.submitted_by_org_id == user.organization_id).all()
    return render_template("ulb/projects.html", projects=project_list)


@ulb_bp.route("/projects/<int:project_id>/validate", methods=["POST"])
@role_required(*ULB_ROLES)
def validate_project(project_id):
    user = get_current_user()
    project = Project.query.get_or_404(project_id)
    if project.challenge.submitted_by_org_id != user.organization_id:
        flash("You do not have access to this project.", "danger")
        return redirect(url_for("ulb.projects"))
    validation = CommunityValidation(project_id=project.id, validated_by_org_id=user.organization_id,
                                      feedback=request.form.get("feedback"),
                                      rating=int(request.form.get("rating", 5)))
    db.session.add(validation)
    db.session.commit()
    flash("Community validation submitted.", "success")
    return redirect(url_for("ulb.projects"))
