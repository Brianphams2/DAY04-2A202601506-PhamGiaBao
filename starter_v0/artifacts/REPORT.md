# Day 04 Lab v2 — Finance Research Agent

## Team

- Lê Nguyễn Minh Quang — 2A202601248
- Nguyễn Thành Công — 2A202601396
- Nguyễn Ngọc Hiệp — 2A202601156
- Đoàn Tiến Thành — 2A202601222
- Phạm Gia Bảo — 2A202601506
- Provider/model: VILAO / `occ/claude-sonnet-4-6`
- Final local UI: `http://localhost:8000`

## Phần A — Giới thiệu agent

### Agent làm được gì

Finance Research Agent nhận câu hỏi về giá tài sản, thị trường, doanh nghiệp,
kinh tế và tin tức tài chính. Agent chọn tool phù hợp, giữ context qua nhiều
lượt, đọc URL, định dạng digest và yêu cầu xác nhận trước khi ghi ra Telegram
hoặc Facebook.

Agent từ chối ngắn gọn các câu hỏi ngoài phạm vi tài chính và không gọi tool cho
các câu hỏi đó. Tin tức tài chính vẫn được xử lý, bao gồm tin về thị trường,
doanh nghiệp, ngân hàng trung ương, lãi suất, tiền tệ, hàng hóa và kinh tế.

### Tool agent có

| Tool | Chức năng | Ghi chú |
|---|---|---|
| `clarify` | Hỏi thêm thông tin còn thiếu hoặc xin xác nhận | Core |
| `timeline` | Đọc bài gần đây của một tài khoản cụ thể | Core |
| `social_search` | Tìm thảo luận/sentiment theo chủ đề | Core |
| `lookup` | Tìm web, tin tức, lãi suất, earnings, ngành | Core |
| `fetch` | Đọc một URL đã biết | Core |
| `format` | Tạo brief, snapshot, newsletter hoặc digest | Core |
| `get_stockprice` | Lấy quote cổ phiếu qua Alpha Vantage | Team tool |
| `get_coinprice` | Lấy giá crypto qua CoinGecko | Team tool |
| `validate_finance_content` | Kiểm tra citation, đơn vị, ngày và ngôn ngữ khuyến nghị | Team tool |
| `send_telegram` | Gửi bản tin Telegram sau confirmation | Optional/action |
| `publish_facebook_page` | Đăng Facebook Page sau confirmation | Optional/action |
| `policy` | Tìm policy nội bộ | Optional |
| `papers` | Tìm paper arXiv | Optional |
| `paper_text` | Trích text từ PDF arXiv | Optional |

### Câu hỏi mẫu

1. `What's the current price of Bitcoin in USD?`
2. `Read the financial article I mentioned.` → agent hỏi URL, sau đó fetch URL được cung cấp.
3. `Tìm tin tức mới nhất về lãi suất Fed trong tuần này.`
4. `Tìm sentiment của NVDA trên mạng xã hội.`
5. `Send this financial summary to Telegram.` → tạo preview và dừng chờ confirmation.

### Kịch bản demo

| Scenario | Trace cần thấy | Evidence |
|---|---|---|
| Crypto quote | `get_coinprice` → result → final answer | `transcripts/v3_vilao_20260729T175159296927.transcript.json` |
| Missing URL | `clarify(response_type=text)` → user bổ sung URL → `fetch` | Cùng transcript live |
| Finance-only boundary | Không gọi tool, trả lời ngoài phạm vi | `data/eval_base.json` R08/R14 và system prompt |
| External publishing | Preview → explicit confirmation → action tool | `tools/send_telegram/TOOL.md`, `server.py` |
| UI evidence | Observation, Tool call, Tool result, status | `ui/index.html`, `server.py` |

## Phần B — Evidence

### B1. Version evidence

Các run v0–v5 dưới đây là evidence thật trong `runs/`. v5 là bản hoàn thiện
flow confirmation, UI trace và UTF-8 CLI, đồng thời đã chạy lại fixed eval.

| Version | Thay đổi chính | Case accuracy | Routing | Args | Multiturn | Evidence |
|---|---|---:|---:|---:|---:|---|
| v0 | Baseline prompt/tool surface | 0.70 | 0.85 | 0.70 | 0.8333 | `runs/v0_B_base_vilao_20260729T152614469130.json` |
| v1 | Làm rõ clarification và confirmation boundary | 0.80 | 0.90 | 0.80 | 1.00 | `runs/v1_B_base_vilao_20260729T153916831242.json` |
| v2 | Tách rõ lookup/social/timeline trong declaration | 0.70 | 0.90 | 0.70 | 0.6667 | `runs/v2_B_base_vilao_20260729T154526104728.json` |
| v3 | Bổ sung finance routing và safety rules | 0.70 | 0.90 | 0.70 | 0.6667 | `runs/v3_B_base_vilao_20260729T154942264733.json` |
| v4 | Đăng ký finance/publishing tools và team eval | 0.75 | 0.95 | 0.75 | 0.6667 | `runs/v4_B_base_vilao_20260729T162646537145.json` |
| v4 group | 10 team-authored cases | 0.60 (6/10) | 0.90 | 0.60 | 0.60 | `runs/v4_B_group_vilao_20260729T163250139791.json` |
| v5 final | Finance-only scope, pending action, UI trace, UTF-8 CLI | 0.70 | 0.90 | 0.70 | 0.6667 | `runs/v5_B_base_vilao_20260729T184436149522.json` |
| v5 group | 10 team-authored cases on final artifacts | 0.60 (6/10) | 0.90 | 0.60 | 0.80 | `runs/v5_B_group_vilao_20260729T184551818384.json` |

Các run được chọn làm metric chính đều có `provider_error_cases=0` và đủ measured cases.
Hai run thử lỗi provider được giữ lại để minh bạch nhưng không dùng làm metric chính:
run OpenRouter đầu tiên bị lỗi quota 402 và run VILAO v1 đầu tiên bị lỗi kết nối.

### B2. Failure analysis

| Case | Failure | Quan sát | Bài học/fix |
|---|---|---|---|
| R03 | `wrong_arg_value` | Query bị mở rộng thành “tin tức AI nổi bật” thay vì giữ `AI` | Cần convention query trong tool declaration |
| R12 | `wrong_boundary` | Model hỏi `response_type=text` khi thiếu nội dung gửi | Action flow phải dùng preview `confirmed=false` và confirmation riêng |
| R13 | `wrong_arg_value` | Query web bị thêm “news/today” trong khi expected query là `AI` | Giữ entity người dùng cung cấp, để `topic/timeframe` mang metadata |
| M02 | `wrong_arg_value` | Context carryover thêm từ “news” vào query `robotics` | Prompt phải phân biệt subject với timeframe/topic |
| M06 | `wrong_arg_value` | Chuyển chủ đề sang OpenAI nhưng query vẫn bị mở rộng | Correction mới nhất phải thay giá trị cũ |
| F04 | `wrong_arg_value` | Social query là `NVDA Nvidia stock sentiment` thay vì `NVDA` | Không thêm từ mô tả vào query khi case yêu cầu ticker nguyên bản |
| F07 | `wrong_arg_value` | Query `Microsoft MSFT news` thay vì `MSFT` | Giữ ticker đã được xác lập trong context |
| F10 | `wrong_tool` | Lượt cuối gọi lại `lookup`, chưa gọi `format` | Cần truyền tool result/context đầy đủ cho formatting follow-up |

### B3. Team eval cases

`data/eval_group.json` có đúng 10 case: 5 single-turn (`F01–F05`) và 5
multi-turn (`F06–F10`). Kết quả group run v4 là 6/10 case pass.

| Case | What it tests | Expected |
|---|---|---|
| F01 | Stock quote | `get_stockprice(AAPL)` |
| F02 | Crypto quote | `get_coinprice(bitcoin, usd)` |
| F03 | Finance news timeframe | `lookup(topic=news, timeframe=week)` |
| F04 | Social prominence | `social_search(NVDA, Top)` |
| F05 | Publish boundary | Confirmation before send |
| F06 | Clarify ticker then quote | `get_stockprice(AAPL)` |
| F07 | News correction/context | `lookup(MSFT, news, month)` |
| F08 | URL follow-up | `fetch(https://example.com/annual-report)` |
| F09 | Switch sentiment to timeline | `timeline(VitalikButerin, limit=3)` |
| F10 | Reuse results for digest | `format(template=brief)` |

### B4. Live chat evidence

Transcript: `transcripts/v3_vilao_20260729T175159296927.transcript.json`.

| Turn | Request | Tool call | Outcome |
|---:|---|---|---|
| 1 | Current Bitcoin price | `get_coinprice(coin_id=bitcoin, vs_currency=usd)` | BTC quote returned with source and timestamp |
| 2 | Read article previously mentioned | `clarify(response_type=text)` | URL clarification returned |
| 3 | Reuters Markets URL | `fetch(url=https://www.reuters.com/markets/)` | Page content and delayed quote caveat returned |

The transcript has `provider_error_cases=0` after the CLI UTF-8 fix. It is a
real VILAO live transcript and includes artifact version, rounds and tool events.

### B5. Tool capability evidence

| Category | Evidence | Result / guardrail |
|---|---|---|
| Must-have team tool | `tools/validate_finance_content/TOOL.md` + `tool.py` + `test_smoke.py` | Deterministic validation; no external side effect |
| Additional finance tool | `tools/get_stockprice/` | Alpha Vantage quote; read-only |
| Additional finance tool | `tools/get_coinprice/` | CoinGecko quote; read-only |
| Optional action | `tools/send_telegram/` + `smoke_test.py` | Offline smoke test 11/11; live configuration requires valid channel ID and bot admin rights |
| Optional action | `tools/publish_facebook_page/` | Explicit confirmation required |
| UI core | `server.py` + `ui/index.html` | Local HTTP UI with rounds/tool events and visible trace |

Telegram live-send was not counted as successful evidence: the configured
`TELEGRAM_CHAT_ID` currently returns `chat not found`, and the bot/channel
configuration must be corrected before a real post.

### B6. Reflection

- `system_prompt.md` owns intent boundaries: finance-only scope, finance news
  exception, clarification behavior and action confirmation rules.
- `tools.yaml` owns interface boundaries: tool names, descriptions, enums and
  confirmation arguments.
- `server.py` owns side-effect safety: it persists the pending action across
  HTTP requests, sends only the exact confirmed preview and rejects ambiguous
  confirmation.
- `ui/index.html` reuses the existing `rounds/tool_events` response and now
  displays Observation, Tool call and Tool result steps with redaction.
- Automatic routing scores do not prove external API success; Telegram
  credentials and destination permissions still require manual verification.
- Next improvement: normalize query arguments more strictly and pass collected
  tool results into later multi-turn formatting requests.

## Submission checklist

- [x] `artifacts/system_prompt.md`
- [x] `artifacts/tools.yaml`
- [x] `artifacts/version_log.csv` with v0–v5 evidence
- [x] `artifacts/REPORT.md`
- [x] `data/eval_group.json` with 10 team cases
- [x] `runs/*.json`
- [x] `analysis/runs.csv`
- [x] `transcripts/*.transcript.json`
- [x] Tool implementations and `TOOL.md` files
- [x] UI: `server.py` + `ui/index.html`
- [x] `requirements.txt`
- [x] `.env`, `.venv`, API keys and caches excluded from submit
