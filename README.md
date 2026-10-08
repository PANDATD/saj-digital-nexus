# SAJ Digital Nexus

A Flask website project for SAJ Digital Nexus.

## Stack

- Python
- Flask
- Jinja templates
- Bootstrap
- Custom CSS and JavaScript
- uv
- Pytest
- Ruff
- Gunicorn
- Vercel configuration

## Structure

```text
.
├── app.py
├── public/
├── src/saj_nexus/
│   ├── __init__.py
│   ├── config.py
│   ├── content.py
│   ├── forms.py
│   ├── routes.py
│   ├── seo.py
│   └── templates/
├── tests/
├── pyproject.toml
└── vercel.json
```

## Local development

```bash
uv sync --all-groups
cp .env.example .env
uv run flask --app app run --debug
```

Set the environment variables required by the application before running features that depend on them. Never commit .env or credentials.

## Checks

```bash
uv run ruff check .
uv run pytest
```

The repository contains deployment and SEO-related configuration, but this README does not make claims about production readiness or business results.

## Project work

Tejas Dixit — https://tejasdixit.in
