"""
YugKrit - Reusable auth/RBAC decorators.

Usage:

    @login_required
    def some_view(): ...

    @role_required("GOVERNMENT_ADMIN", "GOVERNMENT_OFFICER")
    def gov_only_view(): ...

    @permission_required("challenge.verify")
    def verify_view(): ...
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from database.database import db
from database.models import User


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": {"code": "AUTH_REQUIRED",
                                                              "message": "Login required"}}), 401
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def role_required(*role_names):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user or user.role_name() not in role_names:
                if request.path.startswith("/api/"):
                    return jsonify({"success": False, "error": {"code": "FORBIDDEN",
                                                                  "message": "Not authorized"}}), 403
                flash("You do not have access to that page.", "danger")
                return redirect(url_for("public.home"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def permission_required(*permission_codes):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user or not user.role:
                return _deny()
            user_perms = {p.code for p in user.role.permissions}
            if not user_perms.intersection(permission_codes):
                return _deny()
            return f(*args, **kwargs)

        def _deny():
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": {"code": "FORBIDDEN",
                                                              "message": "Missing permission"}}), 403
            flash("You do not have permission to perform that action.", "danger")
            return redirect(request.referrer or url_for("public.home"))
        return wrapper
    return decorator
