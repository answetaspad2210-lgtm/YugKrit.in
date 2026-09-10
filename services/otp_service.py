"""YugKrit - OTP generation, storage, and WhatsApp delivery.

- The OTP code itself is never stored in plain text — only a SHA-256 hash.
- Codes expire after `OTP_EXPIRY_MINUTES` and are rate-limited by both a
  minimum resend interval and a maximum verification-attempt count.
"""

import hashlib
import os
import random
from datetime import datetime, timedelta

from database.database import db
from database.models import OTPCode, User
from utils.validators import validate_phone_required, validate_otp_code, ValidationError

OTP_EXPIRY_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 30
WHATSAPP_PROVIDER = os.environ.get(
    "WHATSAPP_PROVIDER", "console" if os.environ.get("FLASK_DEBUG", "1") == "1" else "cloud_api"
).lower()
DEV_MODE = WHATSAPP_PROVIDER == "console"


def _hash_code(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _dispatch_whatsapp(phone, code):
    """Send the OTP through Meta WhatsApp Cloud API or return it in console mode."""
    if DEV_MODE:
        return code

    if WHATSAPP_PROVIDER != "cloud_api":
        raise ValidationError(
            "WHATSAPP_PROVIDER must be 'cloud_api' for real OTP delivery.",
            code="WHATSAPP_NOT_CONFIGURED",
        )

    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
    template_name = os.environ.get("WHATSAPP_TEMPLATE_NAME", "yugkrit_otp")
    template_language = os.environ.get("WHATSAPP_TEMPLATE_LANGUAGE", "en_US")
    if not all((phone_number_id, access_token, template_name, template_language)):
        raise ValidationError(
            "WhatsApp delivery is not configured. Set the Meta WhatsApp environment variables.",
            code="WHATSAPP_NOT_CONFIGURED",
        )

    try:
        import requests

        country_code = os.environ.get("WHATSAPP_DEFAULT_COUNTRY_CODE", "+91")
        destination = phone if phone.startswith("+") else f"{country_code}{phone}"
        response = requests.post(
            f"https://graph.facebook.com/v22.0/{phone_number_id}/messages",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": destination.lstrip("+"),
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": template_language},
                    "components": [{
                        "type": "body",
                        "parameters": [{"type": "text", "text": code}],
                    }],
                },
            },
            timeout=15,
        )
        if not response.ok:
            raise RuntimeError(f"WhatsApp API returned HTTP {response.status_code}")
    except ImportError as exc:
        raise ValidationError(
            "The requests package is not installed. Run pip install -r requirements.txt.",
            code="WHATSAPP_NOT_CONFIGURED",
        ) from exc
    except Exception as exc:
        raise ValidationError(
            "Unable to send the WhatsApp OTP. Please try again shortly.",
            code="WHATSAPP_SEND_FAILED",
        ) from exc

    return None


def request_otp(phone, purpose="LOGIN"):
    """Generate, hash, store, and 'send' a fresh OTP for the given phone
    number. Returns (otp_record, dev_otp) where dev_otp is only populated
    in development mode for on-screen display."""
    phone = validate_phone_required(phone)

    recent = (OTPCode.query.filter_by(phone=phone, purpose=purpose)
              .order_by(OTPCode.created_at.desc()).first())
    if recent and not recent.is_expired():
        seconds_since = (datetime.utcnow() - recent.created_at).total_seconds()
        if seconds_since < OTP_RESEND_COOLDOWN_SECONDS:
            wait = int(OTP_RESEND_COOLDOWN_SECONDS - seconds_since)
            raise ValidationError(f"Please wait {wait}s before requesting another OTP.",
                                   code="OTP_COOLDOWN")

    code = f"{random.randint(0, 999999):06d}"
    record = OTPCode(
        phone=phone, purpose=purpose, code_hash=_hash_code(code),
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    db.session.add(record)
    try:
        db.session.flush()
        dev_otp = _dispatch_whatsapp(phone, code)
        db.session.commit()
    except ValidationError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise ValidationError("Unable to send the WhatsApp OTP. Please try again shortly.",
                      code="WHATSAPP_SEND_FAILED")
    return record, dev_otp


def verify_otp(phone, code, purpose="LOGIN"):
    """Verify an OTP and return the matching user for login OTPs."""
    phone = validate_phone_required(phone)
    code = validate_otp_code(code)

    record = (OTPCode.query.filter_by(phone=phone, purpose=purpose, is_verified=False)
              .order_by(OTPCode.created_at.desc()).first())
    if not record:
        raise ValidationError("No pending OTP request found for this number. Please request a new one.",
                               code="OTP_NOT_FOUND")
    if record.is_expired():
        raise ValidationError("This OTP has expired. Please request a new one.", code="OTP_EXPIRED")
    if record.is_exhausted():
        raise ValidationError("Too many incorrect attempts. Please request a new OTP.",
                               code="OTP_EXHAUSTED")

    if _hash_code(code) != record.code_hash:
        record.attempts += 1
        db.session.commit()
        remaining = record.max_attempts - record.attempts
        raise ValidationError(f"Incorrect OTP. {max(remaining, 0)} attempt(s) remaining.",
                               code="OTP_INCORRECT")

    record.is_verified = True
    db.session.commit()

    if purpose == "LOGIN":
        user = User.query.filter_by(phone=phone).first()
        if not user:
            raise ValidationError("No account found with this mobile number.", code="PHONE_NOT_FOUND")
        if not user.is_active:
            raise ValidationError("This account has been deactivated.", code="ACCOUNT_INACTIVE")
        user.is_phone_verified = True
        db.session.commit()
        return user

    if purpose == "SIGNUP":
        user = User.query.filter_by(phone=phone).first()
        if not user:
            raise ValidationError("No pending signup found for this mobile number.", code="PHONE_NOT_FOUND")
        user.is_phone_verified = True
        user.is_active = True
        db.session.commit()
        return user

    return None
