import os

from app.tools.http import session


class MarketDataTool:
    """Fetches live market data from CoinGecko including price, volume,
    market cap, 24h high/low, circulating supply, and market cap rank."""

    def run(self, symbol: str = "bitcoin", currency: str = "usd") -> dict:
        api_key = os.getenv("COINGECKO_API_KEY", "")
        headers = {"x-cg-demo-api-key": api_key} if api_key else {}

        # Single /coins/{id} call: its market_data block carries everything
        # the old /simple/price call provided, plus high/low/supply/rank
        coin_url = f"https://api.coingecko.com/api/v3/coins/{symbol}"
        coin_params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false",
        }

        try:
            resp = session.get(
                coin_url, params=coin_params, headers=headers, timeout=10
            )
            resp.raise_for_status()
            coin_data = resp.json()

            market = coin_data.get("market_data") or {}
            price = (market.get("current_price") or {}).get(currency)

            if price is None:
                return {
                    "symbol": symbol,
                    "currency": currency,
                    "error": f"No price found for {symbol.upper()} in {currency.upper()}.",
                }

            change_24h = (
                market.get("price_change_percentage_24h_in_currency") or {}
            ).get(currency)

            return {
                "symbol": symbol,
                "currency": currency,
                "latest_price": price,
                "volume_24h": (market.get("total_volume") or {}).get(currency),
                "market_cap": (market.get("market_cap") or {}).get(currency),
                "change_24h_pct": (
                    round(change_24h, 2) if change_24h is not None else None
                ),
                "high_24h": (market.get("high_24h") or {}).get(currency),
                "low_24h": (market.get("low_24h") or {}).get(currency),
                "circulating_supply": market.get("circulating_supply"),
                "market_cap_rank": coin_data.get("market_cap_rank"),
                "name": coin_data.get("name", symbol.title()),
                "image": (coin_data.get("image") or {}).get("small"),
            }

        except Exception as e:
            return {"error": f"MarketDataTool failed: {str(e)}"}
