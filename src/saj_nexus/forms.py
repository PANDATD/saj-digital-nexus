from __future__ import annotations

import re
from dataclasses import dataclass

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(slots=True)
class ContactResult:
    data: dict[str, str]
    errors: dict[str, str]

    @property
    def valid(self) -> bool:
        return not self.errors


def issue_contact_token(secret_key: str) -> str:
    serializer = URLSafeTimedSerializer(secret_key, salt="contact-form-v1")
    return serializer.dumps({"scope": "contact"})


def verify_contact_token(secret_key: str, token: str) -> bool:
    if not token:
        return False
    serializer = URLSafeTimedSerializer(secret_key, salt="contact-form-v1")
    try:
        payload = serializer.loads(token, max_age=3600)
    except (BadSignature, SignatureExpired):
        return False
    return payload.get("scope") == "contact"


def clean(value: str, limit: int) -> str:
    return " ".join(value.strip().split())[:limit]


def validate_contact(form) -> ContactResult:
    data = {
        "name": clean(form.get("name", ""), 100),
        "organization": clean(form.get("organization", ""), 120),
        "email": clean(form.get("email", ""), 180).lower(),
        "phone": clean(form.get("phone", ""), 40),
        "service": clean(form.get("service", ""), 140),
        "budget": clean(form.get("budget", ""), 80),
        "message": form.get("message", "").strip()[:2000],
        "website": clean(form.get("website", ""), 200),
    }
    errors: dict[str, str] = {}

    if data["website"]:
        errors["form"] = "Submission rejected."
    if len(data["name"]) < 2:
        errors["name"] = "Please enter your name."
    if not EMAIL_RE.match(data["email"]):
        errors["email"] = "Please enter a valid email address."
    if len(data["message"]) < 12:
        errors["message"] = "Please share a little more detail about your project."

    data.pop("website", None)
    return ContactResult(data=data, errors=errors)
