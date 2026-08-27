from __future__ import annotations

import logging
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path

from flask import Flask, g, render_template, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .content import BRAND_NAME, BRAND_TAGLINE
from .routes import bp
from .seo import absolute_url, canonical_url


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False, static_folder=None)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    app.register_blueprint(bp)

    configure_logging(app)
    register_asset_routes(app)
    register_template_context(app)
    register_csp_nonce(app)
    register_security_headers(app)
    register_error_handlers(app)

    is_deployed = bool(os.getenv("VERCEL")) or os.getenv("FLASK_ENV") == "production"
    if is_deployed and app.config["SECRET_KEY"] == "dev-only-change-before-production":
        raise RuntimeError("SECRET_KEY must be configured for deployed environments")
    if is_deployed and not app.config.get("SITE_URL"):
        app.logger.warning("SITE_URL is not configured; canonical URLs will use the request host")

    return app


def configure_logging(app: Flask) -> None:
    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO)


def register_asset_routes(app: Flask) -> None:
    public_dir = Path(app.config["PUBLIC_DIR"])

    @app.get("/assets/<path:filename>")
    def public_asset(filename: str):
        return send_from_directory(public_dir / "assets", filename, max_age=31536000)

    @app.get("/manifest.webmanifest")
    def manifest():
        return send_from_directory(
            public_dir,
            "manifest.webmanifest",
            mimetype="application/manifest+json",
            max_age=86400,
        )

    @app.get("/favicon.ico")
    def favicon():
        return send_from_directory(
            public_dir / "assets" / "images", "favicon.ico", max_age=31536000
        )


def register_template_context(app: Flask) -> None:
    @app.context_processor
    def inject_site_context():
        return {
            "brand_name": BRAND_NAME,
            "brand_tagline": BRAND_TAGLINE,
            "canonical_url": canonical_url(),
            "site_origin": absolute_url("/").rstrip("/"),
            "og_image_url": absolute_url("/assets/images/og-card.jpg"),
            "contact_email": app.config.get("CONTACT_EMAIL", ""),
            "brand_phone": app.config.get("BRAND_PHONE", ""),
            "brand_location": app.config.get("BRAND_LOCATION", ""),
            "current_path": request.path,
            "current_year": datetime.now(UTC).year,
            "csp_nonce": getattr(g, "csp_nonce", ""),
        }


def register_csp_nonce(app: Flask) -> None:
    @app.before_request
    def set_csp_nonce() -> None:
        g.csp_nonce = secrets.token_urlsafe(18)


def register_security_headers(app: Flask) -> None:
    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
            "img-src 'self' data:; "
            "style-src 'self' https://cdn.jsdelivr.net; "
            f"script-src 'self' 'nonce-{g.csp_nonce}' https://cdn.jsdelivr.net; "
            "font-src 'self'; connect-src 'self'; object-src 'none'", 
        )
        if request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload"
            )
        if response.status_code >= 400:
            response.headers.setdefault("X-Robots-Tag", "noindex, nofollow")
        is_cacheable_html = (
            response.mimetype == "text/html"
            and response.status_code == 200
            and request.path != "/contact"
        )
        if is_cacheable_html:
            response.headers.setdefault(
                "Cache-Control", "public, max-age=0, s-maxage=300, stale-while-revalidate=86400"
            )
        return response


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_error):
        return (
            render_template(
                "error.html",
                code=404,
                meta_title="Page Not Found",
                meta_description="The requested page could not be found.",
                structured_data=[],
                meta_robots="noindex,nofollow",
            ),
            404,
        )

    @app.errorhandler(500)
    def server_error(_error):
        return (
            render_template(
                "error.html",
                code=500,
                meta_title="Server Error",
                meta_description="The site encountered an unexpected error.",
                structured_data=[],
                meta_robots="noindex,nofollow",
            ),
            500,
        )
