# Finance Research Agent — Plan không conflict

## 1. Nguyên tắc làm việc

- Người 1 là owner của agent, prompt, UI/UX, file trung tâm, integration, eval, QA và report.
- Người 2–5 chỉ implement tool trong folder được giao.
- Không có hai người cùng sửa một file.
- Người 2–5 không tự sửa `tools.yaml`, `tools/__init__.py`, `.env.example` hoặc `requirements.txt`.
- Mỗi thành viên bàn giao contract và patch; Người 1 là người tích hợp vào file trung tâm.
- Không rename 6 core tool hiện tại.

## 2. Phạm vi tool cuối

### Core research tools

| Tool | Người phụ trách |
|---|---|
| `clarify` | Người 3 |
| `lookup` | Người 3 |
| `fetch` | Người 3 |
| `social_search` | Người 3 |
| `timeline` | Người 3 |
| `format` | Người 3 |

### Finance và action tools

| Tool | Người phụ trách | Trạng thái |
|---|---|---|
| `get_stockprice` | Người 2 | Bắt buộc |
| `get_coinprice` | Người 2 | Bắt buộc |
| `send_telegram` | Người 4 | Bắt buộc |
| `publish_facebook_page` | Người 4 | Optional/stretch |
| `validate_finance_content` | Người 5 | Bắt buộc |

Các tool optional có sẵn như `send`, `policy`, `papers`, `paper_text` không được tính là tool mới của team.

## 3. Phân công và file ownership

### Người 1 — Agent, prompt, UI/UX, integration và toàn bộ phần còn lại

Phụ trách:

- Chốt behavior của Finance Research Agent.
- Viết system prompt và routing rules.
- Chốt tool schema/description sau khi nhận contract từ Người 2–5.
- Generate và hoàn thiện UI/UX.
- Nối UI với `run_model_tool_loop` qua backend/API adapter.
- Chạy v0, v1, v2, v3.
- Viết 10 team eval cases.
- QA, regression, transcript, version log và report.
- Review và merge tool của Người 2–5.

Chỉ Người 1 được sửa các file trung tâm:

```text
starter_v0/artifacts/system_prompt.md
starter_v0/artifacts/tools.yaml
starter_v0/tools/__init__.py
starter_v0/requirements.txt
starter_v0/.env.example
starter_v0/data/eval_group.json
starter_v0/artifacts/version_log.csv
starter_v0/artifacts/REPORT.md
starter_v0/ui/ hoặc starter_v0/frontend/
starter_v0/backend/ hoặc API adapter
```

UI trong `stitch_vilao_content_architect/` chỉ là design reference. UI final phải nằm trong `starter_v0/` để được submit.

### Người 2 — Market data

Chỉ làm các folder:

```text
starter_v0/tools/get_stockprice/
starter_v0/tools/get_coinprice/
```

Phải bàn giao:

- `tool.py`.
- `TOOL.md`.
- Input/output contract.
- API error và rate-limit handling.
- Smoke test.
- Tên environment variables cần thêm.
- Dependency cần thêm nếu có.

Provider dự kiến:

- `get_stockprice`: Alpha Vantage.
- `get_coinprice`: CoinGecko Demo API.

Không được sửa trực tiếp registry, `tools.yaml`, `.env.example` hoặc `requirements.txt`; gửi thông tin cho Người 1 tích hợp.

### Người 3 — Core research tools

Chỉ làm các folder core sau:

```text
starter_v0/tools/clarify/
starter_v0/tools/lookup/
starter_v0/tools/fetch/
starter_v0/tools/social_search/
starter_v0/tools/timeline/
starter_v0/tools/format/
```

Phạm vi:

- Giữ nguyên tên và function contract của core tools.
- Điều chỉnh implementation hoặc `TOOL.md` nếu cần để phù hợp finance research.
- Bảo đảm source có title, URL, publisher và date khi provider trả về.
- `social_search` chỉ cung cấp sentiment/thảo luận, không được coi là nguồn duy nhất cho số liệu.
- `format` hỗ trợ market brief, company snapshot, newsletter hoặc digest nếu implementation hiện tại cần bổ sung.
- Không sửa fixed eval.

Nếu implementation hiện tại đã đủ dùng, chỉ cần bàn giao kết quả kiểm tra và không tạo thêm thay đổi không cần thiết.

### Người 4 — Publishing tools

Chỉ làm các folder:

```text
starter_v0/tools/send_telegram/
starter_v0/tools/publish_facebook_page/
```

Phạm vi:

- `send_telegram` gọi Telegram Bot API.
- `publish_facebook_page` chỉ đăng lên Facebook Page, không đăng profile cá nhân.
- Action tool phải có `requires_confirmation: true`.
- Không cho model tự chọn token, `chat_id` hoặc `page_id`.
- Xử lý invalid token, permission denied, network error và response masking.
- `publish_facebook_page` chỉ làm sau khi Telegram chạy ổn.

Không sửa trực tiếp các file trung tâm; gửi contract và environment variable list cho Người 1.

### Người 5 — Finance validation tool

#### Tool phải implement

`validate_finance_content`

#### Mục tiêu của tool

Kiểm tra một bản draft tài chính trước khi draft được hiển thị là đủ điều kiện để publish.

Tool phải kiểm tra:

- Độ dài draft.
- Citation coverage.
- Chất lượng và loại nguồn.
- Official source.
- Currency và unit của số liệu.
- `as_of_date` hoặc thời điểm dữ liệu.
- Cụm từ có tính chất khuyến nghị mua/bán.

Tool phải trả về:

- `score`.
- `checks`.
- `warnings`.
- `pass` hoặc `fail`.

Tool là local deterministic tool:

- Không gọi API.
- Không gọi model.
- Không ghi file.
- Không tự rewrite draft.
- Không publish nội dung.

#### File được phép sửa

```text
starter_v0/tools/validate_finance_content/
```

Phải tạo:

```text
starter_v0/tools/validate_finance_content/tool.py
starter_v0/tools/validate_finance_content/TOOL.md
```

#### Bàn giao

- Function implementation.
- `TOOL.md` mô tả input, output, warning codes và cách sử dụng.
- Smoke test cho draft hợp lệ và draft lỗi.
- Danh sách input/output để Người 1 đăng ký tool trong registry và `tools.yaml`.

## 4. Contract bàn giao bắt buộc cho mọi tool

Mỗi thành viên gửi cho Người 1 một contract gồm:

```text
name
purpose
when_to_use
when_not_to_use
inputs
outputs
requires_env
side_effect
requires_confirmation
error_cases
smoke_test_command
```

`TOOL.md` phải mô tả đúng contract này. Người 1 dùng contract để cập nhật `tools.yaml` và registry.

## 5. File không được động vào

### Fixed eval

- `starter_v0/data/eval_base.json`.
- Không sửa query.
- Không sửa expected args.
- Không sửa expected behavior.
- Không rename core tool nên không cần sửa tên tool trong fixed eval.

### Harness và provider

Không sửa nếu không có lỗi blocking đã được chứng minh:

```text
starter_v0/agent.py
starter_v0/chat.py
starter_v0/run_eval.py
starter_v0/providers/
starter_v0/env_loader.py
starter_v0/versioning.py
```

UI phải tái sử dụng `run_model_tool_loop` trong `chat.py`; không viết một agent loop khác.

### Secrets và generated files

Không commit hoặc submit:

```text
.env
API keys / access tokens / bot tokens
.venv/
cache/
build output
```

`runs/`, `transcripts/` và `analysis/` phải được tạo từ lệnh chạy thật, không sửa tay để tạo evidence giả.

## 6. Thứ tự tích hợp

### Bước 1 — Baseline

Người 1 chạy `v0` trên starter ban đầu trước khi thay đổi prompt/tool declaration.

### Bước 2 — Tool implementation song song

Người 2, 3, 4, 5 làm song song trong đúng folder riêng của mình.

### Bước 3 — Central integration

Người 1 review contract, sau đó cập nhật:

- `tools/__init__.py`.
- `artifacts/tools.yaml`.
- `.env.example`.
- `requirements.txt` nếu thật sự cần.

### Bước 4 — UI integration

Người 1 nối UI với agent và hiển thị:

- Response cuối.
- Tool name và args.
- Round/status.
- Result/error.
- Source, timestamp, freshness.
- Confirmation modal trước action tool.

### Bước 5 — Eval

Người 1 chạy v1, v2, v3; sau mỗi bản đọc log và ghi version log.

## 7. Quy tắc v0–v3

```text
v0: baseline, chưa tối ưu
v1: một hypothesis về system_prompt.md
v2: một hypothesis về tools.yaml
v3: một hypothesis cuối về prompt hoặc declaration
```

Trong mỗi vòng:

1. Chỉ sửa một hypothesis.
2. Không sửa `data/eval_base.json`.
3. Chạy đúng một lần base eval.
4. Đọc failure và tool trace.
5. Ghi metric, hash và run file vào `version_log.csv`.

Sau v3 mới chạy group eval, live chat và hoàn thiện report.

## 8. Definition of done

- Mỗi tool có owner duy nhất.
- Không có thành viên nào cùng sửa một file trung tâm.
- Core tool names không bị đổi.
- Có ít nhất 5 tool trong `tools.yaml`.
- Có tool mới của team với `TOOL.md`, `tool.py`, registry và declaration.
- Có đúng 10 team eval cases: 5 single-turn và 5 multi-turn.
- UI final nằm trong `starter_v0/` và hiển thị tool trace.
- Có `v0`, `v1`, `v2`, `v3` và evidence tương ứng.
- Có run JSON, transcript JSON và `REPORT.md`.
- Không có secret trong repo hoặc package submit.
