"""Shared pytest fixtures for the YugKrit test suite.

Each test gets a fully isolated, file-based SQLite database (created in a
temp directory and destroyed afterwards) so that tests never leak data into
one another, regardless of how SQLAlchemy pools in-memory connections.
"""

import os
import sys
import uuid
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.database import db
from database.seed import seed_roles_and_permissions, seed_categories


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    flask_app = create_app()
    flask_app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    with flask_app.app_context():
        db.create_all()
        seed_roles_and_permissions()
        seed_categories()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
