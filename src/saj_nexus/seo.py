from __future__ import annotations

from urllib.parse import urljoin

from flask import current_app, request

from .content import BRAND_NAME, BRAND_SUMMARY


def site_origin() -> str:
    configured = current_app.config.get("SITE_URL", "")
    if configured:
        return configured.rstrip("/")
    return request.url_root.rstrip("/")


def absolute_url(path: str) -> str:
    return urljoin(f"{site_origin()}/", path.lstrip("/"))


def canonical_url() -> str:
    return absolute_url(request.path)


def organization_schema() -> dict:
    schema: dict = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{site_origin()}/#organization",
        "name": BRAND_NAME,
        "url": site_origin(),
        "logo": absolute_url("/assets/images/saj-logo.webp"),
        "image": absolute_url("/assets/images/og-card.jpg"),
        "description": BRAND_SUMMARY,
        "knowsAbout": [
            "Script Writing",
            "Speech Writing",
            "Video Editing",
            "Motion Graphics",
            "Graphic Design",
            "Digital Marketing",
            "Digital Public Relations",
            "Podcast Production",
            "Search Engine Optimisation",
            "Web Development",
            "AI Automation",
            "Curated Research",
        ],
    }
    email = current_app.config.get("CONTACT_EMAIL")
    phone = current_app.config.get("BRAND_PHONE")
    location = current_app.config.get("BRAND_LOCATION")
    if email:
        schema["email"] = email
    if phone:
        schema["telephone"] = phone
    if location:
        schema["areaServed"] = location
    return schema


def website_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": f"{site_origin()}/#website",
        "url": site_origin(),
        "name": BRAND_NAME,
        "description": BRAND_SUMMARY,
        "publisher": {"@id": f"{site_origin()}/#organization"},
        "inLanguage": "en-IN",
    }
