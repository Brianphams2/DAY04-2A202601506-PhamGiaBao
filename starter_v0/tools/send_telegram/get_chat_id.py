from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env


API_BASE = "https://api.telegram.org"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    load_lab_env(ROOT)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN in starter_v0/.env")

    try:
        response = requests.get(
            f"{API_BASE}/bot{token}/getUpdates",
            params={"allowed_updates": '["message", "channel_post"]'},
            timeout=30,
        )
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise SystemExit(f"Could not read Telegram updates: {type(exc).__name__}") from None

    if not response.ok or not payload.get("ok"):
        description = payload.get("description") or f"HTTP {response.status_code}"
        raise SystemExit(f"Telegram rejected getUpdates: {description}")

    chats: dict[str, tuple[str, str]] = {}
    for update in payload.get("result", []):
        for field in ("channel_post", "message"):
            message = update.get(field) or {}
            chat = message.get("chat") or {}
            chat_id = str(chat.get("id", ""))
            if chat_id:
                label = chat.get("title") or chat.get("username") or chat.get("first_name") or "(unnamed)"
                chats[chat_id] = (str(chat.get("type", "unknown")), str(label))

    if not chats:
        print("No chats found. Add the bot, send a new message, then run this again.")
        return

    print("CHAT_ID\tTYPE\tNAME")
    for chat_id, (chat_type, label) in chats.items():
        print(f"{chat_id}\t{chat_type}\t{label}")


if __name__ == "__main__":
    main()
