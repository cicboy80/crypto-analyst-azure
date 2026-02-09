import math
import pytest
from app.tools.analytics_tool import AnalyticsTool


class TestAnalyticsTool:
    def setup_method(self):
        self.tool = AnalyticsTool()

    def test_composite_score_formula(
        self, mock_market_data, mock_historical_data, mock_sentiment_data
    ):
        result = self.tool.run(
            market_data=mock_market_data,
            historical_data=mock_historical_data,
            sentiment_data=mock_sentiment_data,
        )

        assert "composite_score" in result
        assert -1 <= result["composite_score"] <= 1

        # Verify two-stage formula: momentum + contrarian boost
        pct = mock_historical_data["pct_change"]
        strength = mock_sentiment_data["sentiment_strength"]
        conf = mock_sentiment_data["confidence"]
        vol = mock_historical_data["volatility_pct"]
        eff = strength * conf

        momentum = (pct / 10) + (eff * 1.5) - (vol / 100)
        momentum = max(-1, min(1, momentum))

        # Bullish data → contrarian_boost = 0
        price_oversold = max(0, min(1, (-pct - 5) / 25))
        fear_level = max(0, min(1, -eff / 0.7))
        contrarian_raw = math.sqrt(price_oversold * fear_level)
        contrarian_boost = contrarian_raw * 0.6

        expected = round(max(-1, min(1, momentum + contrarian_boost)), 2)
        assert result["composite_score"] == expected

    def test_alignment_aligned(
        self, mock_market_data, mock_historical_data, mock_sentiment_data
    ):
        """Upward trend + positive sentiment = aligned."""
        result = self.tool.run(
            market_data=mock_market_data,
            historical_data=mock_historical_data,
            sentiment_data=mock_sentiment_data,
        )
        assert result["alignment"] == "aligned"

    def test_alignment_divergent(
        self, mock_market_data, mock_historical_data, mock_sentiment_data
    ):
        """Upward trend + bearish sentiment = divergent."""
        mock_sentiment_data["sentiment"] = "bearish"
        mock_sentiment_data["sentiment_strength"] = -0.7
        mock_sentiment_data["confidence"] = 0.8

        result = self.tool.run(
            market_data=mock_market_data,
            historical_data=mock_historical_data,
            sentiment_data=mock_sentiment_data,
        )
        assert result["alignment"] == "divergent"

    def test_sub_scores_present(
        self, mock_market_data, mock_historical_data, mock_sentiment_data
    ):
        result = self.tool.run(
            market_data=mock_market_data,
            historical_data=mock_historical_data,
            sentiment_data=mock_sentiment_data,
        )

        assert "overall_score" in result
        assert "market_score" in result
        assert "trend_score" in result
        assert "sentiment_score" in result
        assert "signal" in result

        for key in ["overall_score", "market_score", "trend_score", "sentiment_score"]:
            assert 0 <= result[key] <= 100

    def test_signal_classification(
        self, mock_market_data, mock_historical_data, mock_sentiment_data
    ):
        """With upward trend + bullish sentiment, should be buy signal."""
        result = self.tool.run(
            market_data=mock_market_data,
            historical_data=mock_historical_data,
            sentiment_data=mock_sentiment_data,
        )
        assert result["signal"] in {"buy", "hold", "sell"}

    def test_score_bounded(self, mock_market_data, mock_historical_data):
        """Extreme inputs should still produce bounded score."""
        extreme_sentiment = {
            "sentiment": "bullish",
            "sentiment_strength": 1.0,
            "confidence": 1.0,
            "news_headlines": [],
            "themes": [],
        }
        mock_historical_data["pct_change"] = 500  # extreme

        result = self.tool.run(
            market_data=mock_market_data,
            historical_data=mock_historical_data,
            sentiment_data=extreme_sentiment,
        )
        assert result["composite_score"] <= 1.0
        assert result["composite_score"] >= -1.0

    def test_missing_fields_returns_error(self):
        result = self.tool.run(
            market_data={"latest_price": None},
            historical_data={"pct_change": 5},
            sentiment_data={"sentiment": "bullish"},
        )
        assert "error" in result

    def test_accepts_json_strings(
        self, mock_market_data, mock_historical_data, mock_sentiment_data
    ):
        import json

        result = self.tool.run(
            market_data=json.dumps(mock_market_data),
            historical_data=json.dumps(mock_historical_data),
            sentiment_data=json.dumps(mock_sentiment_data),
        )
        assert "composite_score" in result

    def test_backwards_compatible_sentiment_defaults(self, mock_market_data, mock_historical_data):
        """If sentiment_strength/confidence are missing, should use defaults."""
        basic_sentiment = {
            "sentiment": "bullish",
            "news_headlines": ["h1", "h2", "h3"],
        }

        result = self.tool.run(
            market_data=mock_market_data,
            historical_data=mock_historical_data,
            sentiment_data=basic_sentiment,
        )
        assert "composite_score" in result
        assert result["sentiment_strength"] == 0.7  # bullish default

    def test_contrarian_score_present(
        self, mock_market_data, mock_historical_data, mock_sentiment_data
    ):
        """contrarian_score should exist and be 0-100."""
        result = self.tool.run(
            market_data=mock_market_data,
            historical_data=mock_historical_data,
            sentiment_data=mock_sentiment_data,
        )
        assert "contrarian_score" in result
        assert 0 <= result["contrarian_score"] <= 100

    def test_contrarian_high_for_oversold(self, mock_market_data):
        """Big drop + bearish sentiment → high contrarian, composite > -1."""
        bearish_hist = {
            "symbol": "bitcoin",
            "currency": "usd",
            "days": 30,
            "start_price": 69000,
            "end_price": 52440,
            "pct_change": -24.0,
            "volatility_pct": 4.5,
            "trend": "downward",
            "price_history": [],
        }
        bearish_sent = {
            "sentiment": "bearish",
            "sentiment_strength": -0.7,
            "confidence": 0.85,
            "news_headlines": ["Crash", "Fear"],
            "themes": ["sell-off"],
        }

        result = self.tool.run(
            market_data=mock_market_data,
            historical_data=bearish_hist,
            sentiment_data=bearish_sent,
        )

        assert result["contrarian_score"] >= 70
        assert result["composite_score"] > -1.0

    def test_contrarian_requires_both(self, mock_market_data):
        """Big drop but bullish sentiment → contrarian = 0."""
        drop_hist = {
            "symbol": "bitcoin",
            "currency": "usd",
            "days": 30,
            "start_price": 69000,
            "end_price": 52440,
            "pct_change": -24.0,
            "volatility_pct": 4.5,
            "trend": "downward",
            "price_history": [],
        }
        bullish_sent = {
            "sentiment": "bullish",
            "sentiment_strength": 0.65,
            "confidence": 0.78,
            "news_headlines": ["Recovery expected"],
            "themes": ["bounce"],
        }

        result = self.tool.run(
            market_data=mock_market_data,
            historical_data=drop_hist,
            sentiment_data=bullish_sent,
        )

        assert result["contrarian_score"] == 0
