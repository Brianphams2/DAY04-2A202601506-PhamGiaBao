# Bàn giao `send_telegram` — Người 4 → Người 1

Trạng thái: **xong, đã smoke test**. Không sửa file trung tâm nào. Không cần thêm dependency (`requests` đã có trong `requirements.txt`).

## 1. Contract

```text
name: send_telegram
purpose: Gửi một bản tin đã hoàn chỉnh lên kênh Telegram của team qua Telegram Bot API.
when_to_use: Người dùng yêu cầu gửi/đăng/chia sẻ một draft lên Telegram, và draft đó đã hiện trong hội thoại.
when_not_to_use: Để viết hoặc sửa nội dung (dùng `format`); để gửi draft người dùng chưa đọc; để gửi tới bất kỳ kênh nào ngoài 2 kênh demo đã cấu hình.
inputs: text (string, bắt buộc), confirmed (bool, default false), parse_mode (markdown|html|plain, default markdown), destination (default|test, default default), disable_preview (bool, default true)
outputs: status, preview, destination, chars, messages_sent, message_ids, parse_mode, fallback_to_plain
requires_env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TEST_CHAT_ID (chỉ cần khi destination=test)
side_effect: true
requires_confirmation: true
error_cases: TelegramInputError, TelegramConfigError, TelegramAuthError, TelegramPermissionError, TelegramRateLimited, TelegramRequestError, TelegramNetworkError, TelegramAPIError
smoke_test_command: python tools/send_telegram/smoke_test.py
```

## 2. Registry — `tools/__init__.py`

⚠️ **Bẫy tên hàm**: `tools/send/tool.py` đã export một hàm **tên `send_telegram`**. Nếu import hàm mới cùng tên, import sau sẽ ghi đè import trước và tool `send` cũ sẽ chạy nhầm implementation. Vì vậy hàm mới tên là `send_telegram_message`.

```python
from .send_telegram.tool import send_telegram_message
```

```python
TOOL_FUNCTIONS = {
    ...
    "send_telegram": send_telegram_message,
}
```

## 3. Declaration — `artifacts/tools.yaml`

```yaml
  - name: send_telegram
    description: "Gửi một bản tin đã hoàn chỉnh lên kênh Telegram của team. Gọi lần đầu với confirmed=false để lấy preview cho người dùng duyệt; chỉ gọi lại với confirmed=true sau khi người dùng đồng ý. Không dùng để soạn nội dung."
    requires_confirmation: true
    parameters:
      type: object
      properties:
        text: {type: string, default: "", description: "Nội dung đã hoàn chỉnh cần gửi"}
        confirmed: {type: boolean, default: false, description: "Chỉ đặt true sau khi người dùng xác nhận preview"}
        parse_mode: {type: string, enum: [markdown, html, plain], default: "markdown", description: "Định dạng văn bản"}
        destination: {type: string, enum: [default, test], default: "default", description: "Nhãn kênh đã cấu hình sẵn, không phải chat id"}
        disable_preview: {type: boolean, default: true, description: "Tắt thẻ preview link"}
      required: [text]
```

`to_openai_tools()` chỉ đọc `name`, `description`, `parameters`, nên `requires_confirmation` là metadata an toàn để UI đọc và dựng confirmation modal.

## 4. `.env.example`

`TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` đã có sẵn (đang comment). Cần bỏ comment và thêm 1 dòng:

```bash
# --- Publishing tools ---
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
# Chỉ cần nếu dùng destination=test
TELEGRAM_TEST_CHAT_ID=
```

Theo `TOOL-SETUP.md` §9: để Telegram credentials **unset** trong mọi lần `run_eval`.

## 5. Hai điểm cần Người 1 quyết

1. **Trùng chức năng với tool `send` cũ.** `tools.yaml` đang khai báo `send` ("Gửi một đoạn văn bản đi") cũng gửi Telegram. Hai declaration cùng chức năng làm model dễ route sai. Đã kiểm tra: `send` **không** xuất hiện trong `data/eval_base.json`, `data/eval_group.json` hay `data/eval_research_extension.json`, nên bỏ declaration `send` khỏi `tools.yaml` không ảnh hưởng eval. Đề xuất bỏ, giữ nguyên implementation `tools/send/`.
2. **`destination`.** Là allowlist nhãn kênh để model không bao giờ chọn được `chat_id`. Nếu team chỉ dùng một kênh, có thể bỏ property này khỏi declaration — code vẫn chạy đúng với default.

## 6. UI cần gì (Bước 4 trong plan)

Response `needs_confirmation` trả sẵn `preview` để dựng modal:

```json
{"destination": "default", "chars": 812, "messages": 1,
 "parse_mode": "markdown", "credentials_ready": true,
 "text_preview": "**Market brief** ..."}
```

- `messages` > 1 nghĩa là draft sẽ bị Telegram cắt thành nhiều message.
- `credentials_ready: false` → cảnh báo trước khi người dùng bấm xác nhận, vì lệnh gửi chắc chắn fail.
- Sau khi gửi, `message_ids` là evidence cho transcript.
- Không có field nào chứa token hay chat id, an toàn để render và log.

## 7. Evidence

`python tools/send_telegram/smoke_test.py` → **11/11 checks passed**, exit 0 (offline, không gửi message):

```text
PASS  empty text is rejected
PASS  unknown parse_mode is rejected
PASS  unknown destination is rejected
PASS  dry run stops at needs_confirmation
PASS  dry run returns no error
PASS  preview carries what the UI modal needs
PASS  dry run leaks no secret
PASS  long draft splits into >1 message — 2 chunks
PASS  every chunk fits Telegram's limit
PASS  oversized draft is refused before sending
PASS  missing chat env var is a config error, not a crash
```

Các nhánh lỗi API (401, 403, 400 chat-not-found, 429 + retry, markdown parse fallback, network error, partial send) đã được verify bằng mocked response — tất cả trả đúng error code và không rò token/chat id. Chạy `--live` để test gửi thật vào private demo channel.
