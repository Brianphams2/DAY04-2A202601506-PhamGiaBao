---
name: clarify
track: core
kind: control
requires_env: []
inputs: [question, response_type, options]
outputs: [tool, question, response_type, options, awaiting_user]
side_effect: false
requires_confirmation: false
---
# clarify

## Purpose
Đặt câu hỏi làm rõ nhu cầu nghiên cứu tài chính của người dùng và tạm dừng cuộc hội thoại cho đến lượt phản hồi tiếp theo.

## When to Use
Khi yêu cầu của người dùng thiếu thông tin cốt lõi (ví dụ: mốc thời gian, loại tài sản, cổ phiếu hay tiền mã hóa, tiêu chí đánh giá).

## When NOT to Use
Khi câu hỏi đã rõ ràng và đủ dữ kiện để thực hiện tra cứu tin tức hoặc giá trực tiếp.

## Inputs
- `question` (str): Nội dung câu hỏi làm rõ.
- `response_type` (str): Loại câu hỏi (`text`, `choice`, hoặc `yes_no`). Default là `text`.
- `options` (list[str]): Danh sách các lựa chọn nếu `response_type` là `choice`.

## Outputs
- `tool` (str): `"ask_user"`
- `question` (str): Câu hỏi gửi tới user.
- `response_type` (str): Định dạng phản hồi kỳ vọng.
- `options` (list[str]): Các option nếu có.
- `awaiting_user` (bool): `True`

## Requires Env
Không yêu cầu API key.

## Side Effect
Không gây ra thay đổi hệ thống ngoài (ngoại trừ thay đổi trạng thái hội thoại).

## Requires Confirmation
`false`

## Error Cases
- `question` rỗng: Trả về object câu hỏi rỗng nhưng vẫn đặt `awaiting_user: True`.

## Smoke Test Command
```bash
python -c "from tools.clarify.tool import ask_user; print(ask_user('Bạn muốn phân tích mã CP nào?', response_type='choice', options=['AAPL', 'MSFT']))"
```

