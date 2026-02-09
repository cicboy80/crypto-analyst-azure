import json
import math
from typing import Union


class AnalyticsTool:
    """Aggregates market, historical, and sentiment data to produce
    quantitative analytics including composite score and sub-scores."""

    def run(
        self,
        market_data: Union[str, dict],
        historical_data: Union[str, dict],
        sentiment_data: Union[str, dict],
    ) -> dict:
        try:
            if isinstance(market_data, str):
                market_data = json.loads(market_data)
            if isinstance(historical_data, str):
                historical_data = json.loads(historical_data)
            if isinstance(sentiment_data, str):
                sentiment_data = json.loads(sentiment_data)

            price = market_data.get("latest_price")
            pct_change = historical_data.get("pct_change")
            volatility = historical_data.get("volatility_pct")
            trend = historical_data.get("trend")
            sentiment = sentiment_data.get("sentiment")

            if any(v is None for v in [price, pct_change, trend, sentiment]):
                return {
                    "error": (
                        "Missing required fields in analytics input. "
                        "Ensure all tools returned structured JSON."
                    )
                }

            sentiment = sentiment.lower()

            sentiment_strength = sentiment_data.get("sentiment_strength")
            sentiment_confidence = sentiment_data.get("confidence")

            if sentiment_strength is None:
                sentiment_strength = {
                    "bullish": 0.7,
                    "neutral": 0.0,
                    "bearish": -0.7,
                }.get(sentiment, 0.0)

            if sentiment_confidence is None:
                news_count = len(
                    sentiment_data.get("news_headlines", [])
                )
                sentiment_confidence = min(1.0, 0.2 + 0.1 * news_count)

            effective_sentiment = sentiment_strength * sentiment_confidence

            # Alignment logic
            aligned = (
                trend == "upward" and effective_sentiment > 0.2
            ) or (trend == "downward" and effective_sentiment < -0.2)

            # Stage 1: Momentum score bounded [-1, 1]
            momentum = (
                (pct_change / 10)
                + (effective_sentiment * 1.5)
                - (volatility / 100 if volatility else 0)
            )
            momentum = max(-1, min(1, momentum))

            # Stage 2: Contrarian / mean-reversion boost
            # price_oversold: 0→1 scale, starts at -5% drop, maxes at -30%
            price_oversold = max(0, min(1, (-pct_change - 5) / 25))
            # fear_level: 0→1 scale, based on negative effective_sentiment
            fear_level = max(0, min(1, -effective_sentiment / 0.7))
            # Requires BOTH price drop AND fear
            contrarian_raw = math.sqrt(price_oversold * fear_level)
            contrarian_boost = contrarian_raw * 0.6

            score = round(max(-1, min(1, momentum + contrarian_boost)), 2)

            # --- Sub-scores (0-100 scale) for visualization ---
            # Market score: based on 24h change and volume health
            change_24h = market_data.get("change_24h_pct", 0) or 0
            market_score = int(
                max(0, min(100, 50 + change_24h * 2.5))
            )

            # Trend score: based on pct_change and inverse volatility
            vol_penalty = min(30, (volatility or 0) * 5)
            trend_score = int(
                max(0, min(100, 50 + pct_change * 1.5 - vol_penalty))
            )

            # Sentiment score: based on strength and confidence
            sentiment_score = int(
                max(
                    0,
                    min(
                        100,
                        50 + effective_sentiment * 50,
                    ),
                )
            )

            # Contrarian score: map contrarian_raw [0,1] to [0,100]
            contrarian_score = int(
                max(0, min(100, contrarian_raw * 100))
            )

            # Overall score: map composite [-1,1] to [0,100]
            overall_score = int(max(0, min(100, (score + 1) * 50)))

            # Signal classification
            if overall_score >= 60:
                signal = "buy"
            elif overall_score <= 40:
                signal = "sell"
            else:
                signal = "hold"

            return {
                "price": price,
                "pct_change": pct_change,
                "volatility_pct": volatility,
                "trend": trend,
                "sentiment": sentiment,
                "sentiment_strength": round(sentiment_strength, 3),
                "sentiment_confidence": round(sentiment_confidence, 3),
                "effective_sentiment": round(effective_sentiment, 3),
                "alignment": "aligned" if aligned else "divergent",
                "composite_score": score,
                "overall_score": overall_score,
                "market_score": market_score,
                "trend_score": trend_score,
                "sentiment_score": sentiment_score,
                "contrarian_score": contrarian_score,
                "signal": signal,
                "summary": (
                    f"Trend={trend}, Sentiment={sentiment}, "
                    f"Strength={round(sentiment_strength, 3)}, "
                    f"Confidence={round(sentiment_confidence, 3)}, "
                    f"Alignment={'aligned' if aligned else 'divergent'}, "
                    f"Score={score}"
                ),
            }

        except Exception as e:
            return {"error": f"AnalyticsTool failed: {str(e)}"}
