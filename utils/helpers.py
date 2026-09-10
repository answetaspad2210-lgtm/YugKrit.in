"""YugKrit - Misc helper functions."""

import os
import uuid
import secrets
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def save_uploaded_file(file_storage, subfolder="misc"):
    """Save an uploaded file safely and return (file_name, file_path, file_size)."""
    if not file_storage or file_storage.filename == "":
        return None, None, None
    if not allowed_file(file_storage.filename):
        raise ValueError("File type not allowed.")

    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(folder, exist_ok=True)
    full_path = os.path.join(folder, unique_name)
    file_storage.save(full_path)

    size = os.path.getsize(full_path)
    relative_path = f"uploads/{subfolder}/{unique_name}"
    return original, relative_path, size


def generate_code(prefix):
    """e.g. generate_code('YK') -> 'YK-2026-4F3A9C'."""
    year = datetime.utcnow().year
    token = secrets.token_hex(3).upper()
    return f"{prefix}-{year}-{token}"


def api_success(data=None, message=None, status=200):
    from flask import jsonify
    payload = {"success": True}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def api_error(message, code="ERROR", status=400):
    from flask import jsonify
    return jsonify({"success": False, "error": {"code": code, "message": message}}), status
