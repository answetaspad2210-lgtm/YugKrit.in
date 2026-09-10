"""
YugKrit - Database initialization.
Single SQLAlchemy instance shared across the whole application.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

CHALLENGE_CATEGORIES = [
    "Urban Infrastructure", "Water & Sanitation", "Environment & Waste Management",
    "Public Health", "Education", "Energy", "Public Safety", "Housing & Homelessness",
    "Transportation & Mobility", "Digital Access", "Agriculture & Livelihoods", "Women & Child Safety",
    "Disability & Accessibility", "Community Services", "General Societal Challenge",
]


def init_db(app):
    """Attach SQLAlchemy to the Flask app and create tables if needed."""
    db.init_app(app)
    with app.app_context():
        db.create_all()


def ensure_rbac():
    """Create the role and permission catalog required by registration/login."""
    from database.models import Permission, Role
    from utils.permissions import ALL_PERMISSIONS, ROLE_PERMISSIONS

    permission_objects = {}
    for code, description in ALL_PERMISSIONS:
        permission = Permission.query.filter_by(code=code).first()
        if not permission:
            permission = Permission(code=code, description=description)
            db.session.add(permission)
        permission_objects[code] = permission
    db.session.flush()

    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=role_name.replace("_", " ").title())
            db.session.add(role)
            db.session.flush()
        role.permissions = [permission_objects[code] for code in permission_codes]
    db.session.commit()


def ensure_challenge_categories():
    """Keep the category catalog available for every app startup."""
    from database.models import ChallengeCategory

    for name in CHALLENGE_CATEGORIES:
        if not ChallengeCategory.query.filter_by(name=name).first():
            db.session.add(ChallengeCategory(name=name))
    db.session.commit()
