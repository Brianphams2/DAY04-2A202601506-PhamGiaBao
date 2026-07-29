---
name: format
track: core
kind: local_formatter
requires_env: []
inputs: [items, template, headline]
outputs: [tool, template, markdown, item_count]
side_effect: false
requires_confirmation: false
---
# format

## Purpose
Định dạng các mục dữ liệu tài chính đã thu thập thành bản tin / báo cáo chuẩn định dạng Markdown (`sections`, `market_brief`, `company_snapshot`, `newsletter`, `bullets`, `thread`, `daily_ai_vn`).

## When to Use
Khi đã tổng hợp đủ thông tin từ các tool tra cứu (`lookup`, `fetch`, `social_search`, v.v.) và cần trình bày báo cáo chuyên nghiệp cho người dùng.

## When NOT to Use
Khi chưa có dữ liệu thu thập (tool chỉ định dạng dữ liệu có sẵn, không tự cào dữ liệu từ bên ngoài).

## Inputs
- `items` (list[dict]): Danh sách các đối tượng dữ liệu thu thập được.
- `template` (str): Mẫu định dạng (`sections`, `market_brief`, `company_snapshot`, `newsletter`, `brief`, `bullets`, `thread`, `daily_ai_vn`). Default là `sections`.
- `headline` (str): Tiêu đề chính của báo cáo.

## Outputs
- `tool` (str): `"render_digest"`
- `template` (str): Template được áp dụng.
- `markdown` (str): Văn bản báo cáo cuối cùng theo chuẩn Markdown.
- `item_count` (int): Số lượng item được xử lý trong báo cáo.

## Requires Env
Không yêu cầu API key (Local deterministic tool).

## Side Effect
`false`

## Requires Confirmation
`false`

## Error Cases
- `items` rỗng: Vẫn render khung template Markdown tương ứng với thông báo trống/không có item.

## Smoke Test Command
```bash
python -c "from tools.format.tool import render_digest; print(render_digest([{'title': 'FPT báo lãi kỷ lục', 'url': 'https://fpt.com.vn'}], template='market_brief', headline='Tin nổi bật FPT'))"
```

