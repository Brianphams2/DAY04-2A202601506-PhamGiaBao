"""Smoke test for publish_facebook_page (Người 4).

Default run is offline-safe: validation, the confirmation gate and secret
masking are checked without touching the Graph API. `--live` publishes one real
post to FACEBOOK_PAGE_ID and requires a valid page access token.

    cd starter_v0
    python tools/publish_facebook_page/smoke_test.py
    python tools/publish_facebook_page/smoke_test.py --live
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

from tools.publish_facebook_page.tool import MAX_CHARS, _permalink, publish_facebook_page  # noqa: E402


results: list[bool] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    results.append(passed)
    print(f"{'PASS' if passed else 'FAIL'}  {name}{f' — {detail}' if detail else ''}")


def secrets_leaked(payload: dict) -> bool:
    blob = json.dumps(payload, ensure_ascii=False)
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    return bool(token and len(token) > 3 and token in blob)


def main() -> int:
    live = "--live" in sys.argv

    empty = publish_facebook_page(message="   ", confirmed=True)
    check("empty message is rejected", empty.get("error") == "FacebookInputError", empty.get("message", ""))

    too_long = publish_facebook_page(message="z" * (MAX_CHARS + 1), confirmed=True)
    check("over-limit message is rejected", too_long.get("error") == "FacebookInputError")

    bad_link = publish_facebook_page(message="hello", link="javascript:alert(1)", confirmed=True)
    check("non-http link is rejected", bad_link.get("error") == "FacebookInputError")

    dry = publish_facebook_page(message="Market brief: VN-Index +0.8%", link="https://example.com", confirmed=False)
    preview = dry.get("preview") or {}
    check("dry run stops at needs_confirmation", dry.get("status") == "needs_confirmation")
    check("dry run returns no error", dry.get("error") is None)
    check(
        "preview carries what the UI modal needs",
        {"page_id", "chars", "link", "credentials_ready", "message_preview"} <= set(preview),
        f"credentials_ready={preview.get('credentials_ready')}",
    )
    check("dry run leaks no secret", not secrets_leaked(dry))
    check(
        "dry run sets awaiting_user so the agent loop pauses for the user",
        dry.get("awaiting_user") is True and bool(dry.get("question")),
    )

    check(
        "permalink is built from the composite post id",
        _permalink("123_456") == "https://www.facebook.com/123/posts/456",
        _permalink("123_456"),
    )

    if not (os.getenv("FACEBOOK_PAGE_ID") and os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")):
        cfg = publish_facebook_page(message="hello", confirmed=True)
        check(
            "missing credentials are a config error, not a crash",
            cfg.get("error") == "FacebookConfigError",
            cfg.get("message", ""),
        )

    if live:
        published = publish_facebook_page(message="AI20k Day04 — publish_facebook_page smoke test", confirmed=True)
        check(
            "live publish",
            published.get("status") == "published",
            published.get("message") or published.get("permalink", ""),
        )
        check("live response leaks no secret", not secrets_leaked(published))
    else:
        print("SKIP  live publish (pass --live to publish one real post)")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
