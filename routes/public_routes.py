"""YugKrit - Public (unauthenticated) website routes."""

from flask import Blueprint, render_template, request
from database.models import Challenge, ChallengeLocation, University, ULB, NGO, StudentProfile, Project, ChallengeCategory

public_bp = Blueprint("public", __name__, template_folder="../templates/public")


@public_bp.route("/")
def home():
    stats = {
        "challenges": Challenge.query.count(),
        "universities": University.query.count(),
        "students": StudentProfile.query.count(),
        "projects": Project.query.count(),
        "communities": ULB.query.count() + NGO.query.count(),
    }
    featured = Challenge.query.filter_by(status="VERIFIED").order_by(Challenge.priority_score.desc()).limit(3).all()
    return render_template("public/home.html", stats=stats, featured=featured)


@public_bp.route("/about")
def about():
    return render_template("public/about.html")


@public_bp.route("/how-it-works")
def how_it_works():
    return render_template("public/how_it_works.html")


@public_bp.route("/explore")
def explore_challenges():
    query = Challenge.query.filter(Challenge.status.in_(["VERIFIED", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]))
    category = request.args.get("category")
    district = request.args.get("district")
    state = request.args.get("state")
    if category:
        query = query.join(ChallengeCategory).filter(ChallengeCategory.name == category)
    if district:
        query = query.filter(Challenge.location.has(district=district))
    if state:
        query = query.filter(Challenge.location.has(state=state))
    challenges = query.order_by(Challenge.priority_score.desc()).all()
    categories = ChallengeCategory.query.all()
    states = [row[0] for row in Challenge.query.join(ChallengeLocation).with_entities(ChallengeLocation.state).distinct().order_by(ChallengeLocation.state).all() if row[0]]
    return render_template("public/explore.html", challenges=challenges, categories=categories, states=states)


@public_bp.route("/impact")
def impact():
    completed = Project.query.filter(Project.status.in_(["COMPLETED", "VERIFIED"])).all()
    total_people = sum((p.impact.people_impacted or 0) for p in completed if p.impact)
    return render_template("public/impact.html", completed=completed, total_people=total_people)


@public_bp.route("/for-universities")
def for_universities():
    return render_template("public/for_universities.html")


@public_bp.route("/for-organizations")
def for_organizations():
    return render_template("public/for_organizations.html")
