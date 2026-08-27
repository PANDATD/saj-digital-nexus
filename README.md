# SAJ Digital Nexus — Production Flask Website

A premium, English-first agency website for **SAJ Digital Nexus**, built from the supplied service and pricing brief. The site is server-rendered, mobile-first, SEO-friendly, AI-readable, Git-ready and designed for direct deployment to Vercel.

## Technology

- Python 3.12–3.14; local project pin: Python 3.13
- Flask 3.1.3 with the application-factory and Blueprint patterns
- Bootstrap 5.3.8 from the official jsDelivr build with Subresource Integrity (SRI)
- Custom responsive CSS and lightweight progressive JavaScript
- uv for environment, dependency and lockfile management
- Gunicorn 26.1.0 for conventional WSGI production hosting
- python-dotenv 1.2.3 for local `.env` loading
- Pytest, pytest-cov and Ruff for automated quality checks
- GitHub Actions CI across Python 3.12, 3.13 and 3.14
- Vercel Flask/WSGI deployment with `public/` CDN assets

## Architecture

```text
.
├── app.py                         # Vercel / WSGI entry point
├── pyproject.toml                 # uv + project configuration
├── vercel.json                    # static caching + function exclusions
├── public/                        # CDN-ready static assets
├── src/saj_nexus/
│   ├── __init__.py                # create_app() and platform hooks
│   ├── config.py                  # environment-driven settings
│   ├── content.py                 # canonical English service/pricing data
│   ├── forms.py                   # validation + signed CSRF token
│   ├── routes.py                  # pages + crawler/AI endpoints
│   ├── seo.py                     # canonical URLs + JSON-LD helpers
│   └── templates/                 # semantic Jinja templates
└── tests/                         # route, SEO, security and form tests
```

## Local development with uv

```bash
uv sync --all-groups
cp .env.example .env
uv run flask --app app run --debug
```

Open `http://127.0.0.1:5000`. Because `python-dotenv` is installed, Flask loads local values from `.env` automatically.

For production-like WSGI serving outside Vercel:

```bash
uv run gunicorn --bind 0.0.0.0:8000 app:app
```

### Lockfile

`uv sync` generates `uv.lock`. **Commit `uv.lock` to Git** after the first successful dependency resolution so CI and deployments can use the same resolved dependency graph. Registry access is disabled in the environment that generated this bundle, so a trustworthy lockfile could not be created here rather than fabricating one.

## Environment variables

Copy `.env.example` and set:

- `SECRET_KEY` — required production secret; use a long random value.
- `SITE_URL` — canonical production origin, for example `https://example.com`.
- `CONTACT_WEBHOOK_URL` — optional private endpoint receiving validated enquiry JSON.
- `CONTACT_EMAIL` — optional public contact email.
- `BRAND_PHONE` — optional public phone number.
- `BRAND_LOCATION` — optional service area; defaults to India in the sample configuration.

Never commit `.env`.

## Quality checks

```bash
uv run ruff check .
uv run pytest --cov --cov-report=term-missing --cov-fail-under=85
```

The test suite covers public pages, canonical/SEO markup, JSON-LD validity, crawler endpoints, security headers, static assets, contact validation, CSRF-backed form rendering and 404 behaviour.

## SEO, AI and accessibility

The site includes semantic server-rendered HTML, one clear page-level heading, canonical URLs, descriptive metadata, Open Graph and Twitter cards, Organization/WebSite/Service JSON-LD, `sitemap.xml`, crawler-aware `robots.txt`, `llms.txt`, `llms-full.txt`, and a structured `/site-data.json` representation of public services and pricing. It also includes a skip link, keyboard-visible controls, reduced-motion support and responsive layouts from small phones through large screens.

## Security and performance

Security headers include Content Security Policy, anti-framing, MIME sniffing protection, restrictive permissions policy, referrer policy, COOP and HTTPS HSTS when the request is secure. The contact form uses a signed one-hour CSRF token, server-side validation, a honeypot field, a 32 KB request limit and no local lead persistence. Static assets are long-cacheable; content pages are short CDN-cacheable while `/contact` is explicitly `no-store`.

## Deploy to Vercel

Vercel officially detects a top-level Flask `app` in `app.py`, and this repository exposes exactly that while the real application is created by `create_app()`. Static files live under `public/` for Vercel CDN delivery.

1. Run `uv sync --all-groups`, then commit the generated `uv.lock`.
2. Push the repository to GitHub, GitLab or Bitbucket.
3. Import the repository into Vercel, or run `vercel` from the project root.
4. Add `SECRET_KEY`, `SITE_URL` and any contact variables in Vercel Environment Variables.
5. Deploy a Preview, verify the contact destination and metadata, then promote to Production.

No build command or output directory is required for the Flask deployment.

## Content source

The original supplied brief is preserved at `docs/source/Document.txt`. Public copy is a polished English adaptation of its service categories, package inclusions and INR pricing. Internal profit-margin commentary from the pitch brief is intentionally not exposed on the client-facing website.

The supplied SAJ monogram is preserved as `public/assets/images/saj-monogram-source.png`; optimized web, favicon, app-icon and social-card derivatives are included alongside it.

## Pre-launch checklist

- Generate and commit `uv.lock`.
- Set the official domain in `SITE_URL`.
- Replace sample contact details and configure the private webhook if the form will be used.
- Review commercial wording, taxes, invoices, privacy obligations and any contractual guarantees with the business owner.
- Run CI and test the Vercel Preview on real mobile devices before production DNS cutover.
