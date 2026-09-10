"""YugKrit - Authentication & registration routes."""

from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.database import db
from database.models import Organization, University, UniversityDepartment, ULB, NGO, OrganizationDocument
from services import auth_service, student_service, otp_service
from utils.validators import ValidationError, validate_passwords_match, validate_phone_required
from utils.permissions import ROLE_DASHBOARD
from utils.helpers import save_uploaded_file

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


def _login_user(user):
    session.clear()
    session["user_id"] = user.id
    session.permanent = True


def _post_login_redirect(user):
    next_url = request.args.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(url_for(ROLE_DASHBOARD.get(user.role_name(), "public.home")))


# --------------------------------------------------------------------------
# Password login
# --------------------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        try:
            user = auth_service.authenticate(email, password)
            _login_user(user)
            flash(f"Welcome back, {user.full_name.split(' ')[0]}!", "success")
            return _post_login_redirect(user)
        except ValidationError as e:
            flash(e.message, "danger")
    return render_template("auth/login.html")


# --------------------------------------------------------------------------
# OTP login (mobile number) — two-step: request OTP, then verify OTP.
# --------------------------------------------------------------------------
@auth_bp.route("/login/otp", methods=["GET", "POST"])
def login_otp_request():
    if request.method == "POST":
        phone = request.form.get("phone", "")
        try:
            record, dev_otp = otp_service.request_otp(phone, purpose="LOGIN")
            session["otp_login_phone"] = record.phone
            if dev_otp:
                flash(f"[DEV MODE — no WhatsApp provider configured] Your OTP is {dev_otp}. "
                      f"It expires in {otp_service.OTP_EXPIRY_MINUTES} minutes.", "info")
            else:
                flash("An OTP has been sent to your WhatsApp number.", "success")
            return redirect(url_for("auth.login_otp_verify"))
        except ValidationError as e:
            flash(e.message, "danger")
    return render_template("auth/login_otp_request.html")


@auth_bp.route("/login/otp/verify", methods=["GET", "POST"])
def login_otp_verify():
    phone = session.get("otp_login_phone")
    if not phone:
        flash("Please enter your mobile number first.", "warning")
        return redirect(url_for("auth.login_otp_request"))

    if request.method == "POST":
        code = request.form.get("otp_code", "")
        try:
            user = otp_service.verify_otp(phone, code, purpose="LOGIN")
            session.pop("otp_login_phone", None)
            _login_user(user)
            flash(f"Welcome back, {user.full_name.split(' ')[0]}!", "success")
            return _post_login_redirect(user)
        except ValidationError as e:
            flash(e.message, "danger")
    return render_template("auth/login_otp_verify.html", phone=phone, masked_phone=_mask_phone(phone))


def _mask_phone(phone):
    if len(phone) <= 4:
        return phone
    visible = phone[-4:]
    return ("•" * (len(phone) - 4)) + visible


@auth_bp.route("/login/otp/resend", methods=["POST"])
def login_otp_resend():
    phone = session.get("otp_login_phone")
    if not phone:
        flash("Please enter your mobile number first.", "warning")
        return redirect(url_for("auth.login_otp_request"))
    try:
        record, dev_otp = otp_service.request_otp(phone, purpose="LOGIN")
        if dev_otp:
            flash(f"[DEV MODE — no WhatsApp provider configured] Your new OTP is {dev_otp}.", "info")
        else:
            flash("A new OTP has been sent to your WhatsApp number.", "success")
    except ValidationError as e:
        flash(e.message, "danger")
    return redirect(url_for("auth.login_otp_verify"))


def _start_signup_verification(user):
    auth_service.deactivate_user(user)
    record, dev_otp = otp_service.request_otp(user.phone, purpose="SIGNUP")
    session["signup_user_id"] = user.id
    session["signup_phone"] = record.phone
    if dev_otp:
        flash(f"[DEV MODE — no WhatsApp provider configured] Your signup OTP is {dev_otp}. "
              f"It expires in {otp_service.OTP_EXPIRY_MINUTES} minutes.", "info")
    else:
        flash("A signup OTP has been sent to your WhatsApp number.", "success")
    return redirect(url_for("auth.signup_otp_verify"))


@auth_bp.route("/signup/otp/verify", methods=["GET", "POST"])
def signup_otp_verify():
    phone = session.get("signup_phone")
    user_id = session.get("signup_user_id")
    if not phone or not user_id:
        flash("Please complete the signup form first.", "warning")
        return redirect(url_for("auth.register_landing"))
    if request.method == "POST":
        try:
            user = otp_service.verify_otp(phone, request.form.get("otp_code", ""), purpose="SIGNUP")
            if user.id != user_id:
                raise ValidationError("Signup verification session is invalid.", code="SIGNUP_SESSION_INVALID")
            session.pop("signup_user_id", None)
            session.pop("signup_phone", None)
            _login_user(user)
            flash("Phone verified. Your YugKrit account is ready.", "success")
            return _post_login_redirect(user)
        except ValidationError as e:
            flash(e.message, "danger")
    return render_template("auth/signup_otp_verify.html", masked_phone=_mask_phone(phone))


@auth_bp.route("/signup/otp/resend", methods=["POST"])
def signup_otp_resend():
    phone = session.get("signup_phone")
    if not phone:
        return redirect(url_for("auth.register_landing"))
    try:
        _, dev_otp = otp_service.request_otp(phone, purpose="SIGNUP")
        if dev_otp:
            flash(f"[DEV MODE — no SMS gateway configured] Your new signup OTP is {dev_otp}.", "info")
        else:
            flash("A new signup OTP has been sent.", "success")
    except ValidationError as e:
        flash(e.message, "danger")
    return redirect(url_for("auth.signup_otp_verify"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.home"))


@auth_bp.route("/register")
def register_landing():
    return render_template("auth/register_landing.html")


# --------------------------------------------------------------------------
# University registration (multi-step form, submitted as one POST)
# --------------------------------------------------------------------------
@auth_bp.route("/register/university", methods=["GET", "POST"])
def register_university():
    if request.method == "POST":
        f = request.form
        try:
            validate_passwords_match(f.get("password", ""), f.get("confirm_password", ""))
            rep_phone = validate_phone_required(f.get("rep_phone", ""))

            org = Organization(
                name=f["institution_name"], org_type="UNIVERSITY",
                official_email=f["official_email"], website=f.get("website"),
                phone=f.get("phone"), address=f.get("address"),
                district=f.get("district"), state=f.get("state"),
                status="PENDING",
            )
            db.session.add(org)
            db.session.flush()

            university = University(
                organization_id=org.id,
                institution_type=f.get("institution_type"),
                aishe_code=f.get("aishe_code"),
                affiliating_university=f.get("affiliating_university"),
                rep_name=f["rep_name"], rep_designation=f.get("rep_designation"),
                rep_email=f.get("rep_email"), rep_phone=rep_phone,
            )
            db.session.add(university)
            db.session.flush()

            for dept in ["General"]:
                db.session.add(UniversityDepartment(university_id=university.id, name=dept))

            for file_field, doc_type in [("recognition_certificate", "Recognition Certificate"),
                                          ("registration_proof", "Registration Proof"),
                                          ("authorization_letter", "Authorization Letter")]:
                file = request.files.get(file_field)
                if file and file.filename:
                    name, path, size = save_uploaded_file(file, subfolder="organizations")
                    db.session.add(OrganizationDocument(organization_id=org.id, document_type=doc_type,
                                                         file_name=name, file_path=path, file_size=size))

            db.session.commit()

            # The representative's own mobile number is used for account login
            # (password or OTP) — the institution phone (if different) stays
            # on the Organization record for official contact purposes.
            user = auth_service.create_user(f["rep_name"], f["official_email"], f["password"],
                                  "UNIVERSITY_ADMIN", organization_id=org.id, phone=rep_phone)
            return _start_signup_verification(user)
        except ValidationError as e:
            db.session.rollback()
            flash(e.message, "danger")
        except Exception:
            db.session.rollback()
            flash("Registration failed. Please check the form and try again.", "danger")
    return render_template("auth/register_university.html")


# --------------------------------------------------------------------------
# ULB / NGO registration (merged — same dashboard, same features)
# --------------------------------------------------------------------------
@auth_bp.route("/register/ulb", methods=["GET", "POST"])
def register_ulb():
    if request.method == "POST":
        f = request.form
        try:
            validate_passwords_match(f.get("password", ""), f.get("confirm_password", ""))
            phone = validate_phone_required(f.get("phone", ""))

            category = f.get("category", "ULB")  # 'ULB' or 'NGO'
            org = Organization(
                name=f["name"], org_type="ULB", official_email=f["official_email"],
                website=f.get("website"), phone=phone, address=f.get("address"),
                district=f.get("district"), state=f.get("state"), status="PENDING",
            )
            db.session.add(org)
            db.session.flush()
            ulb = ULB(organization_id=org.id, ulb_type=f.get("ulb_type"), category=category,
                      authorized_officer=f["authorized_officer"], designation=f.get("designation"),
                      registration_number=f.get("registration_number"))
            db.session.add(ulb)

            file = request.files.get("document")
            if file and file.filename:
                name, path, size = save_uploaded_file(file, subfolder="organizations")
                doc_type = "Registration Document" if category == "NGO" else "Authorization Document"
                db.session.add(OrganizationDocument(organization_id=org.id, document_type=doc_type,
                                                     file_name=name, file_path=path, file_size=size))
            db.session.commit()

            user = auth_service.create_user(f["authorized_officer"], f["official_email"], f["password"],
                                  "ULB_ADMIN", organization_id=org.id, phone=phone)
            return _start_signup_verification(user)
        except ValidationError as e:
            db.session.rollback()
            flash(e.message, "danger")
        except Exception:
            db.session.rollback()
            flash("Registration failed. Please check the form and try again.", "danger")
    return render_template("auth/register_ulb.html")


@auth_bp.route("/register/ngo")
def register_ngo():
    # NGOs are registered through the same merged ULB/NGO form.
    return redirect(url_for("auth.register_ulb", category="NGO"))


# --------------------------------------------------------------------------
# Citizen registration
# --------------------------------------------------------------------------
@auth_bp.route("/register/citizen", methods=["GET", "POST"])
def register_citizen():
    if request.method == "POST":
        f = request.form
        try:
            validate_passwords_match(f.get("password", ""), f.get("confirm_password", ""))
            phone = validate_phone_required(f.get("phone", ""))

            user = auth_service.create_user(f["full_name"], f["email"], f["password"], "CITIZEN", phone=phone)
            from services import citizen_service
            citizen_service.register_citizen(
                user,
                address=f.get("address"), city=f.get("city"),
                district=f.get("district"), state=f.get("state"),
            )
            return _start_signup_verification(user)
        except ValidationError as e:
            db.session.rollback()
            flash(e.message, "danger")
        except Exception:
            db.session.rollback()
            flash("Registration failed. Please check the form and try again.", "danger")
    return render_template("auth/register_citizen.html")


# --------------------------------------------------------------------------
# Student registration
# --------------------------------------------------------------------------
@auth_bp.route("/register/student", methods=["GET", "POST"])
def register_student():
    universities = University.query.join(University.organization).filter_by(status="VERIFIED").all()
    if request.method == "POST":
        f = request.form
        try:
            validate_passwords_match(f.get("password", ""), f.get("confirm_password", ""))
            phone = validate_phone_required(f.get("phone", ""))

            user = auth_service.create_user(f["full_name"], f["college_email"], f["password"], "STUDENT",
                                              phone=phone)
            profile = student_service.activate_student_on_registration(
                user, int(f["institution_id"]), f["registration_number"]
            )
            profile.department = f.get("department")
            profile.course = f.get("course")
            profile.year = f.get("year")
            db.session.commit()

            skills = [s.strip() for s in f.get("skills", "").split(",") if s.strip()]
            from database.models import StudentSkill, StudentInterest
            for s in skills:
                db.session.add(StudentSkill(student_id=profile.id, skill_name=s))
            interests = [s.strip() for s in f.get("interests", "").split(",") if s.strip()]
            for s in interests:
                db.session.add(StudentInterest(student_id=profile.id, interest_name=s))
            db.session.commit()

            return _start_signup_verification(user)
        except ValidationError as e:
            db.session.rollback()
            flash(e.message, "danger")
        except Exception:
            db.session.rollback()
            flash("Registration failed. Please check the form and try again.", "danger")
    return render_template("auth/register_student.html", universities=universities)
