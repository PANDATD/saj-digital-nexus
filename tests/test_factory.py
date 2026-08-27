from __future__ import annotations

import pytest

from saj_nexus import create_app


def test_deployed_app_requires_secret(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({"TESTING": True, "SECRET_KEY": "dev-only-change-before-production"})
