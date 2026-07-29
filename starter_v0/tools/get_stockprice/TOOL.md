---
name: get_stockprice
track: team_new
kind: live_api
provider: Alpha Vantage (GLOBAL_QUOTE)
requires_env: [ALPHAVANTAGE_API_KEY]
inputs: [symbol]
outputs: [symbol, price, currency, open, high, low, previous_close, change, change_percent, volume, as_of_date, source]
side_effect: false
requires_confirmation: false
---
# get_stockprice

Lấy giá cổ phiếu (quote gần nhất) từ Alpha Vantage. Tool read-only, không có side effect, không cần confirmation.

## Contract

- **name**: `get_stockprice` (function: `get_stock_price` trong `tool.py`)
- **purpose**: trả về giá hiện tại + biến động trong ngày của một mã cổ phiếu.
- **when_to_use**: user hỏi giá / biến động / volume của một mã cổ phiếu cụ thể (AAPL, MSFT, TSLA, IBM...).
- **when_not_to_use**:
  - hỏi giá crypto → dùng `get_coinprice`;
  - hỏi tin tức về công ty → dùng `lookup` (topic=news);
  - user chưa nói mã nào → `clarify` trước, không tự đoán mã.
- **inputs**:
  - `symbol` (string, bắt buộc): ticker, ví dụ `"AAPL"`. Tool tự uppercase/trim.
- **outputs** (dict): `symbol`, `price` (float), `currency` (luôn `"USD"` với cổ phiếu Mỹ), `open`, `high`, `low`, `previous_close`, `change`, `change_percent` (%), `volume`, `as_of_date` (ngày giao dịch gần nhất, `YYYY-MM-DD`), `source` (`alphavantage.co`).
- **requires_env**: `ALPHAVANTAGE_API_KEY` (lấy free tại https://www.alphavantage.co/support/#api-key).
- **side_effect**: không.
- **requires_confirmation**: không.

## Error cases

Mọi lỗi trả về dict (không raise), agent loop hiển thị được:

| Trường hợp | Output |
|---|---|
| Thiếu env key | `{"tool": "get_stock_price", "error": "RuntimeError", "message": "Missing ALPHAVANTAGE_API_KEY env var"}` |
| `symbol` rỗng | `error: ValueError` |
| Rate limit (free ~25 req/ngày; API trả `Note`/`Information` trong body 200) | `error: "rate_limited"` + `retry_hint` |
| Mã không tồn tại (body trả `Global Quote` rỗng) | `error: "symbol_not_found"` |
| Symbol sai định dạng bị API reject (`Error Message`) | `error: RuntimeError` kèm message của API |
| Network/timeout (30s) | `error: ConnectionError/Timeout...` |

Lưu ý: Alpha Vantage báo lỗi **trong body HTTP 200**, không qua status code — tool đã xử lý cả 3 dạng (`Error Message`, `Note`, `Information`).

## Smoke test

Chạy từ `starter_v0/` (key `demo` của Alpha Vantage chỉ hỗ trợ mã IBM):

```bash
# với key thật trong .env
python -c "from env_loader import load_lab_env; from pathlib import Path; load_lab_env(Path('.')); from tools.get_stockprice.tool import get_stock_price; print(get_stock_price('AAPL'))"

# không có key: test bằng demo key, chỉ IBM
ALPHAVANTAGE_API_KEY=demo python -c "from tools.get_stockprice.tool import get_stock_price; print(get_stock_price('IBM'))"
```

PASS khi output có `price` là số và `as_of_date` khác None.

## Cho Người 1 tích hợp

- Registry (`tools/__init__.py`): `from .get_stockprice.tool import get_stock_price` → `"get_stockprice": get_stock_price`.
- `.env.example`: thêm dòng `ALPHAVANTAGE_API_KEY=` dưới nhóm Research/read tools.
- `requirements.txt`: không cần thêm gì (chỉ dùng `requests` đã có).
- Declaration gợi ý cho `tools.yaml`:

```yaml
  - name: get_stockprice
    description: "Lấy giá cổ phiếu hiện tại (quote Alpha Vantage) theo mã ticker, ví dụ AAPL, MSFT. Chỉ dùng cho cổ phiếu; giá crypto dùng get_coinprice. Nếu user chưa nói mã nào thì hỏi lại bằng clarify, không tự đoán."
    parameters:
      type: object
      properties:
        symbol: {type: string, description: "Mã ticker cổ phiếu, ví dụ AAPL"}
      required: [symbol]
```
