from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import requests

from tools._shared import TIMEOUT, err


GRAPH_BASE = "https://graph.facebook.com"
DEFAULT_VERSION = "v21.0"
MAX_CHARS = 63206
PREVIEW_CHARS = 400

# Page id and token come from env only; the model never chooses a target page.
PAGE_ID_ENV = "FACEBOOK_PAGE_ID"
TOKEN_ENV = "FACEBOOK_PAGE_ACCESS_TOKEN"

AUTH_CODES = {190, 102}
PERMISSION_CODES = {3, 10, 200, 299}
RATE_LIMIT_CODES = {4, 17, 32, 613, 80001}


class FacebookInputError(ValueError):
    pass


class FacebookConfigError(RuntimeError):
    pass


class FacebookAuthError(RuntimeError):
    pass


class FacebookPermissionError(RuntimeError):
    pass


class FacebookRateLimited(RuntimeError):
    pass


class FacebookPolicyBlock(RuntimeError):
    pass


class FacebookNetworkError(RuntimeError):
    pass


class FacebookAPIError(RuntimeError):
    pass


def _mask(text: str) -> str:
    # Page access tokens are long-lived; never let one reach a log or transcript.
    masked = text or ""
    token = os.getenv(TOKEN_ENV)
    if token and len(token) > 3:
        masked = masked.replace(token, "***")
    return masked


def _graph_url(page_id: str) -> str:
    version = os.getenv("FACEBOOK_GRAPH_VERSION") or DEFAULT_VERSION
    return f"{GRAPH_BASE}/{version}/{page_id}/feed"


def _permalink(post_id: str) -> str:
    if "_" in post_id:
        page_part, story_part = post_id.split("_", 1)
        return f"https://www.facebook.com/{page_part}/posts/{story_part}"
    return f"https://www.facebook.com/{post_id}"


def _raise_graph_error(response: requests.Response) -> None:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    error = (payload or {}).get("error") or {}
    code = error.get("code", response.status_code)
    subcode = error.get("error_subcode")
    description = _mask(str(error.get("message") or f"HTTP {response.status_code}"))
    trace = error.get("fbtrace_id")
    suffix = f" (code {code}{f'/{subcode}' if subcode else ''}{f', fbtrace_id {trace}' if trace else ''})"

    if code in AUTH_CODES:
        raise FacebookAuthError(
            f"Page access token rejected or expired: {description}{suffix}. "
            f"Regenerate the token and update {TOKEN_ENV}."
        )
    if code in PERMISSION_CODES:
        raise FacebookPermissionError(
            f"Permission denied: {description}{suffix}. "
            "The token needs pages_manage_posts and an admin role on the page."
        )
    if code in RATE_LIMIT_CODES:
        raise FacebookRateLimited(f"Facebook rate limit: {description}{suffix}")
    if code == 368:
        raise FacebookPolicyBlock(f"Page temporarily blocked by Facebook: {description}{suffix}")
    if code == 100:
        raise FacebookInputError(f"Facebook rejected a parameter: {description}{suffix}")
    raise FacebookAPIError(f"Facebook Graph API error: {description}{suffix}")


def _fail(exc: Exception) -> dict[str, Any]:
    payload = err("publish_facebook_page", exc)
    payload["message"] = _mask(payload.get("message", ""))
    payload["status"] = "error"
    return payload


def publish_facebook_page(
    message: str = "",
    link: str = "",
    confirmed: bool = False,
) -> dict[str, Any]:
    try:
        message = (message or "").strip()
        link = (link or "").strip()
        if not message:
            raise FacebookInputError("`message` is empty. Compose the post before publishing.")
        if len(message) > MAX_CHARS:
            raise FacebookInputError(f"`message` is {len(message)} chars; Facebook allows {MAX_CHARS}.")
        if link and urlparse(link).scheme not in {"http", "https"}:
            raise FacebookInputError("`link` must be an http(s) URL.")

        page_id = os.getenv(PAGE_ID_ENV)
        token = os.getenv(TOKEN_ENV)

        if not confirmed:
            return {
                "tool": "publish_facebook_page",
                "status": "needs_confirmation",
                "awaiting_user": True,
                "message": "Show this preview to the user; resend with confirmed=true only after they say yes.",
                "question": (
                    f"Đăng bài này lên Facebook Page ({len(message)} ký tự"
                    f"{', kèm link' if link else ''})?\n\n---\n{message[:PREVIEW_CHARS]}"
                    f"{'...' if len(message) > PREVIEW_CHARS else ''}\n---\n\n"
                    "Trả lời xác nhận thì tôi mới đăng."
                ),
                "preview": {
                    "page_id": page_id or None,
                    "chars": len(message),
                    "link": link or None,
                    "credentials_ready": bool(page_id and token),
                    "message_preview": message[:PREVIEW_CHARS] + ("..." if len(message) > PREVIEW_CHARS else ""),
                },
            }

        if not page_id or not token:
            missing = [name for name in (PAGE_ID_ENV, TOKEN_ENV) if not os.getenv(name)]
            raise FacebookConfigError(f"Missing env var(s): {', '.join(missing)}.")

        # Token goes in the POST body, not the query string, so it stays out of URLs.
        form: dict[str, str] = {"message": message, "access_token": token}
        if link:
            form["link"] = link

        try:
            response = requests.post(_graph_url(page_id), data=form, timeout=TIMEOUT)
        except requests.RequestException as exc:
            raise FacebookNetworkError(f"Could not reach Facebook Graph API: {_mask(str(exc))}") from None

        if not response.ok:
            _raise_graph_error(response)

        body = response.json() if response.content else {}
        post_id = str((body or {}).get("id") or "")
        if not post_id:
            raise FacebookAPIError("Facebook returned no post id; treat the publish as unconfirmed.")

        return {
            "tool": "publish_facebook_page",
            "status": "published",
            "page_id": page_id,
            "post_id": post_id,
            "permalink": _permalink(post_id),
            "chars": len(message),
            "link": link or None,
        }
    except Exception as exc:
        return _fail(exc)
