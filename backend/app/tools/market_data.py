import os
import requests


class MarketDataTool:
    """Fetches live market data from CoinGecko including price, volume,
    market cap, 24h high/low, circulating supply, and market cap rank."""

    def run(self, symbol: str = "bitcoin", currency: str = "usd") -> dict:
        api_key = os.getenv("COINGECKO_API_KEY", "")
        headers = {"x-cg-demo-api-key": api_key} if api_key else {}

        # --- Fetch price, volume, market cap, 24h change ---
        price_url = (
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={symbol}"
            f"&vs_currencies={currency}"
            f"&include_24hr_vol=true"
            f"&include_market_cap=true"
            f"&include_24hr_change=true"
        )

        try:
            resp = requests.get(price_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            asset = data.get(symbol, {})
            price = asset.get(currency)
            volume = asset.get(f"{currency}_24h_vol")
            market_cap = asset.get(f"{currency}_market_cap")
            change_24h = asset.get(f"{currency}_24h_change")

            if price is None:
                return {
                    "symbol": symbol,
                    "currency": currency,
                    "error": f"No price found for {symbol.upper()} in {currency.upper()}.",
                }

            result = {
                "symbol": symbol,
                "currency": currency,
                "latest_price": price,
                "volume_24h": volume,
                "market_cap": market_cap,
                "change_24h_pct": round(change_24h, 2) if change_24h else None,
            }

            # --- Fetch additional coin details (high/low, supply, rank) ---
            try:
                coin_url = f"https://api.coingecko.com/api/v3/coins/{symbol}"
                coin_params = {
                    "localization": "false",
                    "tickers": "false",
                    "community_data": "false",
                    "developer_data": "false",
                    "sparkline": "false",
                }
                coin_resp = requests.get(
                    coin_url, params=coin_params, headers=headers, timeout=10
                )
                coin_resp.raise_for_status()
                coin_data = coin_resp.json()

                market = coin_data.get("market_data", {})
                result["high_24h"] = (
                    market.get("high_24h", {}).get(currency)
                )
                result["low_24h"] = (
                    market.get("low_24h", {}).get(currency)
                )
                result["circulating_supply"] = market.get("circulating_supply")
                result["market_cap_rank"] = coin_data.get("market_cap_rank")
                result["name"] = coin_data.get("name", symbol.title())
                result["image"] = coin_data.get("image", {}).get("small")
            except Exception:
                # Non-critical — we already have price + volume
                result["high_24h"] = None
                result["low_24h"] = None
                result["circulating_supply"] = None
                result["market_cap_rank"] = None
                result["name"] = symbol.title()
                result["image"] = None

            return result

        except Exception as e:
            return {"error": f"MarketDataTool failed: {str(e)}"}
