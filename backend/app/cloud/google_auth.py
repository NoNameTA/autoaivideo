"""Mint Google access token từ Service Account (SPEC 06 §9.2, 11 §3.2).

Backend ký JWT RS256 (bằng `cryptography`) + đổi lấy access token ngắn hạn qua token endpoint
(`httpx`). KHÔNG thêm dependency ngoài phạm vi D3. Token này (không phải JSON key gốc) là thứ
DUY NHẤT cấp xuống Agent (SPEC 11 §3.3).
"""
from __future__ import annotations

import base64
import json
import time

import httpx

from app.secrets.provider import SecretError

_GRANT = "urn:ietf:params:oauth:grant-type:jwt-bearer"
_DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"
_TOKEN_TTL = 3600


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _sign_rs256(private_key_pem: str, signing_input: bytes) -> bytes:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
    return key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())  # type: ignore[union-attr]


async def mint_service_account_token(sa_json: str, scopes: list[str]) -> tuple[str, int]:
    """Trả (access_token, expires_at_epoch). `sa_json` = nội dung Service Account JSON.

    Lỗi cấu hình/khoá -> SecretError (Permanent). Không log nội dung khoá.
    """
    try:
        sa = json.loads(sa_json)
    except json.JSONDecodeError:
        raise SecretError("Service Account JSON không hợp lệ") from None

    client_email = sa.get("client_email")
    private_key = sa.get("private_key")
    token_uri = sa.get("token_uri") or _DEFAULT_TOKEN_URI
    if not client_email or not private_key:
        raise SecretError("Service Account thiếu client_email/private_key") from None

    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    claims = {
        "iss": client_email,
        "scope": " ".join(scopes),
        "aud": token_uri,
        "iat": now,
        "exp": now + _TOKEN_TTL,
    }
    segments = [
        _b64url(json.dumps(header, separators=(",", ":")).encode()),
        _b64url(json.dumps(claims, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode("ascii")
    try:
        signature = _sign_rs256(private_key, signing_input)
    except Exception as e:  # noqa: BLE001
        raise SecretError(f"Ký JWT lỗi (private_key không hợp lệ?): {type(e).__name__}") from None
    assertion = ".".join(segments) + "." + _b64url(signature)

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            token_uri, data={"grant_type": _GRANT, "assertion": assertion}
        )
    if resp.status_code != 200:
        raise SecretError(f"Đổi token Google thất bại (HTTP {resp.status_code})") from None
    body = resp.json()
    token = body.get("access_token")
    if not token:
        raise SecretError("Phản hồi token Google thiếu access_token") from None
    expires_at = now + int(body.get("expires_in", _TOKEN_TTL))
    return token, expires_at
