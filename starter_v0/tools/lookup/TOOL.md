---
name: lookup
track: core
kind: live_api
provider: Tavily
requires_env: [TAVILY_API_KEY]
inputs: [query, topic, timeframe, max_results]
outputs: [tool, query, topic, timeframe, items]
side_effect: false
requires_confirmation: false
---
# lookup

## Purpose
Tìm kiếm dữ liệu tài chính, tin tức thị trường thực tế và báo cáo trực tuyến qua API Tavily Search.

## When to Use
Khi cần tìm kiếm thông tin vĩ mô, tin tức doanh nghiệp mới nhất, dữ liệu sự kiện tài chính hoặc phân tích ngành từ internet.

## When NOT to Use
Khi đã có URL cụ thể (nên dùng `fetch`) hoặc khi cần giá tài sản trực tuyến tính theo giây (dùng `get_stockprice` / `get_coinprice`).

## Inputs
- `query` (str): Từ khóa hoặc câu hỏi tìm kiếm.
- `topic` (str): Chủ đề tìm kiếm (`general` hoặc `news`). Default là `general`.
- `timeframe` (str | None): Khoảng thời gian (`day`, `week`, `month`, `year` hoặc `None`).
- `max_results` (int): Số lượng kết quả tối đa cần trả về (default là 5).

## Outputs
- `tool` (str): `"web_search"`
- `query` (str): Từ khóa tìm kiếm đã truyền vào.
- `topic` (str): Chủ đề tra cứu.
- `timeframe` (str | None): Khung thời gian tra cứu.
- `items` (list[dict]): Danh sách các kết quả tìm thấy, mỗi item gồm: `title`, `url`, `source`, `publisher`, `summary`, `score`, `date`.

## Requires Env
- `TAVILY_API_KEY`: API key bắt buộc để gọi Tavily API.

## Side Effect
`false`

## Requires Confirmation
`false`

## Error Cases
- Thiếu `TAVILY_API_KEY`: Trả về dict lỗi `{"tool": "web_search", "error": "RuntimeError", "message": "Missing TAVILY_API_KEY env var"}`.
- Lỗi mạng hoặc HTTP exception từ API Tavily: Trả về dict chứa `error` và `message`.

## Smoke Test Command
```bash
python -c "from tools.lookup.tool import web_search; print(web_search('báo cáo tài chính FPT 2025', max_results=2))"
```

