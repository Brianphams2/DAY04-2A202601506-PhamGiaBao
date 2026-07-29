---
name: timeline
track: core
kind: live_api
provider: RapidAPI Twitter API45
requires_env: [RAPIDAPI_KEY, RAPIDAPI_TWITTER_HOST]
inputs: [screenname, limit]
outputs: [tool, screenname, items]
side_effect: false
requires_confirmation: false
---
# timeline

## Purpose
Lấy danh sách các bài đăng gần nhất trên dòng thời gian (timeline) của một tài khoản X/Twitter chỉ định.

## When to Use
Khi cần theo dõi phát ngôn, cập nhật, hoặc phân tích nhận định từ một tài khoản cụ thể (ví dụ: nhà phân tích tài chính, lãnh đạo doanh nghiệp, tài khoản chính thức của dự án).

## When NOT to Use
Khi tìm kiếm bài viết theo từ khóa tổng hợp trên toàn mạng xã hội (dùng `social_search`).

## Inputs
- `screenname` (str): Handle của tài khoản Twitter/X (không chứa ký tự `@`).
- `limit` (int): Số lượng bài đăng cần lấy (default là 5).

## Outputs
- `tool` (str): `"get_user_tweets"`
- `screenname` (str): Handle tài khoản đã truyền vào.
- `items` (list[dict]): Danh sách bài viết thu được, mỗi item bao gồm: `title`, `summary`, `url`, `source`, `publisher`, `date`, `metrics`.

## Requires Env
- `RAPIDAPI_KEY`: API key cho RapidAPI.
- `RAPIDAPI_TWITTER_HOST`: Host API (default `twitter-api45.p.rapidapi.com`).

## Side Effect
`false`

## Requires Confirmation
`false`

## Error Cases
- Thiếu `RAPIDAPI_KEY`: Trả về dict lỗi `{"tool": "get_user_tweets", "error": "RuntimeError", ...}`.
- Handle tài khoản không tồn tại, tài khoản bị khóa/bảo mật, hoặc lỗi kết nối HTTP.

## Smoke Test Command
```bash
python -c "from tools.timeline.tool import get_user_tweets; print(get_user_tweets('elonmusk', limit=2))"
```

