"""YugKrit - Student dashboard routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.models import Challenge, Project, ChallengeCategory, StudentSkill, Milestone
from database.database import db
from utils.decorators import role_required, get_current_user
from services import student_service, project_service

student_bp = Blueprint("student", __name__, template_folder="../templates/student")


def _current_profile():
    user = get_current_user()
    return user.student_profile if user else None


@student_bp.route("/")
@role_required("STUDENT")
def overview():
    profile = _current_profile()
    growth = student_service.get_growth_profile(profile) if profile else None
    return render_template("student/overview.html", profile=profile, growth=growth)


@student_bp.route("/problems")
@role_required("STUDENT")
def problems():
    q = Challenge.query.filter_by(status="VERIFIED")
    category = request.args.get("category")
    if category:
        q = q.join(ChallengeCategory).filter(ChallengeCategory.name == category)
    challenges = q.order_by(Challenge.priority_score.desc()).all()
    categories = ChallengeCategory.query.all()
    return render_template("student/problems.html", challenges=challenges, categories=categories)


@student_bp.route("/problems/<int:challenge_id>")
@role_required("STUDENT")
def problem_detail(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    return render_template("student/problem_detail.html", challenge=challenge)


@student_bp.route("/projects")
@role_required("STUDENT")
def projects():
    profile = _current_profile()
    project_ids = {m.team.project_id for m in profile.team_memberships} if profile else set()
    project_list = Project.query.filter(Project.id.in_(project_ids)).all() if project_ids else []
    return render_template("student/projects.html", projects=project_list)


@student_bp.route("/projects/<int:project_id>")
@role_required("STUDENT")
def project_workspace(project_id):
    project = Project.query.get_or_404(project_id)
    profile = _current_profile()
    if not profile or not any(member.team.project_id == project.id for member in profile.team_memberships):
        flash("You do not have access to this project.", "danger")
        return redirect(url_for("student.projects"))
    tab = request.args.get("tab", "overview")
    return render_template("student/project_workspace.html", project=project, tab=tab)


@student_bp.route("/achievements")
@role_required("STUDENT")
def achievements():
    profile = _current_profile()
    growth = student_service.get_growth_profile(profile) if profile else None
    return render_template("student/achievements.html", profile=profile, growth=growth)


@student_bp.route("/certificates")
@role_required("STUDENT")
def certificates():
    profile = _current_profile()
    return render_template("student/certificates.html", profile=profile)


@student_bp.route("/skills", methods=["POST"])
@role_required("STUDENT")
def add_skill():
    profile = _current_profile()
    skill_name = request.form.get("skill_name", "").strip()
    if skill_name and profile:
        db.session.add(StudentSkill(student_id=profile.id, skill_name=skill_name))
        db.session.commit()
        flash(f'Added "{skill_name}" to your skills.', "success")
    return redirect(url_for("student.overview"))


@student_bp.route("/profile")
@role_required("STUDENT")
def profile_view():
    profile = _current_profile()
    growth = student_service.get_growth_profile(profile) if profile else None
    return render_template("student/profile.html", profile=profile, growth=growth)


@student_bp.route("/milestones/<int:milestone_id>/submit", methods=["POST"])
@role_required("STUDENT")
def submit_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    profile = _current_profile()
    if not profile or not any(member.team.project_id == milestone.project_id for member in profile.team_memberships):
        flash("You do not have access to this milestone.", "danger")
        return redirect(url_for("student.projects"))
    project_service.update_milestone_status(milestone, "SUBMITTED", actor=get_current_user())
    flash("Milestone submitted for faculty review.", "success")
    return redirect(url_for("student.project_workspace", project_id=milestone.project_id, tab="milestones"))
