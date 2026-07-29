"""Finance Research Agent — Streamlit UI.

Reuses `run_model_tool_loop` from chat.py so the UI, the CLI and the eval all
drive the exact same agent loop, prompt and tool declarations.

    cd starter_v0
    streamlit run app.py
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    json_text,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import PROVIDER_CHOICES, make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


HISTORY_WINDOW = 5
ACTION_TOOLS = {"send_telegram", "publish_facebook_page"}

# Any env value long enough to be a credential is redacted before rendering.
SECRET_ENV_KEYS = (
    "VILAO_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
    "TAVILY_API_KEY", "FIRECRAWL_API_KEY", "RAPIDAPI_KEY", "ALPHAVANTAGE_API_KEY", "COINGECKO_API_KEY",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_TEST_CHAT_ID",
    "FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN",
)


def mask_secrets(text: str) -> str:
    for key in SECRET_ENV_KEYS:
        value = os.getenv(key)
        if value and len(value) > 6:
            text = text.replace(value, f"<{key}>")
    return text


def render_json(value: Any, *, max_chars: int | None = 4000) -> None:
    st.code(mask_secrets(json_text(value, max_chars=max_chars)), language="json")


def status_badge(status: str) -> str:
    return {
        "answered": "✅ answered",
        "waiting_for_user": "⏸️ waiting for user",
        "max_tool_rounds": "⚠️ hit max tool rounds",
        "provider_error": "❌ provider error",
    }.get(status, status)


def find_pending_action(tool_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the last action-tool call that stopped for confirmation."""
    for event in reversed(tool_events):
        result = event.get("result")
        if isinstance(result, dict) and result.get("status") == "needs_confirmation":
            return event
    return None


def render_trace(turn: dict[str, Any]) -> None:
    if turn.get("error"):
        st.error(mask_secrets(str(turn["error"])))
        return

    rounds = turn.get("rounds") or []
    if not rounds:
        return

    st.caption(f"{status_badge(turn.get('status', ''))} · {len(rounds)} round(s)")
    for round_record in rounds:
        calls = round_record.get("tool_calls") or []
        header = ", ".join(call["name"] for call in calls) if calls else "no tool call"
        with st.expander(f"Round {round_record['round']} — {header}", expanded=False):
            if round_record.get("assistant_text"):
                st.markdown(f"**Model:** {round_record['assistant_text']}")
            for event in round_record.get("tool_results") or []:
                result = event.get("result")
                is_error = isinstance(result, dict) and result.get("error")
                icon = "❌" if is_error else "🔧"
                st.markdown(f"{icon} **`{event['tool']}`**")
                st.markdown("*args*")
                render_json(event.get("args"), max_chars=1500)
                st.markdown("*result*")
                render_json(result)


def main() -> None:
    st.set_page_config(page_title="Finance Research Agent", page_icon="📈", layout="wide")

    with st.sidebar:
        st.header("Cấu hình")
        provider_name = st.selectbox(
            "Provider",
            PROVIDER_CHOICES,
            index=PROVIDER_CHOICES.index("vilao") if "vilao" in PROVIDER_CHOICES else 0,
        )
        model = st.text_input("Model", value="", placeholder="để trống = model mặc định của provider")
        version = st.text_input("Version label", value="v1")
        max_tool_rounds = st.slider("Max tool rounds", 1, 8, 4)

        system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        tools_path = ARTIFACTS_DIR / "tools.yaml"
        artifact_version = build_artifact_version(version, system_prompt_path, tools_path)

        st.divider()
        st.subheader("Artifact")
        st.code(artifact_version.artifact_version, language="text")

        declarations = load_tool_declarations(tools_path)
        st.caption(f"{len(declarations)} tool được khai báo")
        st.text("\n".join(
            f"{'🔒 ' if d['name'] in ACTION_TOOLS else '   '}{d['name']}" for d in declarations
        ))
        st.caption("🔒 = action tool, cần xác nhận trước khi chạy")

        st.divider()
        if st.button("Xoá hội thoại", use_container_width=True):
            for key in ("turns", "history", "transcript", "transcript_path"):
                st.session_state.pop(key, None)
            st.rerun()

    st.title("📈 Finance Research Agent")

    if "turns" not in st.session_state:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), "ui", timestamp])
        st.session_state.turns = []
        st.session_state.history = []
        st.session_state.transcript_path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
        st.session_state.transcript = {
            "transcript_id": transcript_id,
            **artifact_version_dict(artifact_version),
            "provider": provider_name,
            "model": model or None,
            "interface": "streamlit_ui",
            "system_prompt": str(system_prompt_path),
            "tools": str(tools_path),
            "history_window": HISTORY_WINDOW,
            "max_tool_rounds": max_tool_rounds,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        }

    for turn in st.session_state.turns:
        with st.chat_message("user"):
            st.markdown(turn["user"])
        with st.chat_message("assistant"):
            st.markdown(turn.get("assistant_text") or "")
            render_trace(turn)

    pending = None
    if st.session_state.turns:
        last = st.session_state.turns[-1]
        if last.get("status") == "waiting_for_user":
            pending = find_pending_action(last.get("tool_events") or [])

    def run_turn(user_text: str) -> None:
        system_prompt = system_prompt_path.read_text(encoding="utf-8")
        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(st.session_state.history, HISTORY_WINDOW),
            {"role": "user", "content": user_text},
        ]
        turn_record: dict[str, Any] = {
            "turn_index": len(st.session_state.turns) + 1,
            "started_at": now_iso(),
            "user": user_text,
            "status": "started",
            "assistant_text": None,
            "rounds": [],
            "tool_events": [],
        }
        try:
            with st.spinner("Agent đang chạy..."):
                result = run_model_tool_loop(
                    provider=make_provider(provider_name),
                    messages=messages,
                    tools=to_openai_tools(declarations),
                    model=model or None,
                    max_tool_rounds=max_tool_rounds,
                )
            turn_record.update(result)
            st.session_state.history.append({"role": "user", "content": user_text})
            st.session_state.history.append({"role": "assistant", "content": result["assistant_text"]})
        except Exception as exc:
            turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})

        turn_record["ended_at"] = now_iso()
        st.session_state.turns.append(turn_record)
        st.session_state.transcript["turns"].append(turn_record)
        write_transcript(st.session_state.transcript_path, st.session_state.transcript)

    if pending:
        result = pending["result"]
        preview = result.get("preview") or {}
        st.warning(f"⏸️ `{pending['tool']}` đang chờ xác nhận — chưa có gì được gửi đi.")
        with st.container(border=True):
            st.subheader("Xác nhận trước khi đăng")
            columns = st.columns(4)
            columns[0].metric("Kênh", str(preview.get("destination") or preview.get("page_id") or "—"))
            columns[1].metric("Ký tự", preview.get("chars", "—"))
            columns[2].metric("Số message", preview.get("messages", 1))
            columns[3].metric("Credentials", "sẵn sàng" if preview.get("credentials_ready") else "THIẾU")

            if not preview.get("credentials_ready"):
                st.error("Thiếu env var — bấm gửi bây giờ sẽ lỗi. Kiểm tra cấu hình trước.")

            st.markdown("**Nội dung sẽ được đăng:**")
            st.markdown(f"> {mask_secrets(str(preview.get('text_preview') or preview.get('message_preview') or ''))}")

            left, right = st.columns(2)
            if left.button("✅ Xác nhận, gửi đi", type="primary", use_container_width=True):
                # Echo the exact draft back. The full text lives in the tool args,
                # not in the trimmed history, so without this the model could
                # resend a shortened version of what the user just approved.
                args = pending.get("args") or {}
                original = args.get("text") or args.get("message") or ""
                run_turn(
                    f"Tôi xác nhận. Gọi lại `{pending['tool']}` với confirmed=true và đúng nội dung này:\n\n{original}"
                )
                st.rerun()
            if right.button("✖️ Huỷ", use_container_width=True):
                run_turn("Không gửi nữa, huỷ đi. Đừng gọi lại tool đó.")
                st.rerun()

    if user_text := st.chat_input("Hỏi về thị trường, hoặc yêu cầu gửi bản tin đi..."):
        run_turn(user_text)
        st.rerun()

    if st.session_state.turns:
        st.caption(f"Transcript: `{st.session_state.transcript_path.relative_to(ROOT)}`")


if __name__ == "__main__":
    main()
