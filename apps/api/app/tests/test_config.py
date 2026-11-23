# app/tests/test_config.py
import pytest
from pydantic import ValidationError

from app.core.config import _DEFAULT_SECRET_KEY, Settings


def test_production_rejects_default_secret_key():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY=_DEFAULT_SECRET_KEY,
        )


def test_production_rejects_short_secret_key():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="short",
        )


def test_production_accepts_strong_secret_key():
    cfg = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        SECRET_KEY="x" * 32,
    )
    assert cfg.ENVIRONMENT == "production"
    assert cfg.SECRET_KEY == "x" * 32


def test_development_allows_default_secret_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    cfg = Settings(
        _env_file=None,
        ENVIRONMENT="development",
    )
    assert cfg.ENVIRONMENT == "development"
    assert cfg.SECRET_KEY == _DEFAULT_SECRET_KEY
