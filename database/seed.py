"""
YugKrit - Database seed script.

Run with:  python database/seed.py

Creates:
  - All roles + permissions (utils/permissions.py is the single source of truth)
  - 4 DEVELOPMENT DEMO ACCOUNTS (government, university, ulb, student)
  - The full "Urban Park Renovation" demo workflow described in the spec,
    ending with a COMPLETED project, achievements, and a certificate.
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.database import db
from database.database import CHALLENGE_CATEGORIES
from database.models import (
    Role, Permission, User, Organization, University, ULB,
    UniversityDepartment, Faculty, ChallengeCategory, CitizenProfile
)
from utils.permissions import ALL_PERMISSIONS, ROLE_PERMISSIONS
from services import auth_service, challenge_service, project_service, citizen_service

DEMO_PASSWORDS = {
    "itcell@yugkrit.local": "YugKritIT@2026",
    "gov@yugkrit.local": "YugKritGov@2026",
    "university@yugkrit.local": "YugKritUni@2026",
    "faculty@yugkrit.local": "YugKritFac@2026",
    "ulb@yugkrit.local": "YugKritULB@2026",
    "ngo@yugkrit.local": "YugKritNGO@2026",
    "student@college.local": "YugKritStu@2026",
    "citizen@yugkrit.local": "YugKritCit@2026",
}


def seed_roles_and_permissions():
    print("Seeding roles & permissions...")
    perm_objs = {}
    for code, desc in ALL_PERMISSIONS:
        p = Permission.query.filter_by(code=code).first()
        if not p:
            p = Permission(code=code, description=desc)
            db.session.add(p)
        perm_objs[code] = p
    db.session.commit()

    for role_name, perm_codes in ROLE_PERMISSIONS.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=role_name.replace("_", " ").title())
            db.session.add(role)
            db.session.commit()
        role.permissions = [perm_objs[c] for c in perm_codes]
    db.session.commit()


def seed_categories():
    for n in CHALLENGE_CATEGORIES:
        if not ChallengeCategory.query.filter_by(name=n).first():
            db.session.add(ChallengeCategory(name=n))
    db.session.commit()


def seed_demo_accounts():
    print("Seeding demo accounts and organizations...")

    # --- Government IT Cell (platform head-of-office) ---
    itcell_org = Organization.query.filter_by(name="Government IT Cell - YugKrit Platform Office").first()
    if not itcell_org:
        itcell_org = Organization(name="Government IT Cell - YugKrit Platform Office", org_type="GOVERNMENT",
                                   official_email="itcell@yugkrit.local", status="VERIFIED",
                                   district="Lucknow", state="Uttar Pradesh")
        db.session.add(itcell_org)
        db.session.commit()

    if not User.query.filter_by(email="itcell@yugkrit.local").first():
        auth_service.create_user("Priyanka Nair (IT Cell Head)", "itcell@yugkrit.local", DEMO_PASSWORDS["itcell@yugkrit.local"],
                                  "GOVT_IT_CELL_ADMIN", organization_id=itcell_org.id, phone="9810000001")

    # --- Government ---
    gov_org = Organization.query.filter_by(name="Government of Uttar Pradesh - Urban Dept").first()
    if not gov_org:
        gov_org = Organization(name="Government of Uttar Pradesh - Urban Dept", org_type="GOVERNMENT",
                                official_email="gov@yugkrit.local", status="VERIFIED",
                                district="Lucknow", state="Uttar Pradesh")
        db.session.add(gov_org)
        db.session.commit()

    if not User.query.filter_by(email="gov@yugkrit.local").first():
        auth_service.create_user("Anita Sharma (Govt Admin)", "gov@yugkrit.local", DEMO_PASSWORDS["gov@yugkrit.local"],
                                  "GOVERNMENT_ADMIN", organization_id=gov_org.id, phone="9810000002")

    # --- University ---
    uni_org = Organization.query.filter_by(name="ABC University").first()
    if not uni_org:
        uni_org = Organization(name="ABC University", org_type="UNIVERSITY",
                                official_email="university@yugkrit.local", status="VERIFIED",
                                district="Lucknow", state="Uttar Pradesh")
        db.session.add(uni_org)
        db.session.commit()

    university = University.query.filter_by(organization_id=uni_org.id).first()
    if not university:
        university = University(organization_id=uni_org.id, institution_type="State University",
                                  aishe_code="U-1234", affiliating_university="Self Affiliated",
                                  rep_name="Dr. Rakesh Verma", rep_designation="Dean R&D")
        db.session.add(university)
        db.session.commit()
        for dept in ["Computer Science", "Civil Engineering", "Electronics"]:
            db.session.add(UniversityDepartment(university_id=university.id, name=dept))
        db.session.commit()

    if not User.query.filter_by(email="university@yugkrit.local").first():
        auth_service.create_user("Dr. Rakesh Verma (University Admin)", "university@yugkrit.local",
                                  DEMO_PASSWORDS["university@yugkrit.local"], "UNIVERSITY_ADMIN", organization_id=uni_org.id, phone="9810000003")

    faculty_user = User.query.filter_by(email="faculty@yugkrit.local").first()
    if not faculty_user:
        faculty_user = auth_service.create_user("Prof. Neha Gupta", "faculty@yugkrit.local",
                                                  DEMO_PASSWORDS["faculty@yugkrit.local"], "FACULTY", organization_id=uni_org.id,
                                                  phone="9810000004")
    faculty = Faculty.query.filter_by(user_id=faculty_user.id).first()
    if not faculty:
        faculty = Faculty(user_id=faculty_user.id, university_id=university.id,
                           department="Civil Engineering", designation="Associate Professor")
        db.session.add(faculty)
        db.session.commit()

    # --- ULB ---
    ulb_org = Organization.query.filter_by(name="Lucknow Municipal Corporation").first()
    if not ulb_org:
        ulb_org = Organization(name="Lucknow Municipal Corporation", org_type="ULB",
                                official_email="ulb@yugkrit.local", status="VERIFIED",
                                district="Lucknow", state="Uttar Pradesh")
        db.session.add(ulb_org)
        db.session.commit()

    ulb = ULB.query.filter_by(organization_id=ulb_org.id).first()
    if not ulb:
        ulb = ULB(organization_id=ulb_org.id, ulb_type="Municipal Corporation", category="ULB",
                   authorized_officer="Suresh Yadav", designation="Executive Engineer")
        db.session.add(ulb)
        db.session.commit()

    if not User.query.filter_by(email="ulb@yugkrit.local").first():
        auth_service.create_user("Suresh Yadav (ULB Admin)", "ulb@yugkrit.local", DEMO_PASSWORDS["ulb@yugkrit.local"],
                                  "ULB_ADMIN", organization_id=ulb_org.id, phone="9810000005")

    # --- NGO (merged into the ULB dashboard/model, category='NGO') ---
    ngo_org = Organization.query.filter_by(name="Swachh Lucknow Foundation").first()
    if not ngo_org:
        ngo_org = Organization(name="Swachh Lucknow Foundation", org_type="ULB",
                                official_email="ngo@yugkrit.local", status="VERIFIED",
                                district="Lucknow", state="Uttar Pradesh")
        db.session.add(ngo_org)
        db.session.commit()

    ngo = ULB.query.filter_by(organization_id=ngo_org.id).first()
    if not ngo:
        ngo = ULB(organization_id=ngo_org.id, category="NGO", registration_number="UP/2019/0004512",
                   authorized_officer="Meera Joshi", designation="Founder & Director")
        db.session.add(ngo)
        db.session.commit()

    if not User.query.filter_by(email="ngo@yugkrit.local").first():
        auth_service.create_user("Meera Joshi (NGO — Swachh Lucknow Foundation)", "ngo@yugkrit.local",
                                  DEMO_PASSWORDS["ngo@yugkrit.local"], "ULB_ADMIN", organization_id=ngo_org.id, phone="9810000006")

    # --- Student ---
    if not User.query.filter_by(email="student@college.local").first():
        auth_service.create_user("Rahul Kumar", "student@college.local", DEMO_PASSWORDS["student@college.local"], "STUDENT",
                                  phone="9810000007")

    # --- Citizen (phone-verified) ---
    citizen_user = User.query.filter_by(email="citizen@yugkrit.local").first()
    if not citizen_user:
        citizen_user = auth_service.create_user("Deepak Mishra", "citizen@yugkrit.local", DEMO_PASSWORDS["citizen@yugkrit.local"],
                                                   "CITIZEN", phone="9876500000")

    citizen_profile = CitizenProfile.query.filter_by(user_id=citizen_user.id).first()
    blank_profile = CitizenProfile.query.filter_by(aadhaar_hash="").first()
    if not citizen_profile and not blank_profile:
        citizen_service.register_citizen(
            citizen_user, address="14 Gomti Nagar", city="Lucknow", district="Lucknow", state="Uttar Pradesh",
        )
    citizen_user.is_phone_verified = True
    db.session.commit()

    # Keep credentials consistent when the seeder is rerun against an existing DB.
    for email, password in DEMO_PASSWORDS.items():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = auth_service.hash_password(password)
    db.session.commit()

    return gov_org, uni_org, university, ulb_org, faculty


def seed_demo_workflow(gov_org, uni_org, university, ulb_org, faculty):
    print("Seeding full demo workflow (challenge -> project -> completion)...")
    from database.models import Challenge
    existing = Challenge.query.filter_by(title="Urban Park Renovation and Smart Monitoring").first()
    if existing:
        print("Demo workflow already exists, skipping.")
        return

    gov_user = User.query.filter_by(email="gov@yugkrit.local").first()
    uni_admin = User.query.filter_by(email="university@yugkrit.local").first()
    student_user = User.query.filter_by(email="student@college.local").first()

    # 1. ULB submits the challenge
    challenge = challenge_service.create_challenge(ulb_org, {
        "title": "Urban Park Renovation and Smart Monitoring",
        "description": "Central city park requires renovation and IoT-based smart monitoring "
                        "for footfall, lighting, and waste bins to improve citizen usage and safety.",
        "category": "Urban Infrastructure",
        "subcategory": "Park Infrastructure",
        "affected_population": 2400,
        "urgency": "HIGH",
        "current_situation": "Park is under-utilized due to poor lighting, broken pathways and "
                              "irregular waste collection.",
        "supporting_info": "Citizen complaints received over the last 6 months.",
        "address": "Central City Park, Hazratganj",
        "district": "Lucknow",
        "state": "Uttar Pradesh",
        "latitude": 26.8467,
        "longitude": 80.9462,
    })

    # 2. Government verifies + assigns to university
    challenge_service.verify_challenge(challenge, gov_user, approve=True,
                                        reason="Evidence and AI analysis confirm valid, high-priority problem.")
    challenge_service.assign_challenge(challenge, gov_user, university_id=university.id,
                                        problem_owner_org_id=gov_org.id)

    # 3. University creates project
    project = project_service.create_project(challenge, university, faculty, {
        "name": "Smart Park Monitoring",
        "objective": "Deploy IoT sensors and revamp park infrastructure for safer, smarter public use.",
        "description": "A student-led solution combining civil renovation with IoT monitoring.",
        "expected_outcome": "20% increase in park usage, real-time monitoring dashboard for ULB.",
        "start_date": date(2026, 2, 1),
        "expected_completion": date(2026, 6, 30),
    })

    # 4. Team of 5 students, linked via institution_id + registration_number
    members = [
        {"full_name": "Rahul Kumar", "college_email": "rahul@abcuniversity.edu",
         "registration_number": "ABC2026CS102", "role_in_team": "Team Leader"},
        {"full_name": "Priya Singh", "college_email": "priya@abcuniversity.edu",
         "registration_number": "ABC2026CS103", "role_in_team": "IoT Developer"},
        {"full_name": "Aman Verma", "college_email": "aman@abcuniversity.edu",
         "registration_number": "ABC2026CE104", "role_in_team": "Civil Design"},
        {"full_name": "Sneha Rao", "college_email": "sneha@abcuniversity.edu",
         "registration_number": "ABC2026CS105", "role_in_team": "Data Analyst"},
        {"full_name": "Karan Mehta", "college_email": "karan@abcuniversity.edu",
         "registration_number": "ABC2026EC106", "role_in_team": "Field Coordinator"},
    ]
    team, _ = project_service.create_team(project, "Team Parkwatch", members)

    # Link the demo student login (student@college.local) to Rahul's profile
    rahul_profile = team.members[0].student
    rahul_profile.user_id = student_user.id
    rahul_profile.status = "ACTIVE"
    db.session.commit()

    # 5. Progress milestones: Research, Design, Prototype done; Testing in progress
    titles_done = ["Problem Research", "Solution Design", "Prototype"]
    for m in project.milestones:
        if m.title in titles_done:
            project_service.update_milestone_status(m, "COMPLETED", actor=uni_admin)
        elif m.title == "Testing":
            project_service.update_milestone_status(m, "IN_PROGRESS", actor=uni_admin)

    print("Demo workflow seeded (project in progress, Testing stage).")


def seed_citizen_demo_challenge():
    from database.models import Challenge
    existing = Challenge.query.filter_by(title="Open drain near Gomti Nagar bus stop").first()
    if existing:
        return
    citizen_profile = CitizenProfile.query.join(User, CitizenProfile.user_id == User.id).filter(
        User.email == "citizen@yugkrit.local").first()
    if not citizen_profile:
        return
    challenge_service.create_challenge(citizen_profile, {
        "title": "Open drain near Gomti Nagar bus stop",
        "description": "An uncovered drain near the bus stop is a safety hazard, especially at night.",
        "category": "Public Safety",
        "affected_population": 300,
        "urgency": "HIGH",
        "current_situation": "No cover or warning signage has been installed for over 3 months.",
        "address": "Gomti Nagar Bus Stop", "district": "Lucknow", "state": "Uttar Pradesh",
        "latitude": 26.8600, "longitude": 81.0100,
    }, submitter_type="CITIZEN")
    print("Citizen demo challenge seeded — pending IT Cell review at /dashboard/it-cell/citizen-challenges.")


def seed_state_demo_challenges():
    """Add bounded, clearly-labelled demo problems for the multi-state rollout."""
    from database.models import Challenge

    state_cases = [
        {
            "organization": "Ludhiana Civic Innovation Cell",
            "district": "Ludhiana", "state": "Punjab",
            "title": "Buddha Dariya sewage outfall monitoring",
            "description": "Create a low-cost monitoring and response workflow for sewage outfalls affecting the Buddha Dariya corridor.",
            "category": "Water & Sanitation", "subcategory": "Water quality and sewage",
            "address": "Buddha Dariya corridor, Ludhiana", "latitude": 30.9000, "longitude": 75.8573,
            "affected_population": 8500, "urgency": "HIGH",
            "current_situation": "Residents need transparent reporting of outfalls, sample collection, and resolution progress.",
        },
        {
            "organization": "Amritsar Heritage and Mobility Cell",
            "district": "Amritsar", "state": "Punjab",
            "title": "Safe last-mile access around heritage precincts",
            "description": "Design an accessible, shaded and pedestrian-safe last-mile route connecting local neighbourhoods to public transport and heritage areas.",
            "category": "Urban Infrastructure", "subcategory": "Accessible mobility",
            "address": "Heritage precinct mobility corridor, Amritsar", "latitude": 31.6340, "longitude": 74.8723,
            "affected_population": 4200, "urgency": "MEDIUM",
            "current_situation": "Pedestrian safety, shade, wayfinding and access needs are fragmented across the route.",
        },
        {
            "organization": "Dhanbad Mining-Area Resilience Cell",
            "district": "Dhanbad", "state": "Jharkhand",
            "title": "Mine-area water safety and hazard reporting",
            "description": "Build a community reporting and response system for unsafe water points, mine subsidence alerts and blocked access routes.",
            "category": "Public Safety", "subcategory": "Mining-area resilience",
            "address": "Mining belt community corridor, Dhanbad", "latitude": 23.7957, "longitude": 86.4304,
            "affected_population": 6200, "urgency": "CRITICAL",
            "current_situation": "Residents need a single, geo-tagged channel to report hazards and track escalation to the responsible authority.",
        },
        {
            "organization": "Ranchi Urban Water and Lake Cell",
            "district": "Ranchi", "state": "Jharkhand",
            "title": "Urban lake catchment restoration and waste tracking",
            "description": "Combine drain mapping, waste hotspot reporting and community stewardship around an urban lake catchment.",
            "category": "Environment & Waste Management", "subcategory": "Urban watershed",
            "address": "Urban lake catchment, Ranchi", "latitude": 23.3441, "longitude": 85.3096,
            "affected_population": 5100, "urgency": "HIGH",
            "current_situation": "A shared map of waste hotspots, drains and restoration actions would help coordinate local responses.",
        },
    ]

    gov_user = User.query.filter_by(email="gov@yugkrit.local").first()
    for case in state_cases:
        if Challenge.query.filter_by(title=case["title"]).first():
            continue
        organization = Organization.query.filter_by(name=case["organization"]).first()
        if not organization:
            organization = Organization(name=case["organization"], org_type="ULB",
                                        official_email=None, status="VERIFIED",
                                        district=case["district"], state=case["state"])
            db.session.add(organization)
            db.session.flush()
            db.session.add(ULB(organization_id=organization.id, ulb_type="Municipality",
                               category="ULB", authorized_officer="Demo Civic Officer",
                               designation="Civic Innovation Lead"))
            db.session.commit()
        challenge = challenge_service.create_challenge(organization, case)
        challenge_service.verify_challenge(challenge, gov_user, approve=True,
                                           reason="Seeded state demonstration case for product testing.")
    print("Punjab and Jharkhand state demo challenges seeded.")


def run():
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_roles_and_permissions()
        seed_categories()
        gov_org, uni_org, university, ulb_org, faculty = seed_demo_accounts()
        seed_demo_workflow(gov_org, uni_org, university, ulb_org, faculty)
        seed_citizen_demo_challenge()
        seed_state_demo_challenges()
        print("\nSeed complete.")
        print("Demo accounts — use the password below OR mobile OTP (phone shown):")
        print("  Government IT Cell : itcell@yugkrit.local   / YugKritIT@2026  / 9810000001")
        print("  Government         : gov@yugkrit.local      / YugKritGov@2026 / 9810000002")
        print("  University         : university@yugkrit.local / YugKritUni@2026 / 9810000003")
        print("  Faculty            : faculty@yugkrit.local   / YugKritFac@2026 / 9810000004")
        print("  ULB                : ulb@yugkrit.local       / YugKritULB@2026  / 9810000005")
        print("  NGO (merged ULB)   : ngo@yugkrit.local       / YugKritNGO@2026 / 9810000006")
        print("  Student            : student@college.local   / YugKritStu@2026 / 9810000007")
        print("  Citizen (verified) : citizen@yugkrit.local   / YugKritCit@2026 / 9876500000")
        print("\nOTP login is in DEV MODE (no real SMS gateway) — the OTP is shown on-screen "
              "after requesting it at /auth/login/otp.")


if __name__ == "__main__":
    run()
