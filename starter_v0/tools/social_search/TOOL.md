---
name: social_search
track: core
kind: live_api
provider: RapidAPI Twitter API45
requires_env: [RAPIDAPI_KEY, RAPIDAPI_TWITTER_HOST]
inputs: [query, search_type, limit]
outputs: [tool, query, search_type, items, disclaimer]
side_effect: false
requires_confirmation: false
---
# social_search

## Purpose
Tìm kiếm bài đăng trên mạng xã hội X/Twitter theo từ khóa để phân tích sentiment và các thảo luận xung quanh mã cổ phiếu, tiền mã hóa, hoặc chủ đề tài chính.

## When to Use
Khi cần khảo sát tâm lý đám đông, xu hướng thảo luận cộng đồng hoặc phản ứng truyền thông xã hội về một mã tài sản/sự kiện.

## When NOT to Use
Không dùng làm nguồn duy nhất cho số liệu tài chính, báo cáo doanh thu, hoặc quyết định đầu tư trực tiếp.

## Inputs
- `query` (str): Từ khóa tìm kiếm (mã ticker, tên công ty, từ khóa sự kiện).
- `search_type` (str): Kiểu sắp xếp kết quả (`Latest` hoặc `Top`). Default là `Latest`.
- `limit` (int): Số lượng bài đăng tối đa trả về (default là 5).

## Outputs
- `tool` (str): `"search_tweets"`
- `query` (str): Từ khóa tra cứu.
- `search_type` (str): Loại tìm kiếm.
- `items` (list[dict]): Danh sách bài tweet thu được, mỗi item gồm: `title`, `summary`, `url`, `source`, `publisher`, `date`, `metrics`.
- `disclaimer` (str): Cảnh báo miễn trừ trách nhiệm về nguồn dữ liệu từ mạng xã hội.

## Requires Env
- `RAPIDAPI_KEY`: API key bắt buộc cho RapidAPI.
- `RAPIDAPI_TWITTER_HOST`: Host API (default `twitter-api45.p.rapidapi.com`).

## Side Effect
`false`

## Requires Confirmation
`false`

## Error Cases
- Thiếu `RAPIDAPI_KEY`: Trả về dict chứa `error: RuntimeError`.
- Lỗi kết nối HTTP/RapidAPI rate limit: Trả về dict chứa thông tin ngoại lệ `error` và `message`.

## Smoke Test Command
```bash
python -c "from tools.social_search.tool import search_tweets; print(search_tweets('BTC', limit=2))"
```

