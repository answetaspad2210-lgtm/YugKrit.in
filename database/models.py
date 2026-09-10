"""
YugKrit - Database Models.

Design notes:
- One `User` table holds login credentials for every kind of account
  (government officer, university admin, ULB/NGO admin, student, and any
  future role). `Role` + `Permission` implement RBAC on top of it.
- A student is uniquely identified by (institution_id, registration_number).
  `StudentProfile` enforces this with a unique constraint so the same
  student can never be created twice, no matter how many project teams
  reference them.
- `Organization` is a generic parent for University / ULB / NGO / Government
  Department so that future organization types (Industry, MSME, CSR, etc.)
  can be added without new top-level tables.
"""

from datetime import datetime
from database.database import db


# ---------------------------------------------------------------------------
# Helper mixin
# ---------------------------------------------------------------------------
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------
role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    # e.g. GOVERNMENT_ADMIN, UNIVERSITY_ADMIN, FACULTY, ULB_ADMIN, NGO_ADMIN, STUDENT
    description = db.Column(db.String(255))
    dashboard_route = db.Column(db.String(100))  # e.g. 'student.dashboard'

    permissions = db.relationship("Permission", secondary=role_permissions, backref="roles")
    users = db.relationship("User", backref="role", lazy=True)

    def has_permission(self, code):
        return any(p.code == code for p in self.permissions)


class Permission(db.Model):
    __tablename__ = "permissions"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)  # e.g. 'challenge.verify'
    description = db.Column(db.String(255))


# ---------------------------------------------------------------------------
# USER (single login table for every role, present and future)
# ---------------------------------------------------------------------------
class User(db.Model, TimestampMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    is_email_verified = db.Column(db.Boolean, default=False)
    is_phone_verified = db.Column(db.Boolean, default=False)
    last_login_at = db.Column(db.DateTime)

    student_profile = db.relationship("StudentProfile", backref="user", uselist=False)

    def role_name(self):
        return self.role.name if self.role else None


# ---------------------------------------------------------------------------
# ORGANIZATIONS (generic parent: University / ULB / NGO / Govt Dept / future types)
# ---------------------------------------------------------------------------
class Organization(db.Model, TimestampMixin):
    __tablename__ = "organizations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    org_type = db.Column(db.String(30), nullable=False)
    # 'GOVERNMENT', 'UNIVERSITY', 'ULB', 'NGO'  (extensible: 'INDUSTRY', 'MSME', ...)

    official_email = db.Column(db.String(150))
    website = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(300))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))

    status = db.Column(db.String(20), default="PENDING")
    # PENDING, UNDER_REVIEW, VERIFIED, REJECTED, SUSPENDED
    verified_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    verified_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.String(500))

    users = db.relationship("User", backref="organization", lazy=True, foreign_keys="User.organization_id")
    documents = db.relationship("OrganizationDocument", backref="organization", lazy=True)


class OrganizationDocument(db.Model, TimestampMixin):
    __tablename__ = "organization_documents"
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    document_type = db.Column(db.String(100))  # Recognition Certificate, Registration Proof...
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)


class GovernmentDepartment(db.Model, TimestampMixin):
    __tablename__ = "government_departments"
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    department_name = db.Column(db.String(200))
    jurisdiction_level = db.Column(db.String(50))  # STATE, DISTRICT, CITY

    organization = db.relationship("Organization", backref="government_department", uselist=False)


class University(db.Model, TimestampMixin):
    __tablename__ = "universities"
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    institution_type = db.Column(db.String(100))
    aishe_code = db.Column(db.String(50))
    affiliating_university = db.Column(db.String(200))
    rep_name = db.Column(db.String(150))
    rep_designation = db.Column(db.String(100))
    rep_email = db.Column(db.String(150))
    rep_phone = db.Column(db.String(20))

    organization = db.relationship("Organization", backref="university", uselist=False)
    departments = db.relationship("UniversityDepartment", backref="university", lazy=True)


class UniversityDepartment(db.Model, TimestampMixin):
    __tablename__ = "university_departments"
    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.Integer, db.ForeignKey("universities.id"), nullable=False)
    name = db.Column(db.String(150))


class Faculty(db.Model, TimestampMixin):
    __tablename__ = "faculty"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey("universities.id"), nullable=False)
    department = db.Column(db.String(150))
    designation = db.Column(db.String(100))

    user = db.relationship("User", backref="faculty_profile", uselist=False)
    university = db.relationship("University", backref="faculty_members")


class ULB(db.Model, TimestampMixin):
    __tablename__ = "ulbs"
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    ulb_type = db.Column(db.String(100))  # Municipal Corporation, Municipality...
    category = db.Column(db.String(20), default="ULB")  # 'ULB' or 'NGO' — merged dashboard
    authorized_officer = db.Column(db.String(150))
    designation = db.Column(db.String(100))
    registration_number = db.Column(db.String(100))  # used when category == 'NGO'

    organization = db.relationship("Organization", backref="ulb", uselist=False)


class IndustryProfile(db.Model, TimestampMixin):
    """Structured capabilities for an industry or innovation partner."""
    __tablename__ = "industry_profiles"
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False, unique=True)
    organization_type = db.Column(db.String(50), nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    sub_sector = db.Column(db.String(100))
    organization_size = db.Column(db.String(50))
    description = db.Column(db.Text)
    expertise = db.Column(db.Text)  # comma-separated structured tags
    technologies = db.Column(db.Text)
    services = db.Column(db.Text)
    csr_focus_areas = db.Column(db.Text)
    available_resources = db.Column(db.Text)
    contact_person = db.Column(db.String(150))
    organization = db.relationship("Organization", backref=db.backref("industry_profile", uselist=False))
    mentors = db.relationship("IndustryMentor", backref="industry", lazy=True, cascade="all, delete-orphan")


class IndustryMentor(db.Model, TimestampMixin):
    __tablename__ = "industry_mentors"
    id = db.Column(db.Integer, primary_key=True)
    industry_id = db.Column(db.Integer, db.ForeignKey("industry_profiles.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    designation = db.Column(db.String(120))
    expertise = db.Column(db.Text)
    experience = db.Column(db.String(100))
    skills = db.Column(db.Text)
    contact = db.Column(db.String(150))
    is_active = db.Column(db.Boolean, default=True)


class NGO(db.Model, TimestampMixin):
    __tablename__ = "ngos"
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    registration_number = db.Column(db.String(100))
    registration_authority = db.Column(db.String(150))
    registration_date = db.Column(db.Date)
    authorized_rep = db.Column(db.String(150))

    organization = db.relationship("Organization", backref="ngo", uselist=False)


# ---------------------------------------------------------------------------
# CITIZEN (Aadhaar-based identity — the platform never stores the full
# Aadhaar number, only a one-way hash for dedupe and the last 4 digits for
# display, consistent with data-minimisation best practice)
# ---------------------------------------------------------------------------
class CitizenProfile(db.Model, TimestampMixin):
    __tablename__ = "citizen_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    aadhaar_hash = db.Column(db.String(128), unique=True, nullable=False)  # sha256 of full number
    aadhaar_last4 = db.Column(db.String(4), nullable=False)

    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))

    verification_status = db.Column(db.String(20), default="PENDING")  # PENDING, VERIFIED, REJECTED
    verified_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    verified_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.String(500))

    user = db.relationship("User", foreign_keys=[user_id],
                            backref=db.backref("citizen_profile", uselist=False), uselist=False)
    verified_by = db.relationship("User", foreign_keys=[verified_by_id])

    def masked_aadhaar(self):
        return f"XXXX-XXXX-{self.aadhaar_last4}"


# ---------------------------------------------------------------------------
# STUDENT (single canonical profile per person)
# ---------------------------------------------------------------------------
class StudentProfile(db.Model, TimestampMixin):
    __tablename__ = "student_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # null until user accepts invite
    institution_id = db.Column(db.Integer, db.ForeignKey("universities.id"), nullable=False)
    registration_number = db.Column(db.String(50), nullable=False)

    full_name = db.Column(db.String(150), nullable=False)
    college_email = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(150))
    course = db.Column(db.String(100))
    year = db.Column(db.String(20))
    phone = db.Column(db.String(20))

    status = db.Column(db.String(20), default="INVITED")  # INVITED, ACTIVE

    institution = db.relationship("University", backref="students")
    skills = db.relationship("StudentSkill", backref="student", lazy=True, cascade="all, delete-orphan")
    interests = db.relationship("StudentInterest", backref="student", lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("institution_id", "registration_number", name="uq_student_institution_regno"),
    )

    def stats(self):
        completed = [m for m in self.team_memberships if m.team.project.status == "COMPLETED"]
        return {
            "projects_completed": len(completed),
            "certificates": len(self.certificates),
            "skills": len(self.skills),
        }


class StudentSkill(db.Model):
    __tablename__ = "student_skills"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.String(20), default="INTERMEDIATE")  # BEGINNER/INTERMEDIATE/ADVANCED


class StudentInterest(db.Model):
    __tablename__ = "student_interests"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    interest_name = db.Column(db.String(100), nullable=False)


# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
class ChallengeCategory(db.Model):
    __tablename__ = "challenge_categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(50), default="fa-lightbulb")


class Challenge(db.Model, TimestampMixin):
    __tablename__ = "challenges"
    id = db.Column(db.Integer, primary_key=True)
    challenge_code = db.Column(db.String(30), unique=True)  # e.g. YK-2026-000123
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey("challenge_categories.id"))
    subcategory = db.Column(db.String(100))

    submitted_by_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    submitted_by_citizen_id = db.Column(db.Integer, db.ForeignKey("citizen_profiles.id"), nullable=True)
    problem_owner_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    assigned_university_id = db.Column(db.Integer, db.ForeignKey("universities.id"), nullable=True)

    affected_population = db.Column(db.Integer, default=0)
    urgency = db.Column(db.String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    current_situation = db.Column(db.Text)
    supporting_info = db.Column(db.Text)

    priority_score = db.Column(db.Integer, default=0)  # 0-100, AI or gov assigned
    status = db.Column(db.String(30), default="SUBMITTED")
    # SUBMITTED, UNDER_REVIEW, VERIFIED, REJECTED, ASSIGNED, IN_PROGRESS, RESOLVED

    difficulty = db.Column(db.String(20), default="MEDIUM")  # EASY, MEDIUM, HARD
    required_skills = db.Column(db.String(300))  # comma separated for simplicity

    category = db.relationship("ChallengeCategory", backref="challenges")
    submitted_by_org = db.relationship("Organization", foreign_keys=[submitted_by_org_id])
    submitted_by_citizen = db.relationship("CitizenProfile", foreign_keys=[submitted_by_citizen_id],
                                            backref="submitted_challenges")
    problem_owner_org = db.relationship("Organization", foreign_keys=[problem_owner_org_id])
    assigned_university = db.relationship("University", foreign_keys=[assigned_university_id])
    location = db.relationship("ChallengeLocation", backref="challenge", uselist=False,
                                cascade="all, delete-orphan")
    evidence_items = db.relationship("ChallengeEvidence", backref="challenge", lazy=True,
                                      cascade="all, delete-orphan")
    ai_analysis = db.relationship("AIAnalysis", backref="challenge", uselist=False,
                                   cascade="all, delete-orphan")
    applications = db.relationship("UniversityApplication", backref="challenge", lazy=True)

    def submitter_name(self):
        if self.submitted_by_org:
            return self.submitted_by_org.name
        if self.submitted_by_citizen:
            return f"{self.submitted_by_citizen.user.full_name} (Citizen)"
        return "Unknown"


class ChallengeLocation(db.Model):
    __tablename__ = "challenge_locations"
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    address = db.Column(db.String(300))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)


class ChallengeEvidence(db.Model, TimestampMixin):
    __tablename__ = "challenge_evidence"
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    evidence_type = db.Column(db.String(20))  # PHOTO, VIDEO, DOCUMENT
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))


class ChallengeAssignment(db.Model, TimestampMixin):
    """Audit trail of who a challenge was assigned to and by whom."""
    __tablename__ = "challenge_assignments"
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    assigned_to_type = db.Column(db.String(30))  # PROBLEM_OWNER, UNIVERSITY
    assigned_to_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"))
    assigned_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    challenge = db.relationship("Challenge", backref="assignments")


class AIAnalysis(db.Model, TimestampMixin):
    __tablename__ = "ai_analyses"
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    suggested_category = db.Column(db.String(100))
    priority_score = db.Column(db.Integer)
    suggested_skills = db.Column(db.String(300))
    university_matches = db.Column(db.Text)  # JSON string: [{"name":..,"score":..}]
    similar_challenge_ids = db.Column(db.String(200))
    human_review_required = db.Column(db.Boolean, default=True)
    overridden_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class UniversityApplication(db.Model, TimestampMixin):
    __tablename__ = "university_applications"
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey("universities.id"), nullable=False)
    applied_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    pitch = db.Column(db.Text)
    status = db.Column(db.String(20), default="PENDING")  # PENDING, ACCEPTED, REJECTED

    university = db.relationship("University", backref="applications")


# ---------------------------------------------------------------------------
# PROJECTS
# ---------------------------------------------------------------------------
class Project(db.Model, TimestampMixin):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    project_code = db.Column(db.String(30), unique=True)
    name = db.Column(db.String(200), nullable=False)
    objective = db.Column(db.Text)
    description = db.Column(db.Text)
    expected_outcome = db.Column(db.Text)

    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey("universities.id"), nullable=False)
    faculty_mentor_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=True)

    start_date = db.Column(db.Date)
    expected_completion = db.Column(db.Date)

    status = db.Column(db.String(30), default="PLANNING")
    # PLANNING, IN_PROGRESS, UNDER_REVIEW, COMPLETED, VERIFIED

    research_progress = db.Column(db.Integer, default=0)
    design_progress = db.Column(db.Integer, default=0)
    prototype_progress = db.Column(db.Integer, default=0)
    testing_progress = db.Column(db.Integer, default=0)
    validation_progress = db.Column(db.Integer, default=0)

    challenge = db.relationship("Challenge", backref="projects")
    university = db.relationship("University", backref="projects")
    faculty_mentor = db.relationship("Faculty", backref="mentored_projects")
    teams = db.relationship("ProjectTeam", backref="project", lazy=True, cascade="all, delete-orphan")
    milestones = db.relationship("Milestone", backref="project", lazy=True, cascade="all, delete-orphan")
    impact = db.relationship("ProjectImpact", backref="project", uselist=False, cascade="all, delete-orphan")
    evaluation = db.relationship("ProjectEvaluation", backref="project", uselist=False,
                                  cascade="all, delete-orphan")
    collaborations = db.relationship("IndustryCollaboration", backref="project", lazy=True)


class IndustryCollaborationRequest(db.Model, TimestampMixin):
    __tablename__ = "industry_collaboration_requests"
    id = db.Column(db.Integer, primary_key=True)
    industry_id = db.Column(db.Integer, db.ForeignKey("industry_profiles.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)
    university_id = db.Column(db.Integer, db.ForeignKey("universities.id"), nullable=True)
    proposal_type = db.Column(db.String(100), nullable=False)
    support_types = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    estimated_contribution = db.Column(db.String(200))
    expected_duration = db.Column(db.String(100))
    experts = db.Column(db.Text)
    budget = db.Column(db.Numeric(12, 2))
    status = db.Column(db.String(30), default="REQUESTED", nullable=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    review_note = db.Column(db.String(500))

    industry = db.relationship("IndustryProfile", backref="collaboration_requests")
    challenge = db.relationship("Challenge", backref="industry_requests")
    project = db.relationship("Project", backref="industry_requests")
    university = db.relationship("University", backref="industry_requests")
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])


class IndustryCollaboration(db.Model, TimestampMixin):
    __tablename__ = "industry_collaborations"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("industry_collaboration_requests.id"), nullable=False, unique=True)
    industry_id = db.Column(db.Integer, db.ForeignKey("industry_profiles.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(30), default="ACTIVE", nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    request = db.relationship("IndustryCollaborationRequest", backref=db.backref("collaboration", uselist=False))
    industry = db.relationship("IndustryProfile", backref="collaborations")
    approved_by = db.relationship("User", foreign_keys=[approved_by_id])


class IndustryFunding(db.Model, TimestampMixin):
    __tablename__ = "industry_funding"
    id = db.Column(db.Integer, primary_key=True)
    industry_id = db.Column(db.Integer, db.ForeignKey("industry_profiles.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=True)
    purpose = db.Column(db.String(300), nullable=False)
    expected_outcome = db.Column(db.Text)
    duration = db.Column(db.String(100))
    terms = db.Column(db.Text)
    status = db.Column(db.String(30), default="PROPOSED", nullable=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class IndustryResourceOffer(db.Model, TimestampMixin):
    __tablename__ = "industry_resource_offers"
    id = db.Column(db.Integer, primary_key=True)
    industry_id = db.Column(db.Integer, db.ForeignKey("industry_profiles.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    resource_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="PROPOSED", nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class PilotProject(db.Model, TimestampMixin):
    __tablename__ = "pilot_projects"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    industry_id = db.Column(db.Integer, db.ForeignKey("industry_profiles.id"), nullable=False)
    proposed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(30), default="PILOT_REQUESTED", nullable=False)
    location = db.Column(db.String(200))
    proposed_start = db.Column(db.Date)
    proposed_end = db.Column(db.Date)
    outcome = db.Column(db.Text)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class ProjectTeam(db.Model, TimestampMixin):
    __tablename__ = "project_teams"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    team_name = db.Column(db.String(150))
    team_leader_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=True)

    members = db.relationship("ProjectTeamMember", backref="team", lazy=True, cascade="all, delete-orphan")
    team_leader = db.relationship("StudentProfile", foreign_keys=[team_leader_id])


class ProjectTeamMember(db.Model, TimestampMixin):
    __tablename__ = "project_team_members"
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("project_teams.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    role_in_team = db.Column(db.String(50), default="Developer")
    # Team Leader, Developer, Researcher, Designer, Data Analyst, Field Coordinator, Other

    student = db.relationship("StudentProfile", backref="team_memberships")

    __table_args__ = (db.UniqueConstraint("team_id", "student_id", name="uq_team_student"),)


class Task(db.Model, TimestampMixin):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey("milestones.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=True)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default="TODO")  # TODO, IN_PROGRESS, DONE

    project = db.relationship("Project", backref="tasks")
    assigned_to = db.relationship("StudentProfile", backref="tasks")


class Milestone(db.Model, TimestampMixin):
    __tablename__ = "milestones"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    # Problem Research, Solution Design, Prototype, Testing, Community Validation,
    # Pilot, Implementation, Final Submission
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=True)
    due_date = db.Column(db.Date)
    sequence = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default="NOT_STARTED")
    # NOT_STARTED, IN_PROGRESS, SUBMITTED, UNDER_REVIEW, APPROVED, CHANGES_REQUESTED, COMPLETED
    reviewer_comment = db.Column(db.Text)

    owner = db.relationship("StudentProfile", backref="owned_milestones")
    deliverables = db.relationship("Deliverable", backref="milestone", lazy=True, cascade="all, delete-orphan")


class Deliverable(db.Model, TimestampMixin):
    __tablename__ = "deliverables"
    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey("milestones.id"), nullable=False)
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    description = db.Column(db.String(300))


class ProjectEvaluation(db.Model, TimestampMixin):
    __tablename__ = "project_evaluations"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    evaluated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    score = db.Column(db.Integer)
    comments = db.Column(db.Text)
    verified = db.Column(db.Boolean, default=False)


class CommunityValidation(db.Model, TimestampMixin):
    __tablename__ = "community_validations"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    validated_by_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"))
    feedback = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5

    project = db.relationship("Project", backref="community_validations")


class ProjectImpact(db.Model, TimestampMixin):
    __tablename__ = "project_impacts"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    people_impacted = db.Column(db.Integer, default=0)
    summary = db.Column(db.Text)


# ---------------------------------------------------------------------------
# ACHIEVEMENTS / CERTIFICATES
# ---------------------------------------------------------------------------
class Achievement(db.Model, TimestampMixin):
    __tablename__ = "achievements"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True)
    title = db.Column(db.String(150))
    description = db.Column(db.String(300))
    icon = db.Column(db.String(50), default="fa-award")


class StudentAchievement(db.Model, TimestampMixin):
    __tablename__ = "student_achievements"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievements.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)

    student = db.relationship("StudentProfile", backref="achievements")
    achievement = db.relationship("Achievement")
    project = db.relationship("Project")


class Certificate(db.Model, TimestampMixin):
    __tablename__ = "certificates"
    id = db.Column(db.Integer, primary_key=True)
    certificate_id = db.Column(db.String(50), unique=True, nullable=False)  # public verification id
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    role_in_project = db.Column(db.String(50))
    issued_date = db.Column(db.Date, default=datetime.utcnow)

    student = db.relationship("StudentProfile", backref="certificates")
    project = db.relationship("Project", backref="certificates")


# ---------------------------------------------------------------------------
# NOTIFICATIONS / MESSAGES / AUDIT
# ---------------------------------------------------------------------------
class Notification(db.Model, TimestampMixin):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200))
    message = db.Column(db.String(500))
    link = db.Column(db.String(300))
    is_read = db.Column(db.Boolean, default=False)

    user = db.relationship("User", backref="notifications")


class Message(db.Model, TimestampMixin):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)
    body = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    role_name = db.Column(db.String(50))
    action = db.Column(db.String(100))
    entity = db.Column(db.String(100))
    entity_id = db.Column(db.Integer)
    previous_value = db.Column(db.String(500))
    new_value = db.Column(db.String(500))
    reason = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")


# ---------------------------------------------------------------------------
# OTP (mobile-number login / verification)
# ---------------------------------------------------------------------------
class OTPCode(db.Model):
    """One-time-password codes for mobile-number based login.

    Like Aadhaar numbers, the OTP code itself is never stored in plain text —
    only a SHA-256 hash is kept, compared against the hash of the code the
    user submits. See services/otp_service.py for delivery + verification.
    """
    __tablename__ = "otp_codes"
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    purpose = db.Column(db.String(20), default="LOGIN")  # LOGIN, REGISTRATION

    code_hash = db.Column(db.String(128), nullable=False)
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=5)

    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def is_exhausted(self):
        return self.attempts >= self.max_attempts
