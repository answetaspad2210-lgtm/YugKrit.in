"""YugKrit - Challenge lifecycle service."""

from database.database import db
from database.models import (
    Challenge, ChallengeLocation, ChallengeCategory, ChallengeAssignment,
    AIAnalysis, University, Organization
)
from utils.helpers import generate_code
from services import ai_service
from services.audit_service import log_action
from services.notification_service import notify


def create_challenge(submitter, data, submitter_type="ORG"):
    """`submitter` is an Organization when submitter_type='ORG' (ULB/NGO), or
    a CitizenProfile when submitter_type='CITIZEN'."""
    category = ChallengeCategory.query.filter_by(name=data.get("category")).first()
    if not category:
        category = ChallengeCategory(name=data.get("category") or "General")
        db.session.add(category)
        db.session.flush()

    challenge = Challenge(
        challenge_code=generate_code("YK"),
        title=data["title"],
        description=data.get("description"),
        category_id=category.id,
        subcategory=data.get("subcategory"),
        submitted_by_org_id=submitter.id if submitter_type == "ORG" else None,
        submitted_by_citizen_id=submitter.id if submitter_type == "CITIZEN" else None,
        affected_population=int(data.get("affected_population") or 0),
        urgency=data.get("urgency", "MEDIUM"),
        current_situation=data.get("current_situation"),
        supporting_info=data.get("supporting_info"),
        status="SUBMITTED",
    )
    db.session.add(challenge)
    db.session.flush()

    location = ChallengeLocation(
        challenge_id=challenge.id,
        address=data.get("address"),
        district=data.get("district"),
        state=data.get("state"),
        latitude=float(data["latitude"]) if data.get("latitude") else None,
        longitude=float(data["longitude"]) if data.get("longitude") else None,
    )
    db.session.add(location)
    db.session.commit()

    run_ai_analysis(challenge)
    return challenge


def run_ai_analysis(challenge):
    result = ai_service.analyze_challenge(challenge)
    analysis = AIAnalysis(
        challenge_id=challenge.id,
        suggested_category=result["suggested_category"],
        priority_score=result["priority_score"],
        suggested_skills=result["suggested_skills"],
        university_matches=result["university_matches"],
        similar_challenge_ids=result["similar_challenge_ids"],
        human_review_required=result["human_review_required"],
    )
    challenge.priority_score = result["priority_score"]
    challenge.required_skills = result["suggested_skills"]
    db.session.add(analysis)
    db.session.commit()
    return analysis


def verify_challenge(challenge, gov_user, approve=True, reason=None):
    previous = challenge.status
    challenge.status = "VERIFIED" if approve else "REJECTED"
    db.session.commit()
    log_action(gov_user, "CHALLENGE_VERIFY" if approve else "CHALLENGE_REJECT",
               "Challenge", challenge.id, previous, challenge.status, reason)
    if challenge.submitted_by_org:
        for user in challenge.submitted_by_org.users:
            notify(user, "Challenge review completed",
                   f'Your challenge "{challenge.title}" was {"verified" if approve else "rejected"}.',
                   link=f"/dashboard/ulb/challenges/{challenge.id}")
    if challenge.submitted_by_citizen and challenge.submitted_by_citizen.user:
        notify(challenge.submitted_by_citizen.user, "Problem review completed",
               f'Your problem "{challenge.title}" was {"verified" if approve else "rejected"}.',
               link=f"/dashboard/citizen/problems/{challenge.id}")
    return challenge


def assign_challenge(challenge, gov_user, university_id=None, problem_owner_org_id=None):
    if problem_owner_org_id:
        challenge.problem_owner_org_id = problem_owner_org_id
        db.session.add(ChallengeAssignment(challenge_id=challenge.id, assigned_to_type="PROBLEM_OWNER",
                                            assigned_to_org_id=problem_owner_org_id, assigned_by_id=gov_user.id))
    if university_id:
        challenge.assigned_university_id = university_id
        challenge.status = "ASSIGNED"
        db.session.add(ChallengeAssignment(challenge_id=challenge.id, assigned_to_type="UNIVERSITY",
                                            assigned_to_org_id=None, assigned_by_id=gov_user.id))
        uni = db.session.get(University, university_id)
        if uni:
            for u in uni.organization.users:
                notify(u, "Government-verified problem assigned",
                       f'"{challenge.title}" has been assigned to your university for student solution development.',
                       link=f"/dashboard/university/challenges/{challenge.id}")
    db.session.commit()
    log_action(gov_user, "CHALLENGE_ASSIGN", "Challenge", challenge.id, None,
               f"university_id={university_id}, problem_owner_org_id={problem_owner_org_id}")
    if challenge.submitted_by_org:
        for user in challenge.submitted_by_org.users:
            notify(user, "Challenge assigned", f'"{challenge.title}" has been assigned for solution development.',
                   link=f"/dashboard/ulb/challenges/{challenge.id}")
    return challenge
