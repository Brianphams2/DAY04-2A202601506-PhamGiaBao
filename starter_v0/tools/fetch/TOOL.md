---
name: fetch
track: core
kind: live_api
provider: Firecrawl
requires_env: [FIRECRAWL_API_KEY]
inputs: [url]
outputs: [tool, url, items]
side_effect: false
requires_confirmation: false
---
# fetch

## Purpose
Đọc và trích xuất nội dung văn bản chi tiết dưới dạng Markdown từ một liên kết Web (URL) cụ thể qua API Firecrawl.

## When to Use
Khi đã biết chính xác URL của bài báo tài chính, công bố thông tin doanh nghiệp, hoặc trang tin và cần bóc tách toàn bộ nội dung văn bản.

## When NOT to Use
Khi chưa có URL cụ thể và cần tìm kiếm từ khóa rộng rãi trên internet (dùng `lookup`).

## Inputs
- `url` (str): Đường dẫn URL cần cào và bóc tách nội dung.

## Outputs
- `tool` (str): `"read_url"`
- `url` (str): URL đã truyền vào.
- `items` (list[dict]): Danh sách gồm 1 item chứa: `title`, `url`, `source`, `publisher`, `date`, `summary` (tối đa 4000 ký tự markdown).

## Requires Env
- `FIRECRAWL_API_KEY`: API key bắt buộc để gọi dịch vụ Firecrawl.

## Side Effect
`false`

## Requires Confirmation
`false`

## Error Cases
- Thiếu `FIRECRAWL_API_KEY`: Trả về dict lỗi `{"tool": "read_url", "error": "RuntimeError", "message": "Missing FIRECRAWL_API_KEY env var"}`.
- URL rỗng, không hợp lệ, hoặc bị chặn bởi máy chủ đích: Trả về dict chứa lỗi HTTP exception.

## Smoke Test Command
```bash
python -c "from tools.fetch.tool import read_url; print(read_url('https://example.com'))"
```

