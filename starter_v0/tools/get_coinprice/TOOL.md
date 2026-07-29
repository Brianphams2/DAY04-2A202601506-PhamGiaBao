---
name: get_coinprice
track: team_new
kind: live_api
provider: CoinGecko (Demo API, /simple/price)
requires_env: [COINGECKO_API_KEY (optional)]
inputs: [coin_id, vs_currency]
outputs: [coin_id, price, currency, market_cap, volume_24h, change_24h_percent, as_of_unix, source]
side_effect: false
requires_confirmation: false
---
# get_coinprice

Lấy giá spot của một đồng crypto từ CoinGecko. Tool read-only, không có side effect, không cần confirmation. Chạy được **không cần API key** (public endpoint); có `COINGECKO_API_KEY` (Demo plan) thì rate limit cao hơn.

## Contract

- **name**: `get_coinprice` (function: `get_coin_price` trong `tool.py`)
- **purpose**: trả về giá hiện tại, market cap, volume 24h và % biến động 24h của một coin.
- **when_to_use**: user hỏi giá / biến động của một đồng crypto cụ thể (bitcoin, ethereum, solana...).
- **when_not_to_use**:
  - hỏi giá cổ phiếu → dùng `get_stockprice`;
  - hỏi tin tức/phân tích thị trường → dùng `lookup`;
  - user chưa nói coin nào → `clarify` trước.
- **inputs**:
  - `coin_id` (string, bắt buộc): CoinGecko id (`bitcoin`, `ethereum`, `solana`...). Chấp nhận cả ticker phổ biến, tool tự map: btc, eth, sol, bnb, xrp, doge, ada, usdt, usdc.
  - `vs_currency` (string, default `"usd"`): tiền tệ quy đổi (`usd`, `eur`, `vnd`...).
- **outputs** (dict): `coin_id`, `price` (float), `currency` (uppercase, ví dụ `"USD"`), `market_cap`, `volume_24h`, `change_24h_percent`, `as_of_unix` (unix timestamp lần cập nhật cuối), `source` (`coingecko.com`).
- **requires_env**: `COINGECKO_API_KEY` — **optional** (Demo plan, header `x-cg-demo-api-key`).
- **side_effect**: không.
- **requires_confirmation**: không.

## Error cases

Mọi lỗi trả về dict (không raise):

| Trường hợp | Output |
|---|---|
| `coin_id` rỗng | `error: ValueError` |
| HTTP 429 (public ~5–15 req/phút) | `error: "rate_limited"` + `retry_hint` |
| Coin id không tồn tại (body trả `{}`) | `error: "coin_not_found"` + gợi ý id đúng |
| `vs_currency` không được hỗ trợ | `error: "currency_not_supported"` |
| Network/timeout (30s) | `error: ConnectionError/Timeout...` |

## Smoke test

Chạy từ `starter_v0/` (không cần key):

```bash
python -c "from tools.get_coinprice.tool import get_coin_price; print(get_coin_price('btc'))"
python -c "from tools.get_coinprice.tool import get_coin_price; print(get_coin_price('khong-ton-tai'))"
```

PASS khi lệnh 1 trả `price` là số dương và lệnh 2 trả `error: "coin_not_found"`.

## Cho Người 1 tích hợp

- Registry (`tools/__init__.py`): `from .get_coinprice.tool import get_coin_price` → `"get_coinprice": get_coin_price`.
- `.env.example`: thêm dòng `# COINGECKO_API_KEY=` (optional) dưới nhóm Research/read tools.
- `requirements.txt`: không cần thêm gì (chỉ dùng `requests` đã có).
- Declaration gợi ý cho `tools.yaml`:

```yaml
  - name: get_coinprice
    description: "Lấy giá crypto hiện tại từ CoinGecko theo coin id (bitcoin, ethereum...) hoặc ticker phổ biến (btc, eth). Mặc định quy đổi USD. Chỉ dùng cho crypto; giá cổ phiếu dùng get_stockprice. Nếu user chưa nói coin nào thì hỏi lại bằng clarify."
    parameters:
      type: object
      properties:
        coin_id: {type: string, description: "CoinGecko id hoặc ticker phổ biến, ví dụ bitcoin hoặc btc"}
        vs_currency: {type: string, default: "usd", description: "Tiền tệ quy đổi: usd, eur, vnd..."}
      required: [coin_id]
```
