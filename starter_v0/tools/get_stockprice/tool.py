from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err


def get_stock_price(symbol: str = "") -> dict[str, Any]:
    """Fetch a stock quote from Alpha Vantage (GLOBAL_QUOTE).

    Read-only, no side effects. US equities are quoted in USD.
    """
    try:
        key = os.getenv("ALPHAVANTAGE_API_KEY")
        if not key:
            raise RuntimeError("Missing ALPHAVANTAGE_API_KEY env var")
        symbol = (symbol or "").strip().upper()
        if not symbol:
            raise ValueError("symbol is required, e.g. 'AAPL'")

        response = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": key},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        # Alpha Vantage signals problems inside a 200 body, not via HTTP status.
        if "Error Message" in data:
            raise RuntimeError(f"Alpha Vantage rejected the request: {data['Error Message']}")
        rate_note = data.get("Note") or data.get("Information")
        if rate_note:
            return {
                "tool": "get_stock_price",
                "symbol": symbol,
                "error": "rate_limited",
                "message": f"Alpha Vantage rate limit (free tier ~25 req/day): {rate_note}",
                "retry_hint": "Wait a minute or use another API key.",
            }

        quote = data.get("Global Quote") or {}
        if not quote or not quote.get("05. price"):
            return {
                "tool": "get_stock_price",
                "symbol": symbol,
                "error": "symbol_not_found",
                "message": f"No quote returned for {symbol!r}. Check the ticker (e.g. AAPL, MSFT, IBM).",
            }

        def num(field: str) -> float | None:
            raw = (quote.get(field) or "").rstrip("%")
            try:
                return float(raw)
            except ValueError:
                return None

        return {
            "tool": "get_stock_price",
            "symbol": quote.get("01. symbol", symbol),
            "price": num("05. price"),
            "currency": "USD",
            "open": num("02. open"),
            "high": num("03. high"),
            "low": num("04. low"),
            "previous_close": num("08. previous close"),
            "change": num("09. change"),
            "change_percent": num("10. change percent"),
            "volume": num("06. volume"),
            "as_of_date": quote.get("07. latest trading day"),
            "source": "alphavantage.co",
        }
    except Exception as exc:
        return err("get_stock_price", exc)
