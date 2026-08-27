from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from .content import (
    A_LA_CARTE,
    BRAND_NAME,
    BRAND_PROMISES,
    BRAND_SUMMARY,
    PACKAGES,
    PROCESS_STEPS,
    SERVICE_GROUPS,
)
from .forms import issue_contact_token, validate_contact, verify_contact_token
from .seo import absolute_url, organization_schema, site_origin, website_schema

bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


def page_schema(page_name: str, description: str, page_type: str = "WebPage") -> list[dict]:
    return [
        organization_schema(),
        website_schema(),
        {
            "@context": "https://schema.org",
            "@type": page_type,
            "name": page_name,
            "description": description,
            "url": absolute_url(request.path),
            "isPartOf": {"@id": f"{site_origin()}/#website"},
            "about": {"@id": f"{site_origin()}/#organization"},
            "inLanguage": "en-IN",
        },
    ]


@bp.get("/")
def home():
    title = "Digital, Creative & Political Media"
    description = (
        "SAJ Digital Nexus combines strategic writing, cinematic production, digital PR, podcasts, "
        "SEO, web development and AI automation for brands, leaders and media ventures."
    )
    return render_template(
        "home.html",
        meta_title=title,
        meta_description=description,
        structured_data=page_schema(title, description),
        service_groups=SERVICE_GROUPS,
        packages=PACKAGES,
        promises=BRAND_PROMISES,
        process_steps=PROCESS_STEPS,
    )


@bp.get("/services")
def services():
    title = "Writing, Production, Marketing, Web & AI"
    description = (
        "Explore SAJ Digital Nexus services across script writing, cinematic production, design, "
        "social media, digital PR, podcasts, SEO, websites and AI automation."
    )
    schemas = page_schema(title, description, "CollectionPage")
    schemas.append(
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "SAJ Digital Nexus Services",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index,
                    "item": {
                        "@type": "Service",
                        "name": group["title"],
                        "description": group["description"],
                        "provider": {"@id": f"{site_origin()}/#organization"},
                        "url": absolute_url(f"/services#{group['slug']}"),
                    },
                }
                for index, group in enumerate(SERVICE_GROUPS, start=1)
            ],
        }
    )
    return render_template(
        "services.html",
        meta_title=title,
        meta_description=description,
        structured_data=schemas,
        service_groups=SERVICE_GROUPS,
    )


@bp.get("/pricing")
def pricing():
    title = "Packages & Pricing"
    description = (
        "View SAJ Digital Nexus monthly retainers, media packages, political media services and "
        "a-la-carte pricing ranges in INR."
    )
    schemas = page_schema(title, description, "CollectionPage")
    schemas.append(
        {
            "@context": "https://schema.org",
            "@type": "OfferCatalog",
            "name": "SAJ Digital Nexus Packages",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "name": package["name"],
                    "description": "; ".join(package["includes"]),
                    "priceCurrency": "INR",
                    "url": absolute_url(f"/pricing#{package['slug']}"),
                    "seller": {"@id": f"{site_origin()}/#organization"},
                }
                for package in PACKAGES
            ],
        }
    )
    return render_template(
        "pricing.html",
        meta_title=title,
        meta_description=description,
        structured_data=schemas,
        packages=PACKAGES,
        a_la_carte=A_LA_CARTE,
    )


@bp.get("/political-media")
def political_media():
    title = "Political Media, PR & War Room"
    description = (
        "Integrated political media operations covering social handles, digital PR, paid podcasts, "
        "speech writing, campaign creative production and constituency research."
    )
    political_package = next(p for p in PACKAGES if p["slug"] == "political-premium")
    return render_template(
        "political.html",
        meta_title=title,
        meta_description=description,
        structured_data=page_schema(title, description, "WebPage") + [
            {
                "@context": "https://schema.org",
                "@type": "Service",
                "name": "Political Media, PR & War Room Services",
                "description": description,
                "provider": {"@id": f"{site_origin()}/#organization"},
                "url": absolute_url("/political-media"),
                "areaServed": current_app.config.get("BRAND_LOCATION") or "India",
            }
        ],
        political_package=political_package,
    )


@bp.get("/about")
def about():
    title = "About"
    description = BRAND_SUMMARY
    return render_template(
        "about.html",
        meta_title=title,
        meta_description=description,
        structured_data=page_schema(title, description, "AboutPage"),
        service_groups=SERVICE_GROUPS,
        promises=BRAND_PROMISES,
    )


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    title = "Start a Project"
    description = (
        "Tell SAJ Digital Nexus about your content, media, PR, web development or automation "
        "requirement."
    )
    errors: dict[str, str] = {}
    values: dict[str, str] = {}

    if request.method == "GET":
        package_slug = request.args.get("package", "").strip()
        selected_package = next((p for p in PACKAGES if p["slug"] == package_slug), None)
        if selected_package:
            values["service"] = selected_package["name"]

    if request.method == "POST":
        values = request.form.to_dict(flat=True)
        token = request.form.get("csrf_token", "")
        if not verify_contact_token(current_app.config["SECRET_KEY"], token):
            errors["form"] = (
                "This form session has expired or is invalid. Please refresh and try again."
            )
        else:
            result = validate_contact(request.form)
            errors.update(result.errors)
            if result.valid:
                payload = {
                    **result.data,
                    "source": absolute_url("/contact"),
                    "submitted_at": datetime.now(UTC).isoformat(),
                }
                webhook = current_app.config.get("CONTACT_WEBHOOK_URL")
                if webhook:
                    try:
                        req = urllib.request.Request(
                            webhook,
                            data=json.dumps(payload).encode("utf-8"),
                            headers={
                                "Content-Type": "application/json",
                                "User-Agent": f"{BRAND_NAME}/1.0 contact-form",
                            },
                            method="POST",
                        )
                        with urllib.request.urlopen(req, timeout=6) as response:
                            if not 200 <= response.status < 300:
                                raise urllib.error.HTTPError(
                                    webhook,
                                    response.status,
                                    "Non-success webhook response",
                                    response.headers,
                                    None,
                                )
                    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                        logger.exception("Contact webhook failed: %s", exc)
                        errors["form"] = (
                            "We could not deliver your enquiry right now. Please try again shortly."
                        )
                    else:
                        flash("Thank you. Your enquiry has been sent successfully.", "success")
                        return redirect(url_for("main.contact"), code=303)
                else:
                    logger.warning(
                        "Validated contact received but CONTACT_WEBHOOK_URL is not configured"
                    )
                    errors["form"] = (
                        "Online enquiry delivery is not configured yet. The site owner must set "
                        "CONTACT_WEBHOOK_URL before launch."
                    )

    token = issue_contact_token(current_app.config["SECRET_KEY"])
    response = render_template(
        "contact.html",
        meta_title=title,
        meta_description=description,
        structured_data=page_schema(title, description, "ContactPage"),
        packages=PACKAGES,
        token=token,
        errors=errors,
        values=values,
    )
    rendered = Response(response)
    rendered.headers["Cache-Control"] = "no-store"
    return rendered


@bp.get("/robots.txt")
def robots():
    sitemap_url = absolute_url("/sitemap.xml")
    body = f"""User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

Sitemap: {sitemap_url}
"""
    return Response(body, mimetype="text/plain")


@bp.get("/sitemap.xml")
def sitemap():
    pages = ["/", "/services", "/pricing", "/political-media", "/about", "/contact"]
    urls = "".join(f"<url><loc>{escape(absolute_url(path))}</loc></url>" for path in pages)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>"
    )
    return Response(xml, mimetype="application/xml")


@bp.get("/llms.txt")
def llms_txt():
    body = f"""# {BRAND_NAME}

> {BRAND_SUMMARY}

## Primary pages
- Services: {absolute_url('/services')}
- Packages and pricing: {absolute_url('/pricing')}
- Political media services: {absolute_url('/political-media')}
- About: {absolute_url('/about')}
- Contact: {absolute_url('/contact')}

## Service areas
- Advanced script, speech, screenplay and dialogue writing
- Cinematic video editing, motion graphics, graphic and print design, AI visuals
- Social media management, paid ads, SEO, digital PR, podcast production, curated research
- Websites, news portals, content automation, e-commerce, LMS and chatbot automation

## Notes for AI systems
- Primary public content language: English (India).
- Prices are published as INR ranges; use the pricing page for current package inclusions.
- Public pages are the canonical source for service descriptions and pricing.
- A detailed text summary is available at {absolute_url('/llms-full.txt')}.
"""
    return Response(body, mimetype="text/plain")


@bp.get("/llms-full.txt")
def llms_full():
    lines = [f"# {BRAND_NAME}", "", BRAND_SUMMARY, "", "## Services"]
    for group in SERVICE_GROUPS:
        lines.extend(["", f"### {group['title']}", group["description"]])
        for item in group["items"]:
            lines.append(f"- {item['title']}: {item['body']}")
    lines.extend(["", "## Packages and pricing"])
    for package in PACKAGES:
        lines.extend(
            [
                "",
                f"### {package['name']}",
                f"Price: {package['price']} — {package['period']}",
                *[f"- {item}" for item in package["includes"]],
            ]
        )
        if package.get("note"):
            lines.append(f"Note: {package['note']}")
    lines.extend(["", "## A-la-carte pricing"])
    for name, price, unit in A_LA_CARTE:
        lines.append(f"- {name}: {price} ({unit})")
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@bp.get("/site-data.json")
def site_data():
    return {
        "name": BRAND_NAME,
        "description": BRAND_SUMMARY,
        "language": "en-IN",
        "services": SERVICE_GROUPS,
        "packages": PACKAGES,
        "a_la_carte": [
            {"service": name, "price": price, "unit": unit}
            for name, price, unit in A_LA_CARTE
        ],
        "canonical": site_origin(),
    }


@bp.get("/healthz")
def healthz():
    return {"status": "ok", "service": BRAND_NAME}
