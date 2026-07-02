import json
from unittest.mock import MagicMock, patch

from app.graph.nodes import (
    analytics_node,
    has_fatal_error,
    historical_node,
    market_node,
    report_node,
    strategy_node,
)


def _llm_response(content):
    client = MagicMock()
    client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=content))]
    )
    return client


BASE_STATE = {"crypto_name": "bitcoin", "currency": "usd", "days": 7}


class TestNodeErrorBranches:
    @patch("app.graph.nodes.MarketDataTool")
    def test_market_error_returns_errors_list(self, mock_cls):
        mock_cls.return_value.run.return_value = {"error": "not found"}
        result = market_node(BASE_STATE)
        assert result["errors"] == ["market: not found"]
        assert result["market_data"]["error"] == "not found"

    @patch("app.graph.nodes.MarketDataTool")
    def test_market_success_has_no_errors_key(self, mock_cls):
        mock_cls.return_value.run.return_value = {"latest_price": 100}
        result = market_node(BASE_STATE)
        assert "errors" not in result

    @patch("app.graph.nodes.HistoricalDataTool")
    def test_historical_error_returns_errors_list(self, mock_cls):
        mock_cls.return_value.run.return_value = {"error": "no data"}
        result = historical_node(BASE_STATE)
        assert result["errors"] == ["historical: no data"]

    @patch("app.graph.nodes.AnalyticsTool")
    def test_analytics_error_returns_errors_list(self, mock_cls):
        mock_cls.return_value.run.return_value = {"error": "missing fields"}
        result = analytics_node(BASE_STATE)
        assert result["errors"] == ["analytics: missing fields"]

    @patch("app.graph.nodes.OpenAI")
    def test_strategy_prose_wrapped_json_is_extracted(self, mock_openai_cls):
        strategy = {"action": "ACCUMULATE", "risk_level": "LOW",
                    "confidence": 0.8, "time_horizon": "x",
                    "rationale": "r", "key_factors": []}
        raw = f"Here is the plan:\n{json.dumps(strategy)}\nHope that helps!"
        mock_openai_cls.return_value = _llm_response(raw)

        result = strategy_node(BASE_STATE)
        assert result["strategy_data"]["action"] == "ACCUMULATE"
        assert "errors" not in result

    @patch("app.graph.nodes.OpenAI")
    def test_strategy_exception_returns_hold_and_error(self, mock_openai_cls):
        client = MagicMock()
        client.chat.completions.create.side_effect = RuntimeError("down")
        mock_openai_cls.return_value = client

        result = strategy_node(BASE_STATE)
        assert result["strategy_data"]["action"] == "HOLD"
        assert result["strategy_data"]["confidence"] == 0.0
        assert result["errors"] == ["strategy: down"]

    @patch("app.graph.nodes.OpenAI")
    def test_report_exception_returns_error_report(self, mock_openai_cls):
        client = MagicMock()
        client.chat.completions.create.side_effect = RuntimeError("down")
        mock_openai_cls.return_value = client

        result = report_node(BASE_STATE)
        assert result["report"].startswith("## Error")
        assert result["errors"] == ["report: down"]


class TestHasFatalError:
    def test_empty_state_is_not_fatal(self):
        assert has_fatal_error({}) is False

    def test_market_error_is_fatal(self):
        assert has_fatal_error({"market_data": {"error": "x"}}) is True

    def test_market_partial_error_with_price_is_not_fatal(self):
        state = {"market_data": {"error": "x", "latest_price": 1}}
        assert has_fatal_error(state) is False

    def test_historical_error_is_fatal(self):
        assert has_fatal_error({"historical_data": {"error": "x"}}) is True

    def test_analytics_error_is_fatal(self):
        assert has_fatal_error({"analytics_data": {"error": "x"}}) is True

    def test_sentiment_never_fatal(self):
        state = {"sentiment_data": {"error": "x"}}
        assert has_fatal_error(state) is False

    def test_healthy_state_is_not_fatal(self):
        state = {
            "market_data": {"latest_price": 1},
            "historical_data": {"price_history": []},
            "analytics_data": {"composite_score": 0.1},
        }
        assert has_fatal_error(state) is False
