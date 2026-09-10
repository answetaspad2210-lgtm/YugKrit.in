"""YugKrit - Authentication service."""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database.database import db
from database.models import User, Role
from utils.validators import validate_email, validate_password, ValidationError
from services.audit_service import log_action


def hash_password(raw_password):
    return generate_password_hash(raw_password)


def verify_password(raw_password, password_hash):
    return check_password_hash(password_hash, raw_password)


def authenticate(email, password):
    email = validate_email(email)
    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValidationError("Invalid email or password.", code="INVALID_CREDENTIALS")
    if not user.is_active:
        raise ValidationError("This account has been deactivated.", code="ACCOUNT_INACTIVE")

    user.last_login_at = datetime.utcnow()
    db.session.commit()
    log_action(user, "LOGIN", "User", user.id)
    return user


def create_user(full_name, email, password, role_name, organization_id=None, phone=None):
    email = validate_email(email)
    validate_password(password)

    if User.query.filter_by(email=email).first():
        raise ValidationError("An account with this email already exists.", code="EMAIL_EXISTS")

    if phone and User.query.filter_by(phone=phone).first():
        raise ValidationError("An account with this mobile number already exists.", code="PHONE_EXISTS")

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        raise ValidationError(f"Unknown role: {role_name}", code="INVALID_ROLE")

    user = User(
        full_name=full_name.strip(),
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role_id=role.id,
        organization_id=organization_id,
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    log_action(user, "REGISTER", "User", user.id)
    return user


def deactivate_user(user):
    """Keep a newly registered account closed until phone OTP verification."""
    user.is_active = False
    db.session.commit()
    return user
