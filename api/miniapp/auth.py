"""Telegram Mini App initData validation."""
import hmac
import hashlib
import json
import os
from urllib.parse import parse_qsl


def validate_telegram_init_data(init_data: str) -> dict | None:
    """
    Validate Telegram Mini App initData via HMAC-SHA256.
    Returns user dict if valid, None if invalid.
    """
    if not init_data:
        return None
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        bot_token = os.environ.get("TELEGRAM_TOKEN", "")
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        expected_hash = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_hash, received_hash):
            return None

        user = json.loads(parsed.get("user", "{}"))
        return user
    except Exception as e:
        print(f"[auth] validate error: {e}")
        return None


def get_allowed_user_ids() -> list[str]:
    """Return list of allowed Telegram user IDs from env."""
    raw = os.environ.get("ALLOWED_USER_IDS", "")
    if not raw:
        # Fallback ke TELEGRAM_CHAT_ID jika ALLOWED_USER_IDS tidak di-set
        ids = list(filter(None, [
            os.environ.get("TELEGRAM_CHAT_ID", ""),
            os.environ.get("TELEGRAM_CHAT_ID_2", ""),
        ]))
        return ids
    return [uid.strip() for uid in raw.split(",") if uid.strip()]


def authenticate(request_headers: dict) -> tuple[dict | None, int]:
    """
    Authenticate request dari Mini App.
    Returns (user_dict, status_code).
    """
    # Dev mode — aktifkan dengan set MINIAPP_DEV_MODE=true di env
    if os.environ.get("MINIAPP_DEV_MODE", "").lower() == "true":
        return {"id": 0, "first_name": "Dev"}, 200

    # Coba berbagai format header key (case-insensitive)
    init_data = (
        request_headers.get("X-Telegram-Init-Data")
        or request_headers.get("x-telegram-init-data")
        or request_headers.get("HTTP_X_TELEGRAM_INIT_DATA")
        or ""
    )

    user = validate_telegram_init_data(init_data)
    if not user:
        return None, 401

    allowed = get_allowed_user_ids()
    if allowed and str(user.get("id", "")) not in allowed:
        return None, 403

    return user, 200
