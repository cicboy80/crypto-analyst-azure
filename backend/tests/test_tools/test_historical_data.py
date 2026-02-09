import responses
import pytest
from app.tools.historical_data_tool import HistoricalDataTool
from tests.conftest import MOCK_COINGECKO_CHART


class TestHistoricalDataTool:
    def setup_method(self):
        self.tool = HistoricalDataTool()

    @responses.activate
    def test_returns_correct_structure(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            json=MOCK_COINGECKO_CHART,
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd", days=7)

        assert result["symbol"] == "bitcoin"
        assert result["currency"] == "usd"
        assert result["days"] == 7
        assert "start_price" in result
        assert "end_price" in result
        assert "pct_change" in result
        assert "volatility_pct" in result
        assert "trend" in result
        assert "price_history" in result

    @responses.activate
    def test_pct_change_calculation(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            json=MOCK_COINGECKO_CHART,
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd", days=7)

        # start=42000, end=45500 → (45500-42000)/42000*100 ≈ 8.33%
        assert result["start_price"] == 42000.0
        assert result["end_price"] == 45500.0
        assert abs(result["pct_change"] - 8.33) < 0.1

    @responses.activate
    def test_trend_upward(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            json=MOCK_COINGECKO_CHART,
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd", days=7)
        assert result["trend"] == "upward"

    @responses.activate
    def test_trend_downward(self):
        chart = {
            "prices": [
                [1704067200000, 50000.0],
                [1704153600000, 48000.0],
                [1704240000000, 46000.0],
            ]
        }
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            json=chart,
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd", days=3)
        assert result["trend"] == "downward"

    @responses.activate
    def test_trend_sideways(self):
        chart = {
            "prices": [
                [1704067200000, 50000.0],
                [1704153600000, 50050.0],
                [1704240000000, 50100.0],
            ]
        }
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            json=chart,
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd", days=3)
        assert result["trend"] == "sideways"

    @responses.activate
    def test_empty_response_returns_error(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            json={"prices": []},
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd", days=7)
        assert "error" in result

    @responses.activate
    def test_single_data_point_returns_error(self):
        chart = {"prices": [[1704067200000, 42000.0]]}
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            json=chart,
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd", days=1)
        assert "error" in result

    @responses.activate
    def test_volatility_computation(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            json=MOCK_COINGECKO_CHART,
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd", days=7)
        assert result["volatility_pct"] > 0
        assert isinstance(result["volatility_pct"], float)

    @responses.activate
    def test_price_history_format(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            json=MOCK_COINGECKO_CHART,
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd", days=7)
        assert len(result["price_history"]) == 7
        assert "date" in result["price_history"][0]
        assert "price" in result["price_history"][0]
