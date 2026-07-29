# Tool: validate_finance_content

## Purpose
Kiểm tra một bản nháp (draft) bài phân tích/tin tức tài chính trước khi cho phép xuất bản (publish). Tool hoạt động như một bộ lọc chất lượng deterministic (dựa trên luật cố định, không gọi LLM/API).

## When to use
- Trước khi thực hiện hành động gửi bài (`send_telegram`, `publish_facebook_page`).
- Khi Agent hoàn thành một bản phân tích tài chính phức tạp và cần kiểm định chất lượng tổng thể.

## When not to use
- Không dùng để tìm kiếm hoặc tra cứu thông tin thị trường.
- Không dùng cho văn bản không phải là báo cáo/tin tức tài chính.

## Inputs
- `draft_text` (string, required): Toàn bộ nội dung bài viết tài chính dạng text/markdown cần thẩm định.
- `min_words` (integer, optional, default=30): Số lượng từ tối thiểu của bài viết.

## Outputs
Trả về JSON Object gồm:
- `pass` (boolean): `true` nếu bài viết đủ tiêu chí xuất bản, ngược lại `false`.
- `score` (float): Điểm chất lượng trên thang 10.0.
- `checks` (object): Chi tiết kết quả của 7 chỉ tiêu (Boolean).
- `warnings` (array of strings): Danh sách các cảnh báo vi phạm để Agent tự chỉnh sửa draft.

## Requires Env
- `None` (Local deterministic tool).

## Side Effect
- `None` (Không ghi file, không gọi mạng, không làm thay đổi trạng thái hệ thống).

## Requires Confirmation
- `false` (Không cần xác nhận từ người dùng).

## Error Cases
- Input không phải string hoặc bị rỗng: Trả về `pass: false`, `score: 0.0` cùng thông báo lỗi trong `warnings`.

## Smoke Test Command
```bash
python starter_v0/tools/validate_finance_content/test_smoke.py