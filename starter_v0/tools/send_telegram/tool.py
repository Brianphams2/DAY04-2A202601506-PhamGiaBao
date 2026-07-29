from __future__ import annotations

import os
import re
import time
from typing import Any

import requests

from tools._shared import TIMEOUT, err


API_BASE = "https://api.telegram.org"
MAX_CHARS = 4096
MAX_CHUNKS = 5
PREVIEW_CHARS = 400

# The model picks a label, never a raw chat id. The label maps to an env var.
CHAT_ENV = {"default": "TELEGRAM_CHAT_ID", "test": "TELEGRAM_TEST_CHAT_ID"}
PARSE_MODES = {"markdown": "Markdown", "html": "HTML", "plain": None}


class TelegramInputError(ValueError):
    pass


class TelegramConfigError(RuntimeError):
    pass


class TelegramAuthError(RuntimeError):
    pass


class TelegramPermissionError(RuntimeError):
    pass


class TelegramRateLimited(RuntimeError):
    pass


class TelegramParseError(RuntimeError):
    pass


class TelegramRequestError(RuntimeError):
    pass


class TelegramNetworkError(RuntimeError):
    pass


class TelegramAPIError(RuntimeError):
    pass


def _mask(text: str) -> str:
    # Telegram carries the bot token in the request URL, so it leaks into
    # exception strings and error descriptions. Nothing leaves this module raw.
    masked = re.sub(r"bot\d+:[A-Za-z0-9_-]+", "bot***", text or "")
    for name in ("TELEGRAM_BOT_TOKEN", *CHAT_ENV.values()):
        secret = os.getenv(name)
        if secret and len(secret) > 3:
            masked = masked.replace(secret, "***")
    return masked


def _split_message(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    parts: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= MAX_CHARS:
            parts.append(remaining)
            break
        window = remaining[:MAX_CHARS]
        cut = max(window.rfind("\n\n"), window.rfind("\n"), window.rfind(" "))
        if cut < MAX_CHARS // 2:
            cut = MAX_CHARS
        parts.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    return [part for part in parts if part]


def _body(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _post_chunk(token: str, payload: dict[str, Any], attempt: int = 0) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{API_BASE}/bot{token}/sendMessage",
            json=payload,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise TelegramNetworkError(f"Could not reach Telegram API: {_mask(str(exc))}") from None

    body = _body(response)
    if response.ok and body.get("ok"):
        return body.get("result") or {}

    code = body.get("error_code", response.status_code)
    description = _mask(str(body.get("description") or f"HTTP {response.status_code}"))
    if code == 401:
        raise TelegramAuthError("Telegram rejected the bot token (401). Check TELEGRAM_BOT_TOKEN.")
    if code == 403:
        raise TelegramPermissionError(
            f"Telegram refused the send (403): {description}. "
            "Add the bot to the channel as admin with post rights."
        )
    if code == 429:
        retry_after = int((body.get("parameters") or {}).get("retry_after", 1))
        if attempt == 0 and retry_after <= 5:
            time.sleep(retry_after)
            return _post_chunk(token, payload, attempt=1)
        raise TelegramRateLimited(f"Telegram rate limit hit; retry after {retry_after}s.")
    if code == 400 and "parse" in description.lower():
        raise TelegramParseError(description)
    if code == 400:
        raise TelegramRequestError(f"Telegram rejected the request (400): {description}")
    raise TelegramAPIError(f"Telegram API error {code}: {description}")


def _fail(exc: Exception, progress: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = err("send_telegram", exc)
    payload["message"] = _mask(payload.get("message", ""))
    payload["status"] = "error"
    payload.update(progress or {})
    return payload


def send_telegram_message(
    text: str = "",
    confirmed: bool = False,
    parse_mode: str = "markdown",
    destination: str = "default",
    disable_preview: bool = True,
) -> dict[str, Any]:
    message_ids: list[int] = []
    try:
        text = (text or "").strip()
        if not text:
            raise TelegramInputError("`text` is empty. Compose the message before sending.")
        if parse_mode not in PARSE_MODES:
            raise TelegramInputError(f"`parse_mode` must be one of {sorted(PARSE_MODES)}.")
        if destination not in CHAT_ENV:
            raise TelegramInputError(f"`destination` must be one of {sorted(CHAT_ENV)}.")

        chunks = _split_message(text)
        if len(chunks) > MAX_CHUNKS:
            raise TelegramInputError(
                f"Draft is {len(text)} chars = {len(chunks)} Telegram messages "
                f"(limit {MAX_CHUNKS}). Shorten it or send it in parts."
            )

        chat_env = CHAT_ENV[destination]
        credentials_ready = bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv(chat_env))

        if not confirmed:
            return {
                "tool": "send_telegram",
                "status": "needs_confirmation",
                "message": "Show this preview to the user; resend with confirmed=true only after they say yes.",
                # The agent loop stops on this flag, so the model cannot answer its
                # own confirmation prompt inside the same turn.
                "awaiting_user": True,
                "question": (
                    f"Gửi tin này lên Telegram ({destination}, {len(text)} ký tự, "
                    f"{len(chunks)} message)?\n\n---\n{text[:PREVIEW_CHARS]}"
                    f"{'...' if len(text) > PREVIEW_CHARS else ''}\n---\n\n"
                    "Trả lời xác nhận thì tôi mới gửi."
                ),
                "preview": {
                    "destination": destination,
                    "chars": len(text),
                    "messages": len(chunks),
                    "parse_mode": parse_mode,
                    "credentials_ready": credentials_ready,
                    "text_preview": text[:PREVIEW_CHARS] + ("..." if len(text) > PREVIEW_CHARS else ""),
                },
            }

        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv(chat_env)
        if not token or not chat_id:
            missing = [name for name in ("TELEGRAM_BOT_TOKEN", chat_env) if not os.getenv(name)]
            raise TelegramConfigError(f"Missing env var(s): {', '.join(missing)}.")

        fallback_to_plain = False
        for chunk in chunks:
            payload: dict[str, Any] = {
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": bool(disable_preview),
            }
            if PARSE_MODES[parse_mode]:
                payload["parse_mode"] = PARSE_MODES[parse_mode]
            try:
                result = _post_chunk(token, payload)
            except TelegramParseError:
                # Model-written Markdown breaks Telegram's parser often enough
                # that plain text is a better outcome than a failed send.
                payload.pop("parse_mode", None)
                result = _post_chunk(token, payload)
                fallback_to_plain = True
            message_ids.append(result.get("message_id"))

        return {
            "tool": "send_telegram",
            "status": "sent",
            "destination": destination,
            "chars": len(text),
            "messages_sent": len(message_ids),
            "message_ids": message_ids,
            "parse_mode": "plain" if fallback_to_plain else parse_mode,
            "fallback_to_plain": fallback_to_plain,
        }
    except Exception as exc:
        progress: dict[str, Any] = {"destination": destination}
        if message_ids:
            # Some chunks already reached the channel; say so instead of a bare error.
            progress.update({
                "status_detail": "partial_send",
                "messages_sent": len(message_ids),
                "message_ids": message_ids,
            })
        return _fail(exc, progress)
