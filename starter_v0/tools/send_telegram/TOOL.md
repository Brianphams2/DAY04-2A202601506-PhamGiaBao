---
name: send_telegram
track: bonus
kind: action
provider: Telegram Bot API
requires_env: [TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TEST_CHAT_ID]
inputs: [text, confirmed, parse_mode, destination, disable_preview]
outputs: [status, awaiting_user, question, preview, destination, chars, messages_sent, message_ids, parse_mode, fallback_to_plain]
side_effect: true
requires_confirmation: true
---
# send_telegram

Publishes a finished draft to the team's Telegram channel through the Telegram
Bot API. `track: bonus` only means it is not part of `data/eval_base.json`; the
team plan lists it as required.

The implementation lives in `tool.py` as `send_telegram_message` — the name
differs from the tool name on purpose, because `tools/send/tool.py` already
exports a function called `send_telegram`. See `HANDOVER.md`.

## When to use

- The user asked to send, post, or share a draft on Telegram.
- The draft already exists in the conversation and the user has seen it.

## When not to use

- To write or improve the draft — use `format` first, this tool only delivers.
- To send a draft the user has not read yet.
- To reach any channel other than the two configured demo channels.

## Inputs

| Arg | Type | Default | Notes |
|---|---|---|---|
| `text` | string | `""` | Message body. Required, trimmed, must be non-empty. |
| `confirmed` | boolean | `false` | Must be `true` for anything to be sent. |
| `parse_mode` | enum `markdown` \| `html` \| `plain` | `markdown` | Telegram legacy Markdown by default. |
| `destination` | enum `default` \| `test` | `default` | A label, not a chat id. Maps to `TELEGRAM_CHAT_ID` / `TELEGRAM_TEST_CHAT_ID`. |
| `disable_preview` | boolean | `true` | Suppresses Telegram's link preview card. |

The bot token and chat id are read from the environment. The model cannot pass,
override, or read them.

## Outputs

Two-step flow. With `confirmed=false` the tool sends nothing and returns:

```json
{
  "tool": "send_telegram",
  "status": "needs_confirmation",
  "awaiting_user": true,
  "question": "Gửi tin này lên Telegram (default, 812 ký tự, 1 message)? ...",
  "preview": {
    "destination": "default", "chars": 812, "messages": 1,
    "parse_mode": "markdown", "credentials_ready": true,
    "text_preview": "**Market brief** ..."
  }
}
```

`awaiting_user: true` is what makes the gate real. `run_model_tool_loop` in
`chat.py` stops the round as soon as a tool result carries that flag and returns
`status: "waiting_for_user"` with `question` as the assistant text. Without it
the loop would feed this preview straight back to the model, which could answer
its own confirmation prompt and call again with `confirmed=true` in the same
turn — the user would never see it. The gate is enforced by the harness, not by
the model's cooperation.

`preview` is what the UI shows in the confirmation modal. `credentials_ready`
warns that the send would fail on missing env vars before the user commits.

With `confirmed=true` and a successful send:

```json
{
  "tool": "send_telegram", "status": "sent", "destination": "default",
  "chars": 812, "messages_sent": 1, "message_ids": [4471],
  "parse_mode": "markdown", "fallback_to_plain": false
}
```

Drafts longer than 4096 characters are split on paragraph, line, then word
boundaries and sent as consecutive messages (hard stop at 5 messages).

## Error cases

Errors return `status: "error"` plus `error` and `message`, matching the
`tools/_shared.py` `err()` shape.

| `error` | Cause |
|---|---|
| `TelegramInputError` | Empty `text`, unknown `parse_mode`/`destination`, or draft over 5 messages. |
| `TelegramConfigError` | `TELEGRAM_BOT_TOKEN` or the chat id env var is unset. |
| `TelegramAuthError` | Telegram 401 — bad or revoked bot token. |
| `TelegramPermissionError` | Telegram 403 — bot is not an admin of the channel, or was blocked. |
| `TelegramRateLimited` | Telegram 429. Retries once automatically when `retry_after` ≤ 5s. |
| `TelegramRequestError` | Telegram 400 that is not a parse error, e.g. chat not found. |
| `TelegramNetworkError` | DNS, TLS, timeout, or connection failure. |
| `TelegramAPIError` | Any other non-OK Graph response. |

A 400 caused by broken Markdown is not an error: the chunk is resent as plain
text and the result carries `fallback_to_plain: true`.

If a multi-message send fails halfway, the error also carries
`status_detail: "partial_send"` with the `message_ids` that did land.

## Security

- The bot token appears in Telegram's request URL, so it leaks into exception
  strings. Every returned `message` is passed through a mask that redacts the
  token and both chat ids.
- Chat ids are never returned — only the `destination` label.
- Keep Telegram credentials unset during `run_eval` runs.

## Smoke test

Offline (no message sent, no API call):

```bash
python tools/send_telegram/smoke_test.py
```

Live send to the demo channel, only after a teammate confirms:

```bash
python tools/send_telegram/smoke_test.py --live
```

One-liner dry run once Người 1 has registered the tool:

```bash
python -c "from pathlib import Path; from env_loader import load_lab_env; load_lab_env(Path.cwd()); from tools import TOOL_FUNCTIONS as T; r=T['send_telegram']('AI20k dry run', confirmed=False); print({'status':r.get('status'), 'error':r.get('error')})"
```

PASS when `status` is `needs_confirmation` and `error` is `None`.
