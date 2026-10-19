from __future__ import annotations

import jwt
import pytest

from app.core.config import Settings, get_settings, validate_production_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_station_token,
    try_decode_access_token,
    verify_password,
    verify_station_token,
)


def test_access_token_roundtrip() -> None:
    claims = decode_access_token(create_access_token("user-id", "admin"))
    assert claims["sub"] == "user-id"
    assert claims["role"] == "admin"
    assert claims["iss"] == get_settings().jwt_issuer
    assert claims["aud"] == get_settings().jwt_audience


@pytest.mark.parametrize("invalid_claim", ["exp", "iss", "aud"])
def test_access_token_rejects_invalid_claims(invalid_claim: str) -> None:
    settings = get_settings()
    claims = decode_access_token(create_access_token("user-id", "admin"))
    claims[invalid_claim] = 0 if invalid_claim == "exp" else "untrusted"
    token = jwt.encode(claims, settings.jwt_secret, algorithm="HS256")
    assert try_decode_access_token(token) is None


def test_access_token_rejects_wrong_signature_and_algorithm() -> None:
    claims = decode_access_token(create_access_token("user-id", "admin"))
    assert try_decode_access_token(jwt.encode(claims, "wrong-key", algorithm="HS256")) is None
    assert try_decode_access_token(jwt.encode(claims, get_settings().jwt_secret, algorithm="HS512")) is None
    assert try_decode_access_token(jwt.encode(claims, "", algorithm="none")) is None
    assert try_decode_access_token("not-a-token") is None


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_station_token_hash_roundtrip() -> None:
    token = "station-token-with-at-least-32-characters"
    hashed = hash_station_token(token)

    assert hashed != token
    assert verify_station_token(token, hashed)
    assert not verify_station_token("wrong-token", hashed)
    assert not verify_station_token(token, None)


def test_production_rejects_default_or_short_secrets() -> None:
    with pytest.raises(RuntimeError, match="JWT_SECRET.*PARTNER_WEBHOOK_SECRET"):
        validate_production_settings(
            Settings(
                app_env="production",
                jwt_secret="change-me",
                partner_webhook_secret="short",
            )
        )


def test_production_accepts_strong_secrets() -> None:
    validate_production_settings(
        Settings(
            app_env="production",
            jwt_secret="j" * 32,
            partner_webhook_secret="w" * 32,
        )
    )
