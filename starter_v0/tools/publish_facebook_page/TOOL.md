---
name: publish_facebook_page
track: bonus
kind: action
provider: Facebook Graph API
requires_env: [FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_GRAPH_VERSION]
inputs: [message, link, confirmed]
outputs: [status, awaiting_user, question, preview, page_id, post_id, permalink, chars, link]
side_effect: true
requires_confirmation: true
---
# publish_facebook_page

Publishes a finished draft to the team's Facebook **Page** feed via the Graph
API `POST /{page-id}/feed` endpoint. Optional/stretch tool in the team plan;
integrate it only after `send_telegram` is verified live.

## When to use

- The user asked to publish or post a draft to the team's Facebook Page.
- The draft already exists in the conversation and the user has seen it.

## When not to use

- To post to a personal profile, a group, or any page other than the configured
  one. This tool only writes to the page id in the environment.
- To write or improve the draft — use `format` first.
- When `send_telegram` is the requested channel.

## Inputs

| Arg | Type | Default | Notes |
|---|---|---|---|
| `message` | string | `""` | Post body. Required, trimmed, max 63206 chars. |
| `link` | string | `""` | Optional http(s) URL attached to the post. |
| `confirmed` | boolean | `false` | Must be `true` for anything to be published. |

`FACEBOOK_PAGE_ID` and `FACEBOOK_PAGE_ACCESS_TOKEN` come from the environment.
The model cannot pass, override, or read them. `FACEBOOK_GRAPH_VERSION`
defaults to `v21.0`.

## Outputs

With `confirmed=false` nothing is published:

```json
{
  "tool": "publish_facebook_page",
  "status": "needs_confirmation",
  "awaiting_user": true,
  "question": "Đăng bài này lên Facebook Page (640 ký tự, kèm link)? ...",
  "preview": {
    "page_id": "1234567890", "chars": 640, "link": "https://...",
    "credentials_ready": true, "message_preview": "Market brief ..."
  }
}
```

`awaiting_user: true` makes `run_model_tool_loop` stop the round and hand
control back to the user, so the model cannot answer its own confirmation
prompt and publish within the same turn. Same mechanism as `send_telegram`.

With `confirmed=true` and a successful publish:

```json
{
  "tool": "publish_facebook_page", "status": "published",
  "page_id": "1234567890", "post_id": "1234567890_9876543210",
  "permalink": "https://www.facebook.com/1234567890/posts/9876543210",
  "chars": 640, "link": null
}
```

## Error cases

Errors return `status: "error"` plus `error` and `message`, matching the
`tools/_shared.py` `err()` shape. Graph's `code`, `error_subcode` and
`fbtrace_id` are appended to `message` for debugging.

| `error` | Cause |
|---|---|
| `FacebookInputError` | Empty `message`, over the char limit, non-http `link`, or Graph code 100. |
| `FacebookConfigError` | `FACEBOOK_PAGE_ID` or `FACEBOOK_PAGE_ACCESS_TOKEN` unset. |
| `FacebookAuthError` | Graph code 190/102 — token invalid or expired. |
| `FacebookPermissionError` | Graph code 3/10/200/299 — missing `pages_manage_posts` or not a page admin. |
| `FacebookRateLimited` | Graph code 4/17/32/613/80001. |
| `FacebookPolicyBlock` | Graph code 368 — page temporarily blocked. |
| `FacebookNetworkError` | DNS, TLS, timeout, or connection failure. |
| `FacebookAPIError` | Any other non-OK Graph response, or a 200 with no post id. |

## Security

- The page access token is sent in the POST **body**, never in the query
  string, so it stays out of URLs in logs and exception strings.
- Every returned `message` is masked for the token value.
- Page access tokens expire. `FacebookAuthError` is the expected symptom.

## Setup

1. Facebook Page + a Meta developer app with the page added.
2. Graph API Explorer → generate a **Page** access token with
   `pages_manage_posts` and `pages_read_engagement`.
3. Exchange it for a long-lived token if the demo is more than an hour away.
4. Put `FACEBOOK_PAGE_ID` and `FACEBOOK_PAGE_ACCESS_TOKEN` in `.env`.

## Smoke test

Offline (nothing published, no API call):

```bash
python tools/publish_facebook_page/smoke_test.py
```

Live publish to the demo page, only after a teammate confirms:

```bash
python tools/publish_facebook_page/smoke_test.py --live
```

One-liner dry run once Người 1 has registered the tool:

```bash
python -c "from pathlib import Path; from env_loader import load_lab_env; load_lab_env(Path.cwd()); from tools import TOOL_FUNCTIONS as T; r=T['publish_facebook_page']('AI20k dry run', confirmed=False); print({'status':r.get('status'), 'error':r.get('error')})"
```

PASS when `status` is `needs_confirmation` and `error` is `None`.
