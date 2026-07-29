from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err


# Convenience aliases so the model can pass common tickers instead of CoinGecko ids.
COIN_ALIASES = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "doge": "dogecoin",
    "ada": "cardano",
    "usdt": "tether",
    "usdc": "usd-coin",
}


def get_coin_price(coin_id: str = "", vs_currency: str = "usd") -> dict[str, Any]:
    """Fetch a crypto spot price from CoinGecko (/simple/price).

    Read-only, no side effects. Works without an API key on the public
    endpoint; set COINGECKO_API_KEY (Demo plan) for a higher rate limit.
    """
    try:
        coin_id = (coin_id or "").strip().lower()
        if not coin_id:
            raise ValueError("coin_id is required, e.g. 'bitcoin' or 'btc'")
        coin_id = COIN_ALIASES.get(coin_id, coin_id)
        vs_currency = (vs_currency or "usd").strip().lower()

        headers = {}
        key = os.getenv("COINGECKO_API_KEY")
        if key:
            headers["x-cg-demo-api-key"] = key

        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true",
            },
            headers=headers,
            timeout=TIMEOUT,
        )
        if response.status_code == 429:
            return {
                "tool": "get_coin_price",
                "coin_id": coin_id,
                "error": "rate_limited",
                "message": "CoinGecko rate limit hit (public: ~5-15 req/min).",
                "retry_hint": "Wait ~60s or set COINGECKO_API_KEY (Demo plan).",
            }
        response.raise_for_status()
        data = response.json()

        entry = data.get(coin_id)
        if not entry:
            return {
                "tool": "get_coin_price",
                "coin_id": coin_id,
                "error": "coin_not_found",
                "message": f"No price for {coin_id!r}. Use a CoinGecko id like 'bitcoin', 'ethereum', 'solana'.",
            }
        if vs_currency not in entry:
            return {
                "tool": "get_coin_price",
                "coin_id": coin_id,
                "error": "currency_not_supported",
                "message": f"Currency {vs_currency!r} not supported. Try 'usd', 'eur', 'vnd'.",
            }

        return {
            "tool": "get_coin_price",
            "coin_id": coin_id,
            "price": entry.get(vs_currency),
            "currency": vs_currency.upper(),
            "market_cap": entry.get(f"{vs_currency}_market_cap"),
            "volume_24h": entry.get(f"{vs_currency}_24h_vol"),
            "change_24h_percent": entry.get(f"{vs_currency}_24h_change"),
            "as_of_unix": entry.get("last_updated_at"),
            "source": "coingecko.com",
        }
    except Exception as exc:
        return err("get_coin_price", exc)
