"""Tests for OTP (mobile number) login and password-confirmation on registration."""

import re
import pytest
from database.database import db
from services import auth_service, otp_service


def test_request_otp_creates_hashed_code(app):
    with app.app_context():
        auth_service.create_user("OTP User", "otpuser1@test.local", "Demo@123", "STUDENT", phone="9000000001")
        record, dev_otp = otp_service.request_otp("9000000001", purpose="LOGIN")
        assert dev_otp is not None
        assert len(dev_otp) == 6
        assert record.code_hash != dev_otp  # never stored in plain text
        assert len(record.code_hash) == 64  # sha256 hex digest


def test_correct_otp_logs_user_in(app):
    with app.app_context():
        auth_service.create_user("OTP User 2", "otpuser2@test.local", "Demo@123", "STUDENT", phone="9000000002")
        record, dev_otp = otp_service.request_otp("9000000002", purpose="LOGIN")
        user = otp_service.verify_otp("9000000002", dev_otp, purpose="LOGIN")
        assert user.email == "otpuser2@test.local"
        assert user.is_phone_verified is True


def test_incorrect_otp_is_rejected_and_counts_attempt(app):
    from utils.validators import ValidationError
    with app.app_context():
        auth_service.create_user("OTP User 3", "otpuser3@test.local", "Demo@123", "STUDENT", phone="9000000003")
        otp_service.request_otp("9000000003", purpose="LOGIN")
        with pytest.raises(ValidationError):
            otp_service.verify_otp("9000000003", "000000", purpose="LOGIN")

        from database.models import OTPCode
        record = OTPCode.query.filter_by(phone="9000000003").first()
        assert record.attempts == 1


def test_otp_exhausted_after_max_attempts(app):
    from utils.validators import ValidationError
    with app.app_context():
        auth_service.create_user("OTP User 4", "otpuser4@test.local", "Demo@123", "STUDENT", phone="9000000004")
        otp_service.request_otp("9000000004", purpose="LOGIN")
        for _ in range(5):
            with pytest.raises(ValidationError):
                otp_service.verify_otp("9000000004", "111111", purpose="LOGIN")
        with pytest.raises(ValidationError) as exc_info:
            otp_service.verify_otp("9000000004", "111111", purpose="LOGIN")
        assert exc_info.value.code == "OTP_EXHAUSTED"


def test_otp_resend_cooldown_enforced(app):
    from utils.validators import ValidationError
    with app.app_context():
        otp_service.request_otp("9000000005", purpose="LOGIN")
        with pytest.raises(ValidationError) as exc_info:
            otp_service.request_otp("9000000005", purpose="LOGIN")
        assert exc_info.value.code == "OTP_COOLDOWN"


def test_otp_login_unknown_phone_rejected(app):
    from utils.validators import ValidationError
    with app.app_context():
        record, dev_otp = otp_service.request_otp("9000099999", purpose="LOGIN")
        with pytest.raises(ValidationError) as exc_info:
            otp_service.verify_otp("9000099999", dev_otp, purpose="LOGIN")
        assert exc_info.value.code == "PHONE_NOT_FOUND"


def test_otp_login_end_to_end_via_http(app, client):
    with app.app_context():
        auth_service.create_user("HTTP OTP User", "httpotp@test.local", "Demo@123", "STUDENT",
                                   phone="9000000006")

    r1 = client.post("/auth/login/otp", data={"phone": "9000000006"}, follow_redirects=True)
    assert r1.status_code == 200
    match = re.search(rb"Your OTP is (\d{6})", r1.data)
    assert match is not None
    otp_code = match.group(1).decode()

    r2 = client.post("/auth/login/otp/verify", data={"otp_code": otp_code}, follow_redirects=True)
    assert r2.status_code == 200
    assert b"Welcome back" in r2.data


def test_registration_requires_matching_passwords(app, client):
    resp = client.post("/auth/register/citizen", data={
        "full_name": "Mismatch Citizen", "email": "mismatchcitizen@test.local",
        "aadhaar_number": "999988887777", "phone": "9000000007",
        "password": "Demo@123", "confirm_password": "Other@123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"do not match" in resp.data

    from database.models import User
    with app.app_context():
        assert User.query.filter_by(email="mismatchcitizen@test.local").first() is None


def test_citizen_signup_requires_phone_otp_not_aadhaar(app, client):
    response = client.post("/auth/register/citizen", data={
        "full_name": "OTP Citizen", "email": "otpcitizen@test.local",
        "phone": "9000000010", "city": "Ranchi", "district": "Ranchi",
        "state": "Jharkhand", "password": "Demo@123", "confirm_password": "Demo@123",
    }, follow_redirects=True)
    assert response.status_code == 200
    match = re.search(rb"Your signup OTP is (\d{6})", response.data)
    assert match is not None

    from database.models import User, CitizenProfile
    with app.app_context():
        user = User.query.filter_by(email="otpcitizen@test.local").first()
        assert user is not None
        assert user.is_active is False
        assert CitizenProfile.query.filter_by(user_id=user.id).count() == 1

    verified = client.post("/auth/signup/otp/verify", data={
        "otp_code": match.group(1).decode(),
    }, follow_redirects=True)
    assert verified.status_code == 200
    assert b"Phone verified" in verified.data

    with app.app_context():
        user = User.query.filter_by(email="otpcitizen@test.local").first()
        assert user.is_active is True
        assert user.is_phone_verified is True


def test_registration_requires_phone_number(app, client):
    resp = client.post("/auth/register/citizen", data={
        "full_name": "No Phone Citizen", "email": "nophonecitizen@test.local",
        "aadhaar_number": "999988886666", "phone": "",
        "password": "Demo@123", "confirm_password": "Demo@123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Mobile number is required" in resp.data


def test_duplicate_phone_number_rejected(app):
    from utils.validators import ValidationError
    with app.app_context():
        auth_service.create_user("First Phone Owner", "firstphone@test.local", "Demo@123", "STUDENT",
                                   phone="9000000008")
        with pytest.raises(ValidationError) as exc_info:
            auth_service.create_user("Second Phone Owner", "secondphone@test.local", "Demo@123", "STUDENT",
                                       phone="9000000008")
        assert exc_info.value.code == "PHONE_EXISTS"
