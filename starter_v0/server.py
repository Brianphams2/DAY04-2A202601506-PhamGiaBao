from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from chat import execute_tool_call, run_model_tool_loop, trim_history
from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools

ROOT = Path(__file__).parent
load_lab_env(ROOT)
SYSTEM_PROMPT = (ROOT / "artifacts/system_prompt.md").read_text(encoding="utf-8")
DECLARATIONS = load_tool_declarations(ROOT / "artifacts/tools.yaml")
OPENAI_TOOLS = to_openai_tools(DECLARATIONS)
PROVIDER_NAME = "vilao"
PROVIDER = make_provider(PROVIDER_NAME)
MODEL = getattr(PROVIDER, "default_model", None)
EXTERNAL_WRITE_TOOLS = {"send", "send_telegram", "publish_facebook_page"}


def _is_explicit_rejection(text: str) -> bool:
    normalized = " ".join(text.casefold().split())
    return "không" in normalized or "hủy" in normalized or bool(re.search(r"\b(no|cancel|reject|don't)\b", normalized))


def _is_explicit_confirmation(text: str) -> bool:
    normalized = " ".join(text.casefold().split())
    if _is_explicit_rejection(normalized):
        return False
    return (
        "xác nhận" in normalized
        or "đồng ý" in normalized
        or "gửi đi" in normalized
        or "gửi luôn" in normalized
        or bool(re.search(r"\b(yes|y|ok|okay|confirm|send|send it|do it)\b", normalized))
    )


class Handler(BaseHTTPRequestHandler):
    history: list[dict[str, str]] = []
    awaiting_confirmation: bool = False
    pending_external_write: dict[str, object] | None = None

    def _send(self, status: int, body: object, content_type: str = "application/json") -> None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8") if content_type == "application/json" else body
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self._send(204, b"", "text/plain")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send(200, {"status": "ok", "provider": PROVIDER_NAME, "model": MODEL})
            return
        if path in {"/", "/index.html"}:
            self._send(200, (ROOT / "ui/index.html").read_bytes(), "text/html")
            return
        if path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/chat":
            self._send(404, {"error": "not_found"})
            return
        state = type(self)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(size))
            text = str(data.get("message", "")).strip()
            if not text:
                self._send(400, {"error": "message_required"})
                return
            if text == "__reset__":
                self.history.clear()
                state.awaiting_confirmation = False
                state.pending_external_write = None
                self._send(200, {"status": "reset"})
                return
            if state.pending_external_write:
                if _is_explicit_confirmation(text):
                    pending = state.pending_external_write
                    state.pending_external_write = None
                    event = execute_tool_call(
                        ToolCall(
                            str(pending["tool"]),
                            {**dict(pending["args"]), "confirmed": True},
                        ),
                        allow_external_writes=True,
                    )
                    sent = event.get("result", {}).get("status") in {"sent", "published"}
                    result = {
                        "status": "answered",
                        "assistant_text": "Đã gửi thành công." if sent else "Gửi thất bại: " + str(event.get("result", {}).get("message", "lỗi không xác định")),
                        "rounds": [],
                        "tool_events": [event],
                    }
                    state.awaiting_confirmation = False
                    self.history.extend([{"role": "user", "content": text}, {"role": "assistant", "content": result["assistant_text"]}])
                    self._send(200, result)
                    return
                if _is_explicit_rejection(text):
                    state.pending_external_write = None
                    state.awaiting_confirmation = False
                    result = {"status": "answered", "assistant_text": "Đã hủy gửi.", "rounds": [], "tool_events": []}
                    self.history.extend([{"role": "user", "content": text}, {"role": "assistant", "content": result["assistant_text"]}])
                    self._send(200, result)
                    return
                self._send(200, {"status": "waiting_for_user", "assistant_text": "Mình đang chờ bạn xác nhận gửi nội dung này.", "rounds": [], "tool_events": []})
                return
            allow_external_writes = state.awaiting_confirmation
            state.awaiting_confirmation = False
            messages = [{"role": "system", "content": SYSTEM_PROMPT}, *trim_history(self.history, 5), {"role": "user", "content": text}]
            result = run_model_tool_loop(provider=PROVIDER, messages=messages, tools=OPENAI_TOOLS, model=MODEL, max_tool_rounds=4, allow_external_writes=allow_external_writes)
            pending_event = next(
                (
                    event
                    for event in result.get("tool_events", [])
                    if event.get("tool") in EXTERNAL_WRITE_TOOLS
                    and event.get("result", {}).get("status") == "needs_confirmation"
                ),
                None,
            )
            if pending_event:
                state.pending_external_write = {
                    "tool": pending_event["tool"],
                    "args": dict(pending_event.get("args", {})),
                }
            external_write_succeeded = any(
                event.get("tool") in EXTERNAL_WRITE_TOOLS
                and event.get("result", {}).get("status") in {"sent", "published"}
                for event in result.get("tool_events", [])
            )
            if allow_external_writes:
                for event in result.get("tool_events", []):
                    if event.get("tool") in EXTERNAL_WRITE_TOOLS and event.get("result", {}).get("status") == "needs_confirmation":
                        args = dict(event.get("args", {}))
                        args["confirmed"] = True
                        event["result"] = TOOL_FUNCTIONS[event["tool"]](**args)
                        external_write_succeeded = external_write_succeeded or event["result"].get("status") in {"sent", "published"}
                        result["assistant_text"] = "Đã gửi thành công." if event["result"].get("status") in {"sent", "published"} else "Gửi thất bại: " + str(event["result"].get("message", "lỗi không xác định"))
            if external_write_succeeded:
                state.pending_external_write = None
            if not external_write_succeeded and pending_event:
                state.awaiting_confirmation = True
                result["assistant_text"] = "Mình đã chuẩn bị nội dung gửi. Bạn xác nhận gửi không?"
            self.history.extend([{"role": "user", "content": text}, {"role": "assistant", "content": result["assistant_text"]}])
            self._send(200, result)
        except Exception as exc:
            self._send(500, {"error": type(exc).__name__, "message": str(exc)})


if __name__ == "__main__":
    print("Finance Research Agent: http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
