import os
import requests
import statistics
from datetime import datetime, timezone


class HistoricalDataTool:
    """Fetches historical cryptocurrency market data from CoinGecko and computes
    trend, percent change, and volatility. Returns structured dict."""

    def run(
        self, symbol: str = "bitcoin", currency: str = "usd", days: int = 30
    ) -> dict:
        api_key = os.getenv("COINGECKO_API_KEY", "")
        headers = {"x-cg-demo-api-key": api_key} if api_key else {}

        url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
        params = {"vs_currency": currency, "days": days}

        try:
            response = requests.get(
                url, params=params, headers=headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            prices = data.get("prices", [])
            if not prices:
                return {"error": f"No historical data found for '{symbol}'."}

            history = [
                {
                    "date": datetime.fromtimestamp(
                        p[0] / 1000, tz=timezone.utc
                    ).strftime("%Y-%m-%d"),
                    "price": float(p[1]),
                }
                for p in prices
            ]

            if len(history) < 2:
                return {
                    "error": "Insufficient historical data for analysis."
                }

            start_price = history[0]["price"]
            end_price = history[-1]["price"]

            pct_change = ((end_price - start_price) / start_price) * 100

            daily_returns = [
                (history[i + 1]["price"] - history[i]["price"])
                / history[i]["price"]
                for i in range(len(history) - 1)
            ]

            volatility = (
                statistics.stdev(daily_returns) * 100
                if len(daily_returns) > 1
                else 0
            )

            if pct_change > 1.5:
                trend = "upward"
            elif pct_change < -1.5:
                trend = "downward"
            else:
                trend = "sideways"

            return {
                "symbol": symbol,
                "currency": currency,
                "days": days,
                "start_price": round(start_price, 2),
                "end_price": round(end_price, 2),
                "pct_change": round(pct_change, 2),
                "volatility_pct": round(volatility, 2),
                "trend": trend,
                "price_history": history,
            }

        except Exception as e:
            return {"error": f"HistoricalDataTool failed: {str(e)}"}
