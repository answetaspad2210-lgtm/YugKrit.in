"""YugKrit - Public certificate verification routes."""

from flask import Blueprint, render_template
from services.certificate_service import get_certificate_by_public_id

certificate_bp = Blueprint("certificate", __name__, template_folder="../templates/public")


@certificate_bp.route("/certificate/<certificate_id>")
def verify_certificate(certificate_id):
    cert = get_certificate_by_public_id(certificate_id)
    return render_template("public/certificate_verify.html", cert=cert, certificate_id=certificate_id)
