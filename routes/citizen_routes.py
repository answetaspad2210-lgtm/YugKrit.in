"""YugKrit - Citizen dashboard routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.database import db
from database.models import Challenge, ChallengeCategory, ChallengeEvidence
from utils.decorators import role_required, get_current_user
from utils.helpers import save_uploaded_file
from services import challenge_service

citizen_bp = Blueprint("citizen", __name__, template_folder="../templates/citizen")


def _current_profile():
    user = get_current_user()
    return user.citizen_profile if user else None


@citizen_bp.route("/")
@role_required("CITIZEN")
def overview():
    profile = _current_profile()
    my_challenges = Challenge.query.filter_by(submitted_by_citizen_id=profile.id).order_by(
        Challenge.created_at.desc()).all() if profile else []
    stats = {
        "posted": len(my_challenges),
        "verified": len([c for c in my_challenges if c.status not in ("SUBMITTED", "REJECTED")]),
        "in_progress": len([c for c in my_challenges if c.status in ("ASSIGNED", "IN_PROGRESS")]),
        "resolved": len([c for c in my_challenges if c.status == "RESOLVED"]),
    }
    return render_template("citizen/overview.html", profile=profile, my_challenges=my_challenges[:5], stats=stats)


@citizen_bp.route("/post-problem", methods=["GET", "POST"])
@role_required("CITIZEN")
def post_problem():
    profile = _current_profile()
    if not profile or (profile.verification_status != "VERIFIED" and profile.aadhaar_hash):
        flash("Your citizen profile must be verified before you can post a problem. Please contact support.", "warning")
        return redirect(url_for("citizen.overview"))

    if request.method == "POST":
        f = request.form
        state = f.get("state", "").strip()
        data = {
            "title": f["title"], "description": f.get("description"),
            "category": f.get("category"), "subcategory": f.get("subcategory"),
            "affected_population": f.get("affected_population"), "urgency": f.get("urgency", "MEDIUM"),
            "current_situation": f.get("current_situation"), "supporting_info": f.get("supporting_info"),
            "address": f.get("address"), "district": f.get("district"), "state": state,
            "latitude": f.get("latitude"), "longitude": f.get("longitude"),
        }
        challenge = challenge_service.create_challenge(profile, data, submitter_type="CITIZEN")

        for file in request.files.getlist("evidence"):
            if file and file.filename:
                name, path, size = save_uploaded_file(file, subfolder="challenges")
                ext = name.rsplit(".", 1)[1].lower() if name else ""
                evidence_type = "PHOTO" if ext in ("jpg", "jpeg", "png") else (
                    "VIDEO" if ext == "mp4" else "DOCUMENT")
                db.session.add(ChallengeEvidence(challenge_id=challenge.id, evidence_type=evidence_type,
                                                  file_name=name, file_path=path))
        db.session.commit()

        flash("Problem submitted successfully. It will be reviewed by the Government IT Cell.", "success")
        return redirect(url_for("citizen.my_problems"))
    return render_template("citizen/post_problem.html", categories=ChallengeCategory.query.order_by(
        ChallengeCategory.name).all())


@citizen_bp.route("/my-problems")
@role_required("CITIZEN")
def my_problems():
    profile = _current_profile()
    challenges = Challenge.query.filter_by(submitted_by_citizen_id=profile.id).order_by(
        Challenge.created_at.desc()).all() if profile else []
    return render_template("citizen/my_problems.html", challenges=challenges)


@citizen_bp.route("/problems")
@role_required("CITIZEN")
def problems():
    q = Challenge.query.filter(Challenge.status.in_(["VERIFIED", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]))
    category = request.args.get("category")
    if category:
        q = q.join(ChallengeCategory).filter(ChallengeCategory.name == category)
    challenges = q.order_by(Challenge.priority_score.desc()).all()
    categories = ChallengeCategory.query.all()
    return render_template("citizen/problems.html", challenges=challenges, categories=categories)


@citizen_bp.route("/problems/<int:challenge_id>")
@role_required("CITIZEN")
def problem_detail(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    return render_template("citizen/problem_detail.html", challenge=challenge)
