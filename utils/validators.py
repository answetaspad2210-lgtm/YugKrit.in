"""YugKrit - Input validation helpers."""

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REGNO_RE = re.compile(r"^[A-Za-z0-9\-\/]{4,50}$")
AADHAAR_RE = re.compile(r"^\d{12}$")


class ValidationError(Exception):
    def __init__(self, message, code="VALIDATION_ERROR", field=None):
        self.message = message
        self.code = code
        self.field = field
        super().__init__(message)


def require_fields(data, fields):
    missing = [f for f in fields if not str(data.get(f, "")).strip()]
    if missing:
        raise ValidationError(f"Missing required field(s): {', '.join(missing)}", field=missing[0])


def validate_email(email):
    if not email or not EMAIL_RE.match(email):
        raise ValidationError("Invalid email address.", field="email")
    return email.strip().lower()


def validate_password(password):
    if not password or len(password) < 6:
        raise ValidationError("Password must be at least 6 characters.", field="password")
    return password


def validate_passwords_match(password, confirm_password):
    validate_password(password)
    if password != confirm_password:
        raise ValidationError("Password and Confirm Password do not match.", field="confirm_password")
    return password


def validate_phone_required(phone):
    if not phone or not phone.strip():
        raise ValidationError("Mobile number is required.", field="phone")
    cleaned = re.sub(r"[\s\-]", "", phone)
    if not re.match(r"^\+?\d{7,15}$", cleaned):
        raise ValidationError("Invalid mobile number.", field="phone")
    return cleaned


def validate_otp_code(code):
    cleaned = re.sub(r"\s", "", code or "")
    if not re.match(r"^\d{6}$", cleaned):
        raise ValidationError("Enter the 6-digit OTP sent to your mobile number.", field="otp_code")
    return cleaned


def validate_registration_number(reg_no):
    if not reg_no or not REGNO_RE.match(reg_no.strip()):
        raise ValidationError("Invalid registration number.", field="registration_number")
    return reg_no.strip().upper()


def validate_phone(phone):
    if phone and not re.match(r"^[0-9+\-\s]{7,15}$", phone):
        raise ValidationError("Invalid phone number.", field="phone")
    return phone


def validate_aadhaar(aadhaar_number):
    """Format-check only (12 digits). YugKrit never persists the full
    number — only a hash + last 4 digits (see services/auth_service.py)."""
    cleaned = re.sub(r"\s|-", "", aadhaar_number or "")
    if not AADHAAR_RE.match(cleaned):
        raise ValidationError("Aadhaar number must be exactly 12 digits.", field="aadhaar_number")
    return cleaned
