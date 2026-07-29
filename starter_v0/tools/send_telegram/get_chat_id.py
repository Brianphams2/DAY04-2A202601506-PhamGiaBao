"""In ra chat id của các cuộc trò chuyện mà bot nhìn thấy (Người 4).

Dùng để lấy TELEGRAM_CHAT_ID mà không phải gõ bot token ra command line.

    cd starter_v0
    # đặt TELEGRAM_BOT_TOKEN vào .env trước
    python tools/send_telegram/get_chat_id.py

Trước khi chạy: thêm bot vào channel/group với quyền admin, rồi gửi một tin
nhắn bất kỳ trong đó. Telegram chỉ giữ update trong 24 giờ.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env  # noqa: E402

load_lab_env(ROOT)


def main() -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Chưa có TELEGRAM_BOT_TOKEN trong starter_v0/.env — lấy token từ @BotFather trước.")
        return 1

    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=30)
        body = response.json()
    except requests.RequestException as exc:
        print(f"Không gọi được Telegram API: {type(exc).__name__}")
        return 1

    if not body.get("ok"):
        print(f"Token bị Telegram từ chối (error_code {body.get('error_code')}). Kiểm tra lại TELEGRAM_BOT_TOKEN.")
        return 1
    print(f"Bot OK: @{(body.get('result') or {}).get('username')}\n")

    updates = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30).json()
    seen: dict[int, tuple[str, str]] = {}
    for update in updates.get("result", []):
        for key in ("channel_post", "message", "edited_channel_post", "my_chat_member"):
            chat = (update.get(key) or {}).get("chat") or {}
            if chat.get("id") is not None:
                seen[chat["id"]] = (chat.get("type", "?"), chat.get("title") or chat.get("username") or "(private)")

    if not seen:
        print("Chưa thấy chat nào. Làm theo thứ tự:")
        print("  1. Thêm bot vào channel/group và cấp quyền admin (Post Messages).")
        print("  2. Gửi một tin nhắn bất kỳ trong channel/group đó.")
        print("  3. Chạy lại script này trong vòng 24 giờ.")
        return 1

    print("TELEGRAM_CHAT_ID có thể dùng:")
    for chat_id, (chat_type, title) in seen.items():
        print(f"  {chat_id}   ({chat_type}) {title}")
    print("\nChannel/group có id âm, thường bắt đầu bằng -100. Chọn đúng channel demo rồi")
    print("dán vào starter_v0/.env — không dán id/token vào chat nhóm hay report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
