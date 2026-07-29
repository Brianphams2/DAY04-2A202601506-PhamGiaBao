"""Smoke test for send_telegram (Người 4).

Default run is offline-safe: validation, the confirmation gate, chunking and
secret masking are checked without touching the Telegram API. `--live` sends
one short message to TELEGRAM_CHAT_ID and requires real credentials.

    cd starter_v0
    python tools/send_telegram/smoke_test.py
    python tools/send_telegram/smoke_test.py --live
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env  # noqa: E402

load_lab_env(ROOT)

from tools.send_telegram.tool import MAX_CHARS, _split_message, send_telegram_message  # noqa: E402


results: list[bool] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    results.append(passed)
    print(f"{'PASS' if passed else 'FAIL'}  {name}{f' — {detail}' if detail else ''}")


def secrets_leaked(payload: dict) -> bool:
    blob = json.dumps(payload, ensure_ascii=False)
    for name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_TEST_CHAT_ID"):
        secret = os.getenv(name)
        if secret and len(secret) > 3 and secret in blob:
            return True
    return False


def main() -> int:
    live = "--live" in sys.argv

    empty = send_telegram_message(text="   ", confirmed=True)
    check("empty text is rejected", empty.get("error") == "TelegramInputError", empty.get("message", ""))

    bad_mode = send_telegram_message(text="hello", parse_mode="latex", confirmed=True)
    check("unknown parse_mode is rejected", bad_mode.get("error") == "TelegramInputError")

    bad_dest = send_telegram_message(text="hello", destination="ceo_dm", confirmed=True)
    check("unknown destination is rejected", bad_dest.get("error") == "TelegramInputError")

    dry = send_telegram_message(text="**Market brief**\nVN-Index +0.8%", confirmed=False)
    preview = dry.get("preview") or {}
    check("dry run stops at needs_confirmation", dry.get("status") == "needs_confirmation")
    check("dry run returns no error", dry.get("error") is None)
    check(
        "preview carries what the UI modal needs",
        {"destination", "chars", "messages", "credentials_ready", "text_preview"} <= set(preview),
        f"credentials_ready={preview.get('credentials_ready')}",
    )
    check("dry run leaks no secret", not secrets_leaked(dry))
    check(
        "dry run sets awaiting_user so the agent loop pauses for the user",
        dry.get("awaiting_user") is True and bool(dry.get("question")),
    )

    chunks = _split_message("paragraph one.\n\n" + ("x" * 5000) + "\n\ntail")
    check("long draft splits into >1 message", len(chunks) > 1, f"{len(chunks)} chunks")
    check("every chunk fits Telegram's limit", all(len(part) <= MAX_CHARS for part in chunks))

    huge = send_telegram_message(text="y" * (MAX_CHARS * 6), confirmed=True)
    check("oversized draft is refused before sending", huge.get("error") == "TelegramInputError")

    missing_test_chat = not os.getenv("TELEGRAM_TEST_CHAT_ID")
    if missing_test_chat:
        cfg = send_telegram_message(text="hello", destination="test", confirmed=True)
        check(
            "missing chat env var is a config error, not a crash",
            cfg.get("error") == "TelegramConfigError",
            cfg.get("message", ""),
        )

    if live:
        sent = send_telegram_message(text="AI20k Day04 — send_telegram smoke test", confirmed=True)
        check("live send", sent.get("status") == "sent", sent.get("message") or str(sent.get("message_ids")))
        check("live response leaks no secret", not secrets_leaked(sent))
    else:
        print("SKIP  live send (pass --live to send one real message)")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
