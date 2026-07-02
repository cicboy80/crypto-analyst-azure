import copy

import requests
import responses

from app.tools.market_data import MarketDataTool
from tests.conftest import MOCK_COINGECKO_COIN

COIN_URL = "https://api.coingecko.com/api/v3/coins/bitcoin"


class TestMarketDataTool:
    def setup_method(self):
        self.tool = MarketDataTool()

    @responses.activate
    def test_returns_price_and_volume(self):
        responses.add(
            responses.GET, COIN_URL, json=MOCK_COINGECKO_COIN, status=200
        )

        result = self.tool.run(symbol="bitcoin", currency="usd")

        assert result["symbol"] == "bitcoin"
        assert result["currency"] == "usd"
        assert result["latest_price"] == 69114
        assert result["volume_24h"] == 47530000000

    @responses.activate
    def test_returns_extended_fields(self):
        responses.add(
            responses.GET, COIN_URL, json=MOCK_COINGECKO_COIN, status=200
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
    def test_zero_change_is_preserved_not_none(self):
        """A legitimate 0.0 24h change must not be coerced to None."""
        coin = copy.deepcopy(MOCK_COINGECKO_COIN)
        coin["market_data"]["price_change_percentage_24h_in_currency"]["usd"] = 0.0
        responses.add(responses.GET, COIN_URL, json=coin, status=200)

        result = self.tool.run(symbol="bitcoin", currency="usd")
        assert result["change_24h_pct"] == 0.0

    @responses.activate
    def test_missing_change_returns_none(self):
        coin = copy.deepcopy(MOCK_COINGECKO_COIN)
        del coin["market_data"]["price_change_percentage_24h_in_currency"]
        responses.add(responses.GET, COIN_URL, json=coin, status=200)

        result = self.tool.run(symbol="bitcoin", currency="usd")
        assert result["change_24h_pct"] is None

    @responses.activate
    def test_missing_price_returns_error(self):
        coin = copy.deepcopy(MOCK_COINGECKO_COIN)
        coin["market_data"]["current_price"] = {}
        responses.add(responses.GET, COIN_URL, json=coin, status=200)

        result = self.tool.run(symbol="bitcoin", currency="usd")
        assert "error" in result

    @responses.activate
    def test_timeout_returns_error(self):
        responses.add(
            responses.GET, COIN_URL, body=requests.Timeout("timed out")
        )

        result = self.tool.run(symbol="bitcoin", currency="usd")
        assert "error" in result
        assert "failed" in result["error"].lower()

    @responses.activate
    def test_connection_error_returns_error(self):
        responses.add(
            responses.GET, COIN_URL, body=ConnectionError("refused")
        )

        result = self.tool.run(symbol="bitcoin", currency="usd")
        assert "error" in result

    @responses.activate
    def test_bad_response_returns_error(self):
        responses.add(responses.GET, COIN_URL, status=500)

        result = self.tool.run(symbol="bitcoin", currency="usd")
        assert "error" in result
