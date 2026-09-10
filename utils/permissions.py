"""
YugKrit - Permission definitions.

Permissions are independent of roles. Roles are just named bundles of
permissions (stored in the database, seeded here). To add a new role later
(Industry, Citizen, Mentor, ...), add it to ROLE_PERMISSIONS below and re-run
`python database/seed.py` — no route or template code needs to change.
"""

ALL_PERMISSIONS = [
    ("challenge.create", "Submit a new challenge"),
    ("challenge.view", "View challenges"),
    ("challenge.verify", "Verify / reject a challenge"),
    ("challenge.assign", "Assign a challenge to problem owner / university"),

    ("project.create", "Create a project"),
    ("project.view", "View projects"),
    ("project.update", "Update a project"),
    ("project.approve", "Approve / verify a project"),

    ("organization.verify", "Verify universities / ULBs / NGOs"),

    ("student.view", "View student profiles"),
    ("student.update", "Update student profiles"),

    ("document.upload", "Upload documents"),
    ("document.view", "View documents"),

    ("analytics.view", "View analytics dashboards"),
    ("audit.view", "View audit trail"),

    ("citizen.verify", "Verify citizen Aadhaar identity"),
    ("citizen.view", "View citizen profiles and submissions"),
    ("platform.monitor", "Monitor all organizations, universities, students and citizens platform-wide"),
    ("industry.profile", "Manage the industry capability profile"),
    ("industry.recommendations", "View industry challenge recommendations"),
    ("industry.collaborate", "Request and manage industry collaborations"),
    ("industry.funding", "Propose industry funding and resources"),
    ("industry.mentor", "Manage industry mentors"),
]

# Role -> list of permission codes.
ROLE_PERMISSIONS = {
    "GOVT_IT_CELL_ADMIN": [
        # Head-of-platform role: monitoring, progress tracking, validation and
        # approval rights over every organization type, universities, students
        # and citizens.
        "challenge.view", "challenge.verify", "challenge.assign",
        "project.view", "project.approve",
        "organization.verify",
        "student.view", "student.update",
        "citizen.verify", "citizen.view",
        "document.view",
        "analytics.view", "audit.view",
        "platform.monitor",
    ],
    "GOVERNMENT_ADMIN": [
        "challenge.view", "challenge.verify", "challenge.assign",
        "project.view", "project.approve",
        "organization.verify",
        "student.view",
        "document.view",
        "analytics.view", "audit.view",
    ],
    "GOVERNMENT_OFFICER": [
        "challenge.view", "challenge.verify",
        "project.view",
        "student.view",
        "document.view",
        "analytics.view",
    ],
    "UNIVERSITY_ADMIN": [
        "challenge.view",
        "project.create", "project.view", "project.update",
        "student.view", "student.update",
        "document.upload", "document.view",
        "analytics.view",
    ],
    "FACULTY": [
        "challenge.view",
        "project.view", "project.update",
        "student.view",
        "document.upload", "document.view",
    ],
    "ULB_ADMIN": [
        # Also used by NGOs — the ULB and NGO dashboards were merged into one
        # civic-body dashboard with identical features.
        "challenge.create", "challenge.view",
        "project.view",
        "document.upload", "document.view",
        "analytics.view",
    ],
    "NGO_ADMIN": [
        # Kept only for backward compatibility with accounts created before
        # NGOs were merged into the ULB dashboard. New NGO registrations are
        # created as ULB_ADMIN.
        "challenge.create", "challenge.view",
        "project.view",
        "document.upload", "document.view",
        "analytics.view",
    ],
    "STUDENT": [
        "challenge.view",
        "project.view", "project.update",
        "document.upload", "document.view",
    ],
    "CITIZEN": [
        "challenge.create", "challenge.view",
        "document.upload",
    ],
    "INDUSTRY": [
        "challenge.view", "project.view",
        "industry.profile", "industry.recommendations", "industry.collaborate",
        "industry.funding", "industry.mentor", "document.upload", "document.view",
    ],
}

ROLE_DASHBOARD = {
    "GOVT_IT_CELL_ADMIN": "itcell.overview",
    "GOVERNMENT_ADMIN": "government.overview",
    "GOVERNMENT_OFFICER": "government.overview",
    "UNIVERSITY_ADMIN": "university.overview",
    "FACULTY": "university.overview",
    "ULB_ADMIN": "ulb.overview",
    "NGO_ADMIN": "ulb.overview",
    "STUDENT": "student.overview",
    "CITIZEN": "citizen.overview",
    "INDUSTRY": "industry.dashboard",
}
