"""
YugKrit - AI Service.

If AI_API_KEY is configured in the environment, this module could be
extended to call an external LLM. For the first working version we use a
transparent, rule-based "mock AI" engine so the platform works out of the
box with no external dependency. Every recommendation is clearly labeled
and government/university users can always override it.
"""

import json
import os
from database.models import Challenge, University

KEYWORD_CATEGORY_MAP = {
    "water": "Water & Sanitation",
    "sewage": "Water & Sanitation",
    "park": "Urban Infrastructure",
    "road": "Urban Infrastructure",
    "traffic": "Urban Infrastructure",
    "waste": "Environment & Waste Management",
    "garbage": "Environment & Waste Management",
    "pollution": "Environment & Waste Management",
    "health": "Public Health",
    "hospital": "Public Health",
    "school": "Education",
    "education": "Education",
    "power": "Energy",
    "electric": "Energy",
    "safety": "Public Safety",
    "crime": "Public Safety",
}

KEYWORD_SKILL_MAP = {
    "water": ["Civil Engineering", "Environmental Science", "IoT"],
    "park": ["Civil Engineering", "IoT", "GIS"],
    "waste": ["Environmental Science", "Mechanical Engineering", "Data Analysis"],
    "traffic": ["IoT", "Data Analysis", "GIS"],
    "health": ["Public Health", "Data Analysis", "Mobile App Development"],
    "school": ["EdTech", "UI/UX Design", "Web Development"],
    "power": ["Electrical Engineering", "IoT", "Renewable Energy"],
    "safety": ["IoT", "Mobile App Development", "Data Analysis"],
}

AI_ENABLED_EXTERNALLY = bool(os.environ.get("AI_API_KEY"))


def categorize_challenge(title, description):
    text = f"{title} {description}".lower()
    for keyword, category in KEYWORD_CATEGORY_MAP.items():
        if keyword in text:
            return category
    return "General Societal Challenge"


def calculate_priority(affected_population, urgency):
    urgency_weight = {"LOW": 20, "MEDIUM": 45, "HIGH": 70, "CRITICAL": 90}.get(urgency, 45)
    population_weight = min(affected_population / 100, 30) if affected_population else 0
    score = int(min(urgency_weight + population_weight, 100))
    return max(score, 1)


def recommend_skills(title, description):
    text = f"{title} {description}".lower()
    skills = set()
    for keyword, skill_list in KEYWORD_SKILL_MAP.items():
        if keyword in text:
            skills.update(skill_list)
    if not skills:
        skills = {"Research", "Data Analysis", "Project Management"}
    return sorted(skills)


def find_similar_challenges(title, description, exclude_id=None, limit=5):
    text_words = set(f"{title} {description}".lower().split())
    candidates = Challenge.query.filter(Challenge.id != exclude_id).all() if exclude_id else Challenge.query.all()
    scored = []
    for c in candidates:
        c_words = set(f"{c.title} {c.description or ''}".lower().split())
        overlap = len(text_words.intersection(c_words))
        if overlap > 1:
            scored.append((overlap, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]]


def recommend_universities(required_skills, district=None, limit=3):
    """Rule-based scoring: departments matching required skills score higher."""
    universities = University.query.join(University.organization).filter_by(status="VERIFIED").all()
    scored = []
    for uni in universities:
        dept_names = " ".join([d.name.lower() for d in uni.departments]) if uni.departments else ""
        score = 60  # base score
        for skill in required_skills:
            if skill.lower().split()[0] in dept_names:
                score += 10
        if district and uni.organization and uni.organization.district == district:
            score += 15
        score = min(score, 99)
        scored.append({"university_id": uni.id, "name": uni.organization.name, "score": score})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def analyze_challenge(challenge):
    """Run the full mock-AI pipeline on a Challenge object and return a dict
    ready to be stored in AIAnalysis."""
    category = categorize_challenge(challenge.title, challenge.description or "")
    priority = calculate_priority(challenge.affected_population or 0, challenge.urgency)
    skills = recommend_skills(challenge.title, challenge.description or "")
    district = challenge.location.district if challenge.location else None
    universities = recommend_universities(skills, district)
    similar = find_similar_challenges(challenge.title, challenge.description or "", exclude_id=challenge.id)

    return {
        "suggested_category": category,
        "priority_score": priority,
        "suggested_skills": ", ".join(skills),
        "university_matches": json.dumps(universities),
        "similar_challenge_ids": ",".join(str(c.id) for c in similar),
        "human_review_required": True,
        "source": "rule-based-mock-engine" if not AI_ENABLED_EXTERNALLY else "external-ai",
    }
