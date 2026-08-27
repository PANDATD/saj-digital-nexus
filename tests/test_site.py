from __future__ import annotations

import json
import re

import pytest

from saj_nexus.forms import issue_contact_token, validate_contact


@pytest.mark.parametrize(
    ("path", "needle"),
    [
        ("/", "Ideas engineered for attention"),
        ("/services", "Advanced Writing, Scripts & Narrative"),
        ("/pricing", "₹28,000 – ₹35,000"),
        ("/political-media", "A disciplined media operation"),
        ("/about", "A modern media studio"),
        ("/contact", "Tell us what you are building"),
    ],
)
def test_public_pages_render(client, path, needle):
    response = client.get(path)
    assert response.status_code == 200
    assert needle.encode() in response.data
    assert b'<html lang="en-IN">' in response.data
    assert b'<meta name="description"' in response.data
    assert b'<link rel="canonical"' in response.data


def test_service_groups_render_child_services(client):
    """Regression: dict key `items` must not resolve to dict.items in Jinja."""
    services = client.get("/services")
    assert services.status_code == 200
    assert (
        b"Reels, Shorts &amp; Advertising Scripts" in services.data
        or b"Reels, Shorts & Advertising Scripts" in services.data
    )
    assert (
        b"E-commerce, LMS &amp; Chatbot Automation" in services.data
        or b"E-commerce, LMS & Chatbot Automation" in services.data
    )

    about = client.get("/about")
    assert about.status_code == 200
    assert b"4 capabilities" in about.data
    assert b"6 capabilities" in about.data
    assert b"3 capabilities" in about.data


def test_assets_are_served_locally(client):
    response = client.get("/assets/css/site.css")
    assert response.status_code == 200
    assert response.mimetype == "text/css"
    assert b"--saj-bg" in response.data


def test_machine_readable_endpoints(client):
    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert b"OAI-SearchBot" in robots.data
    assert b"https://saj.example/sitemap.xml" in robots.data

    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert b"https://saj.example/services" in sitemap.data

    llms = client.get("/llms.txt")
    assert llms.status_code == 200
    assert b"Primary public content language: English (India)." in llms.data

    site_data = client.get("/site-data.json")
    assert site_data.status_code == 200
    payload = site_data.get_json()
    assert payload["language"] == "en-IN"
    assert len(payload["services"]) == 4
    assert len(payload["packages"]) == 4


def test_json_ld_is_valid_json(client):
    response = client.get("/services")
    html = response.get_data(as_text=True)
    blocks = re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    assert blocks
    for block in blocks:
        json.loads(block)


def test_security_headers(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert "cdn.jsdelivr.net" in response.headers["Content-Security-Policy"]


def test_contact_get_is_not_cached_and_can_preselect_package(client):
    response = client.get("/contact?package=enterprise-content-hub")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    html = response.get_data(as_text=True)
    assert "csrf_token" in html
    assert (
        '<option value="Premium YouTube, Podcast &amp; Brand Hub" selected>' in html
        or '<option value="Premium YouTube, Podcast & Brand Hub" selected>' in html
    )


def test_contact_validation_rejects_invalid_submission(client, app):
    token = issue_contact_token(app.config["SECRET_KEY"])
    response = client.post(
        "/contact",
        data={
            "csrf_token": token,
            "name": "A",
            "email": "not-an-email",
            "message": "short",
            "website": "",
        },
    )
    assert response.status_code == 200
    assert b"Please enter your name." in response.data
    assert b"Please enter a valid email address." in response.data
    assert b"Please share a little more detail" in response.data


def test_contact_honeypot_is_rejected():
    result = validate_contact(
        {
            "name": "Example Person",
            "email": "person@example.com",
            "message": "This is a sufficiently detailed enquiry for testing.",
            "website": "https://spam.invalid",
        }
    )
    assert not result.valid
    assert result.errors["form"]


def test_404_is_branded(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert b"Page Not Found" in response.data
    assert response.headers["X-Robots-Tag"] == "noindex, nofollow"
    assert b'content="noindex,nofollow"' in response.data


def test_static_metadata_and_health_endpoints(client):
    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    assert manifest.mimetype == "application/manifest+json"

    favicon = client.get("/favicon.ico")
    assert favicon.status_code == 200
    assert favicon.mimetype in {"image/vnd.microsoft.icon", "image/x-icon"}

    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.get_json()["status"] == "ok"

    full = client.get("/llms-full.txt")
    assert full.status_code == 200
    assert b"Leadership PR, Paid Podcast & War Room Management" in full.data


def test_https_response_gets_hsts(client):
    response = client.get("/", base_url="https://saj.example")
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]


def test_valid_contact_without_webhook_shows_configuration_message(client, app):
    token = issue_contact_token(app.config["SECRET_KEY"])
    response = client.post(
        "/contact",
        data={
            "csrf_token": token,
            "name": "Example Person",
            "email": "person@example.com",
            "message": "We need an integrated media project for a new launch campaign.",
            "website": "",
        },
    )
    assert response.status_code == 200
    assert b"Online enquiry delivery is not configured yet" in response.data


def test_contact_webhook_success_redirects(client, app, monkeypatch):
    captured = {}

    class StubResponse:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return StubResponse()

    monkeypatch.setattr("saj_nexus.routes.urllib.request.urlopen", fake_urlopen)
    app.config["CONTACT_WEBHOOK_URL"] = "https://webhook.example/intake"
    token = issue_contact_token(app.config["SECRET_KEY"])
    response = client.post(
        "/contact",
        data={
            "csrf_token": token,
            "name": "Example Person",
            "organization": "Example Organisation",
            "email": "PERSON@example.com",
            "message": "We need a production and distribution scope for a podcast series.",
            "website": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["Location"].endswith("/contact")
    assert captured["timeout"] == 6
    body = json.loads(captured["request"].data)
    assert body["email"] == "person@example.com"
    assert body["source"] == "https://saj.example/contact"


def test_csrf_token_verification_and_cleaning(app):
    from saj_nexus.forms import clean, verify_contact_token

    token = issue_contact_token(app.config["SECRET_KEY"])
    assert verify_contact_token(app.config["SECRET_KEY"], token)
    assert not verify_contact_token(app.config["SECRET_KEY"], token + "tampered")
    assert not verify_contact_token(app.config["SECRET_KEY"], "")
    assert clean("  multiple   spaces  ", 50) == "multiple spaces"
