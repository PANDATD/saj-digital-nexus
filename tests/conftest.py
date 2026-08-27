from __future__ import annotations

import pytest

from saj_nexus import create_app


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-that-is-not-used-in-production",
            "SITE_URL": "https://saj.example",
            "CONTACT_WEBHOOK_URL": "",
            "CONTACT_EMAIL": "hello@saj.example",
            "BRAND_LOCATION": "India",
        }
    )
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()
