import json
from unittest.mock import MagicMock, patch

from app.graph.pipeline import build_graph
from tests.conftest import MOCK_STRATEGY_LLM


def _mock_openai_response(content):
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=content))
    ]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_completion
    return mock_client


class TestPipeline:
    @patch("app.graph.nodes.SentimentTool")
    @patch("app.graph.nodes.HistoricalDataTool")
    @patch("app.graph.nodes.MarketDataTool")
    @patch("app.graph.nodes.OpenAI")
    def test_full_pipeline_end_to_end(
        self,
        mock_openai_cls,
        mock_market_cls,
        mock_historical_cls,
        mock_sentiment_cls,
        mock_market_data,
        mock_historical_data,
        mock_sentiment_data,
    ):
        # Mock tool instances
        mock_market_cls.return_value.run.return_value = mock_market_data
        mock_historical_cls.return_value.run.return_value = mock_historical_data
        mock_sentiment_cls.return_value.run.return_value = mock_sentiment_data

        # Mock OpenAI for strategy + report nodes
        mock_client = _mock_openai_response(json.dumps(MOCK_STRATEGY_LLM))
        # Second call returns report
        mock_client.chat.completions.create.side_effect = [
            MagicMock(
                choices=[MagicMock(message=MagicMock(content=json.dumps(MOCK_STRATEGY_LLM)))]
            ),
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="## Market Overview\n\nBitcoin is trading at $69,114."
                        )
                    )
                ]
            ),
        ]
        mock_openai_cls.return_value = mock_client

        graph = build_graph()

        input_state = {
            "crypto_name": "bitcoin",
            "currency": "usd",
            "days": 7,
        }

        config = {"configurable": {"thread_id": "test-1"}}
        result = graph.invoke(input_state, config=config)

        # Verify all node outputs are present
        assert result["market_data"] is not None
        assert result["historical_data"] is not None
        assert result["sentiment_data"] is not None
        assert result["analytics_data"] is not None
        assert result["strategy_data"] is not None
        assert result["report"] is not None
        assert isinstance(result["report"], str)
        assert len(result["report"]) > 0

    @patch("app.graph.nodes.SentimentTool")
    @patch("app.graph.nodes.HistoricalDataTool")
    @patch("app.graph.nodes.MarketDataTool")
    @patch("app.graph.nodes.OpenAI")
    def test_market_error_short_circuits_llm_nodes(
        self,
        mock_openai_cls,
        mock_market_cls,
        mock_historical_cls,
        mock_sentiment_cls,
        mock_historical_data,
        mock_sentiment_data,
    ):
        """A failed market fetch must skip the paid strategy/report LLM calls."""
        mock_market_cls.return_value.run.return_value = {"error": "coin not found"}
        mock_historical_cls.return_value.run.return_value = mock_historical_data
        mock_sentiment_cls.return_value.run.return_value = mock_sentiment_data

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        graph = build_graph()
        result = graph.invoke(
            {"crypto_name": "notacoin", "currency": "usd", "days": 7},
        )

        assert "strategy_data" not in result
        assert "report" not in result
        assert any("market: coin not found" in e for e in result["errors"])
        # No LLM call was made (sentiment tool is mocked out entirely)
        mock_client.chat.completions.create.assert_not_called()

    @patch("app.graph.nodes.SentimentTool")
    @patch("app.graph.nodes.HistoricalDataTool")
    @patch("app.graph.nodes.MarketDataTool")
    @patch("app.graph.nodes.OpenAI")
    def test_parallel_branch_errors_merge(
        self,
        mock_openai_cls,
        mock_market_cls,
        mock_historical_cls,
        mock_sentiment_cls,
        mock_sentiment_data,
    ):
        """Errors from concurrently failing branches accumulate via the reducer."""
        mock_market_cls.return_value.run.return_value = {"error": "market down"}
        mock_historical_cls.return_value.run.return_value = {"error": "history down"}
        mock_sentiment_cls.return_value.run.return_value = mock_sentiment_data
        mock_openai_cls.return_value = MagicMock()

        graph = build_graph()
        result = graph.invoke(
            {"crypto_name": "bitcoin", "currency": "usd", "days": 7},
        )

        assert any("market: market down" in e for e in result["errors"])
        assert any("historical: history down" in e for e in result["errors"])

    @patch("app.graph.nodes.SentimentTool")
    @patch("app.graph.nodes.HistoricalDataTool")
    @patch("app.graph.nodes.MarketDataTool")
    @patch("app.graph.nodes.OpenAI")
    def test_strategy_failure_records_error_but_completes(
        self,
        mock_openai_cls,
        mock_market_cls,
        mock_historical_cls,
        mock_sentiment_cls,
        mock_market_data,
        mock_historical_data,
        mock_sentiment_data,
    ):
        """LLM failure in strategy falls back to HOLD and records a non-fatal error."""
        mock_market_cls.return_value.run.return_value = mock_market_data
        mock_historical_cls.return_value.run.return_value = mock_historical_data
        mock_sentiment_cls.return_value.run.return_value = mock_sentiment_data

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            RuntimeError("OpenAI unavailable"),
            MagicMock(
                choices=[MagicMock(message=MagicMock(content="## Report"))]
            ),
        ]
        mock_openai_cls.return_value = mock_client

        graph = build_graph()
        result = graph.invoke(
            {"crypto_name": "bitcoin", "currency": "usd", "days": 7},
        )

        assert result["strategy_data"]["action"] == "HOLD"
        assert result["strategy_data"]["confidence"] == 0.0
        assert any("strategy: OpenAI unavailable" in e for e in result["errors"])
        # Pipeline still finished the report
        assert result["report"] == "## Report"

    @patch("app.graph.nodes.SentimentTool")
    @patch("app.graph.nodes.HistoricalDataTool")
    @patch("app.graph.nodes.MarketDataTool")
    @patch("app.graph.nodes.OpenAI")
    def test_analytics_receives_prior_node_data(
        self,
        mock_openai_cls,
        mock_market_cls,
        mock_historical_cls,
        mock_sentiment_cls,
        mock_market_data,
        mock_historical_data,
        mock_sentiment_data,
    ):
        mock_market_cls.return_value.run.return_value = mock_market_data
        mock_historical_cls.return_value.run.return_value = mock_historical_data
        mock_sentiment_cls.return_value.run.return_value = mock_sentiment_data

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            MagicMock(
                choices=[MagicMock(message=MagicMock(content=json.dumps(MOCK_STRATEGY_LLM)))]
            ),
            MagicMock(
                choices=[MagicMock(message=MagicMock(content="## Report"))]
            ),
        ]
        mock_openai_cls.return_value = mock_client

        graph = build_graph()
        config = {"configurable": {"thread_id": "test-3"}}
        result = graph.invoke(
            {"crypto_name": "bitcoin", "currency": "usd", "days": 7},
            config=config,
        )

        analytics = result["analytics_data"]
        assert "composite_score" in analytics
        assert "overall_score" in analytics
        assert analytics["signal"] in {"buy", "hold", "sell"}
