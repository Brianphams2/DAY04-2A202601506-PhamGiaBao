# Bàn giao `publish_facebook_page` — Người 4 → Người 1

Trạng thái: **code xong, đã smoke test offline; chưa test live** (chưa có Page token). Đây là tool optional/stretch trong plan — theo plan, chỉ tích hợp sau khi `send_telegram` chạy ổn live. Không cần thêm dependency.

## 1. Contract

```text
name: publish_facebook_page
purpose: Đăng một bản tin đã hoàn chỉnh lên Facebook Page của team qua Graph API POST /{page-id}/feed.
when_to_use: Người dùng yêu cầu đăng/publish một draft lên Facebook Page, và draft đó đã hiện trong hội thoại.
when_not_to_use: Đăng lên profile cá nhân, group, hoặc page khác; soạn/sửa nội dung (dùng `format`); khi kênh được yêu cầu là Telegram.
inputs: message (string, bắt buộc), link (string, optional, http/https), confirmed (bool, default false)
outputs: status, preview, page_id, post_id, permalink, chars, link
requires_env: FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_GRAPH_VERSION (optional, default v21.0)
side_effect: true
requires_confirmation: true
error_cases: FacebookInputError, FacebookConfigError, FacebookAuthError, FacebookPermissionError, FacebookRateLimited, FacebookPolicyBlock, FacebookNetworkError, FacebookAPIError
smoke_test_command: python tools/publish_facebook_page/smoke_test.py
```

## 2. Registry — `tools/__init__.py`

```python
from .publish_facebook_page.tool import publish_facebook_page
```

```python
TOOL_FUNCTIONS = {
    ...
    "publish_facebook_page": publish_facebook_page,
}
```

Tên hàm trùng tên tool, không đụng hàm nào đang có trong registry.

## 3. Declaration — `artifacts/tools.yaml`

```yaml
  - name: publish_facebook_page
    description: "Đăng một bản tin đã hoàn chỉnh lên Facebook Page của team. Gọi lần đầu với confirmed=false để lấy preview cho người dùng duyệt; chỉ gọi lại với confirmed=true sau khi người dùng đồng ý. Chỉ đăng được lên đúng page đã cấu hình."
    requires_confirmation: true
    parameters:
      type: object
      properties:
        message: {type: string, default: "", description: "Nội dung bài đăng đã hoàn chỉnh"}
        link: {type: string, default: "", description: "URL http(s) đính kèm, có thể bỏ trống"}
        confirmed: {type: boolean, default: false, description: "Chỉ đặt true sau khi người dùng xác nhận preview"}
      required: [message]
```

## 4. `.env.example`

```bash
# --- Facebook Page publishing (optional) ---
FACEBOOK_PAGE_ID=
FACEBOOK_PAGE_ACCESS_TOKEN=
# Optional, mặc định v21.0
FACEBOOK_GRAPH_VERSION=v21.0
```

Lấy credentials: Facebook Page → Meta developer app → Graph API Explorer → sinh **Page** access token có `pages_manage_posts` + `pages_read_engagement` → đổi sang long-lived token nếu demo cách xa thời điểm sinh token. Token hết hạn sẽ báo `FacebookAuthError`.

## 5. Điểm cần Người 1 quyết

- **Có khai báo trong `tools.yaml` hay không.** Mỗi declaration thừa đều được gửi cho model và có thể làm hỏng routing của base eval. Nếu chưa có Page token thật để demo, đề xuất giữ implementation + registry nhưng **chưa** thêm declaration vào `tools.yaml`, đúng theo `TOOL-SETUP.md` §3 (strict isolation).
- **Thứ tự**: plan ghi rõ chỉ làm Facebook sau khi Telegram chạy ổn. Nếu thời gian gấp, bỏ tool này không ảnh hưởng definition of done vì `send_telegram` đã là tool mới của team.

## 6. UI cần gì

Response `needs_confirmation` trả sẵn `preview` cho modal:

```json
{"page_id": "1234567890", "chars": 640, "link": "https://example.com",
 "credentials_ready": true, "message_preview": "Market brief ..."}
```

Sau khi publish thành công, `permalink` (dạng `https://www.facebook.com/{page}/posts/{story}`) là evidence để mở kiểm tra và đưa vào transcript. Không field nào chứa access token.

## 7. Evidence

`python tools/publish_facebook_page/smoke_test.py` → **9/9 checks passed**, exit 0 (offline, không đăng gì):

```text
PASS  empty message is rejected
PASS  over-limit message is rejected
PASS  non-http link is rejected
PASS  dry run stops at needs_confirmation
PASS  dry run returns no error
PASS  preview carries what the UI modal needs
PASS  dry run leaks no secret
PASS  permalink is built from the composite post id
PASS  missing credentials are a config error, not a crash
```

Các nhánh lỗi Graph API (190 token hết hạn, 200 thiếu permission, 100 sai tham số, 32 rate limit, 368 bị block, 200-OK-không-có-id, network error) đã verify bằng mocked response — đúng error code, không rò token, và access token nằm trong POST body chứ không nằm trong URL.

**Chưa chạy live.** Trước khi claim tool này trong report, phải chạy `python tools/publish_facebook_page/smoke_test.py --live` một lần với Page token thật và giữ lại output.
