# Lấy 2 biến env Telegram — Người 4 → Người 1

Cần đúng 2 biến cho `send_telegram`:

```bash
TELEGRAM_BOT_TOKEN=   # token của bot, lấy từ @BotFather
TELEGRAM_CHAT_ID=     # id của channel demo, số âm dạng -100xxxxxxxxxx
```

Biến thứ 3 `TELEGRAM_TEST_CHAT_ID` chỉ cần nếu dùng `destination: test`.

## Bước 1 — Tạo bot, lấy `TELEGRAM_BOT_TOKEN`

1. Mở Telegram, tìm [@BotFather](https://t.me/BotFather), bấm Start.
2. Gõ `/newbot`.
3. Đặt display name, ví dụ `AI20k Finance Research Agent`.
4. Đặt username, phải kết thúc bằng `bot`, ví dụ `ai20k_finance_day04_bot`.
5. BotFather trả về một dòng dạng `123456789:AAF...`. Đó là `TELEGRAM_BOT_TOKEN`.

Token này = toàn quyền điều khiển bot. Không dán vào chat nhóm, report, screenshot, hay commit.
Nếu lỡ lộ: `/revoke` trong BotFather để sinh token mới.

## Bước 2 — Tạo channel demo và thêm bot làm admin

### 2.1 Tạo channel private

Trên điện thoại:

1. Mở Telegram, bấm icon bút chì / dấu ✏️ ở góc (iOS: dưới phải, Android: dưới phải).
2. Chọn **New Channel**.
3. Đặt tên channel, ví dụ `AI20k Day04 Demo`. Description để trống cũng được. Bấm **Next**.
4. Màn hình Channel Type: chọn **Private**. Bấm **Next**.
5. Màn hình "Add Subscribers": bấm **Skip** hoặc dấu ✓ để bỏ qua. Không cần thêm ai.

Trên Telegram Desktop: menu ☰ → **New Channel** → điền tên → **Private** → Skip.

### 2.2 Thêm bot làm admin

Bot **phải** là admin thì mới đăng được vào channel. Chỉ thêm làm subscriber là không đủ.

1. Mở channel vừa tạo, bấm **tên channel ở thanh trên cùng** để mở Channel Info.
2. Vào mục Administrators:
   - iOS: bấm **Edit** (góc trên phải) → **Administrators**.
   - Android: bấm icon bút chì ✏️ → **Administrators**.
   - Desktop: bấm **⋮** → **Manage Channel** → **Administrators**.
3. Bấm **Add Admin**.
4. Ô tìm kiếm: gõ **đầy đủ username của bot**, ví dụ `ai20k_finance_day04_bot`. Bot không nằm trong danh bạ nên gõ thiếu sẽ không ra. Bấm vào bot trong kết quả.
5. Bảng quyền hiện ra: bật **Post Messages**. Các quyền còn lại (Edit, Delete, Add Members, Manage Video Chats, Add New Admins...) tắt hết.
6. Lưu: bấm ✓ hoặc **Done** ở góc trên phải. Quay lại phải thấy bot trong danh sách Administrators.

### 2.3 Gửi một tin nhắn trong channel

Gõ `hello` vào channel và gửi. **Phải làm sau bước 2.2, không phải trước.**

Lý do: `get_chat_id.py` gọi Telegram `getUpdates`, mà API này chỉ trả về những sự kiện bot **nhìn thấy được**. Bot chỉ nhận được message của channel kể từ lúc nó thành admin. Channel trống, hoặc message gửi trước khi bot được thêm vào, thì bot không có update nào → script không tìm ra chat id.

Telegram chỉ giữ update trong 24 giờ, nên nếu để cách hôm sau mới chạy script thì gửi lại một tin nhắn mới.

## Bước 3 — Lấy `TELEGRAM_CHAT_ID`

Đặt token vào `starter_v0/.env` trước:

```bash
TELEGRAM_BOT_TOKEN=123456789:AAF...
```

Rồi chạy:

```bash
cd starter_v0
python tools/send_telegram/get_chat_id.py
```

Script in ra danh sách chat mà bot nhìn thấy, ví dụ:

```text
Bot OK: @ai20k_finance_day04_bot

TELEGRAM_CHAT_ID có thể dùng:
  -1002345678901   (channel) AI20k Day04 Demo
```

Copy số âm đó vào `.env`:

```bash
TELEGRAM_CHAT_ID=-1002345678901
```

Script gọi `getUpdates` nên token không bao giờ xuất hiện trên command line hay shell history.

Không thấy chat nào → kiểm tra theo thứ tự: bot đã nằm trong danh sách Administrators chưa (bước 2.2), đã gửi tin nhắn **sau** khi thêm bot chưa (bước 2.3), và tin nhắn đó có trong vòng 24 giờ không. Gửi thêm một tin nhắn mới rồi chạy lại script.

Phương án dự phòng nếu vẫn không ra: đặt channel thành **Public** và gán một username (Channel Info → Edit → Channel Type → Public). Khi đó dùng luôn username làm chat id, không cần chạy script:

```bash
TELEGRAM_CHAT_ID=@ten_channel_cua_ban
```

Cách này tiện nhưng channel thành công khai, ai cũng đọc được nội dung team đăng. Chỉ dùng khi kẹt.

## Bước 4 — Verify

```bash
cd starter_v0
python tools/send_telegram/smoke_test.py          # offline, không gửi gì, phải 11/11
python tools/send_telegram/smoke_test.py --live   # gửi thật 1 message vào channel
```

`--live` PASS và message xuất hiện trong channel → 2 biến đúng. Giữ lại output này làm evidence cho REPORT (output đã được mask, không chứa token).

Lỗi hay gặp:

| Kết quả | Nguyên nhân |
|---|---|
| `TelegramAuthError` | Token sai hoặc đã bị revoke. |
| `TelegramPermissionError` | Bot chưa là admin của channel, hoặc thiếu quyền Post Messages. |
| `TelegramRequestError` (chat not found) | `TELEGRAM_CHAT_ID` sai, thiếu dấu `-`, hoặc thiếu tiền tố `-100`. |
| `TelegramConfigError` | Biến chưa được set trong môi trường đang chạy. |

## Bước 5 — Đưa lên Vercel

Trên Vercel, env var đặt ở **Project → Settings → Environment Variables**, không phải file `.env` trong repo (`.env` đã gitignore và không được deploy).

1. Thêm `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID`.
2. Chọn đúng environment: Production, và Preview nếu cần demo bản preview.
3. **Redeploy** sau khi thêm — env var mới không áp dụng cho deployment đã build trước đó.
4. Sau khi deploy, mở UI và chạy thử luồng thật: agent gọi tool → modal hiện preview → xác nhận → message vào channel. Nếu preview hiện `credentials_ready: false` thì env var chưa tới được runtime.

Ba điều bắt buộc tránh:

- **Không** đặt tên biến có tiền tố `NEXT_PUBLIC_`. Biến đó bị nhúng vào bundle chạy trên trình duyệt, tức là công khai token.
- **Không** commit token vào repo để "cho tiện deploy".
- Link deploy là public: ai có link cũng bấm xác nhận gửi được vào channel thật. Trỏ `TELEGRAM_CHAT_ID` vào channel private demo, hoặc chỉ set env var trong lúc demo rồi xoá.

## Cảnh báo về Vercel — cần Người 1 xác nhận trước

Hai điểm có thể chặn deploy, không liên quan tới 2 biến env:

1. **Streamlit không chạy được trên Vercel.** Vercel host static site và serverless function; Streamlit cần server chạy liên tục và WebSocket. Nếu UI làm bằng Streamlit như `TOOL-SETUP.md` §10 gợi ý thì phải đổi host — Streamlit Community Cloud, Hugging Face Spaces, Render, Railway hoặc Fly.io — hoặc viết lại UI thành Next.js/React gọi Python API route.
2. **Giới hạn thời gian chạy của serverless function.** Agent loop chạy nhiều round tool call, mỗi HTTP call trong `tools/_shared.py` đã để `TIMEOUT = 30`. Function timeout mặc định trên Vercel ngắn hơn nhiều và có trần theo plan; cần kiểm tra `maxDuration` theo plan đang dùng trước khi chốt Vercel, nếu không agent sẽ bị cắt giữa chừng.
