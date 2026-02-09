import responses
import pytest
from app.tools.market_data import MarketDataTool
from tests.conftest import MOCK_COINGECKO_PRICE, MOCK_COINGECKO_COIN


class TestMarketDataTool:
    def setup_method(self):
        self.tool = MarketDataTool()

    @responses.activate
    def test_returns_price_and_volume(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/simple/price",
            json=MOCK_COINGECKO_PRICE,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin",
            json=MOCK_COINGECKO_COIN,
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd")

        assert result["symbol"] == "bitcoin"
        assert result["currency"] == "usd"
        assert result["latest_price"] == 69114
        assert result["volume_24h"] == 47530000000

    @responses.activate
    def test_returns_extended_fields(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/simple/price",
            json=MOCK_COINGECKO_PRICE,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin",
            json=MOCK_COINGECKO_COIN,
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd")

        assert result["market_cap"] == 1382130000000
        assert result["change_24h_pct"] == 2.45
        assert result["high_24h"] == 71850
        assert result["low_24h"] == 68480
        assert result["circulating_supply"] == 19500000
        assert result["market_cap_rank"] == 1
        assert result["name"] == "Bitcoin"

    @responses.activate
    def test_missing_symbol_returns_error(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/simple/price",
            json={"notbitcoin": {}},
            status=200,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd")
        assert "error" in result

    @responses.activate
    def test_timeout_returns_error(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/simple/price",
            body=ConnectionError("timeout"),
        )

        result = self.tool.run(symbol="bitcoin", currency="usd")
        assert "error" in result
        assert "failed" in result["error"].lower()

    @responses.activate
    def test_bad_response_returns_error(self):
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/simple/price",
            status=500,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd")
        assert "error" in result

    @responses.activate
    def test_coin_details_failure_still_returns_price(self):
        """If /coins/{id} fails, we still get price + volume."""
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/simple/price",
            json=MOCK_COINGECKO_PRICE,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://api.coingecko.com/api/v3/coins/bitcoin",
            status=500,
        )

        result = self.tool.run(symbol="bitcoin", currency="usd")
        assert result["latest_price"] == 69114
        assert result["high_24h"] is None  # Graceful fallback
