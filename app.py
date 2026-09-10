"""
YugKrit - Application entry point.

Run:
    python app.py

The app factory pattern (`create_app`) makes it trivial to register new
dashboards later: just add a new blueprint in routes/ and register it here.
"""

import os
from flask import Flask, render_template, session
from dotenv import load_dotenv

load_dotenv()

from config import config_by_name
from database.database import db, init_db, ensure_rbac, ensure_challenge_categories
import database.models  # noqa: F401 - register all tables before db.create_all()
from utils.decorators import get_current_user
from services.notification_service import unread_count
from services import otp_service


def create_app(config_name=None):
    app = Flask(__name__)
    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    init_db(app)
    with app.app_context():
        ensure_rbac()
        ensure_challenge_categories()

    # --- Register blueprints ---
    from routes.public_routes import public_bp
    from routes.auth_routes import auth_bp
    from routes.government_routes import government_bp
    from routes.itcell_routes import itcell_bp
    from routes.university_routes import university_bp
    from routes.ulb_routes import ulb_bp
    from routes.student_routes import student_bp
    from routes.citizen_routes import citizen_bp
    from routes.certificate_routes import certificate_bp
    from routes.api_routes import api_bp
    from routes.notification_routes import notification_bp
    from routes.industry_routes import industry_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(government_bp, url_prefix="/dashboard/government")
    app.register_blueprint(itcell_bp, url_prefix="/dashboard/it-cell")
    app.register_blueprint(university_bp, url_prefix="/dashboard/university")
    app.register_blueprint(ulb_bp, url_prefix="/dashboard/ulb")
    app.register_blueprint(student_bp, url_prefix="/dashboard/student")
    app.register_blueprint(citizen_bp, url_prefix="/dashboard/citizen")
    app.register_blueprint(certificate_bp, url_prefix="/verify")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(notification_bp, url_prefix="/notifications")
    app.register_blueprint(industry_bp, url_prefix="/industry")

    # --- Template globals (available in every Jinja template) ---
    @app.context_processor
    def inject_globals():
        user = get_current_user()
        return {
            "current_user": user,
            "app_name": app.config["APP_NAME"],
            "app_tagline": app.config["APP_TAGLINE"],
            "unread_notifications": unread_count(user) if user else 0,
            "otp_dev_mode": otp_service.DEV_MODE,
        }

    # --- Error handlers (never leak stack traces) ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template("shared/error.html", code=404,
                                message="Page not found."), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("shared/error.html", code=403,
                                message="You don't have permission to view this page."), 403

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("shared/error.html", code=500,
                                message="Something went wrong on our end."), 500

    return app


app = create_app()

if __name__ == "__main__":
    ssl_context = "adhoc" if os.environ.get("FLASK_HTTPS", "0") == "1" else None
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"], ssl_context=ssl_context)
