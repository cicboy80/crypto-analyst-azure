import json
import responses
import pytest
from unittest.mock import patch, MagicMock

from app.tools.sentiment_tool import SentimentTool
from tests.conftest import MOCK_SERPER_NEWS, MOCK_SENTIMENT_LLM


class TestSentimentTool:
    def setup_method(self):
        self.tool = SentimentTool()

    @responses.activate
    @patch("app.tools.sentiment_tool.OpenAI")
    def test_full_pipeline(self, mock_openai_cls):
        # Mock Serper
        responses.add(
            responses.POST,
            "https://google.serper.dev/news",
            json=MOCK_SERPER_NEWS,
            status=200,
        )

        # Mock OpenAI
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=json.dumps(MOCK_SENTIMENT_LLM)))
        ]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_cls.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            result = self.tool.run(query="bitcoin")

        assert result["sentiment"] == "bullish"
        assert -1.0 <= result["sentiment_strength"] <= 1.0
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["themes"], list)
        assert isinstance(result["news_headlines"], list)

    @patch.dict("os.environ", {"OPENAI_API_KEY": ""})
    def test_missing_openai_key_returns_neutral(self):
        result = self.tool.run(query="bitcoin")
        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 0.0

    @responses.activate
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test", "SERPER_API_KEY": ""})
    def test_missing_serper_key_returns_neutral(self):
        result = self.tool.run(query="bitcoin")
        assert result["sentiment"] == "neutral"
        assert "SERPER_API_KEY" in result.get("reasoning", "")

    @responses.activate
    @patch("app.tools.sentiment_tool.OpenAI")
    def test_bounds_validation(self, mock_openai_cls):
        """Strength and confidence should be clipped to valid ranges."""
        responses.add(
            responses.POST,
            "https://google.serper.dev/news",
            json=MOCK_SERPER_NEWS,
            status=200,
        )

        # LLM returns out-of-bounds values
        bad_response = {
            "sentiment": "bullish",
            "sentiment_strength": 5.0,  # should clip to 1.0
            "confidence": -2.0,  # should clip to 0.0
            "reasoning": "test",
            "news_headlines": ["test"],
            "themes": [],
        }

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=json.dumps(bad_response)))
        ]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_cls.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            result = self.tool.run(query="bitcoin")

        assert result["sentiment_strength"] == 1.0
        assert result["confidence"] == 0.0

    @responses.activate
    @patch("app.tools.sentiment_tool.OpenAI")
    def test_json_extraction_fallback(self, mock_openai_cls):
        """Should extract JSON from text that wraps it."""
        responses.add(
            responses.POST,
            "https://google.serper.dev/news",
            json=MOCK_SERPER_NEWS,
            status=200,
        )

        # LLM returns JSON wrapped in markdown
        raw = f'Here is the analysis:\n```json\n{json.dumps(MOCK_SENTIMENT_LLM)}\n```'

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=raw))
        ]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_cls.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            result = self.tool.run(query="bitcoin")

        assert result["sentiment"] == "bullish"

    @responses.activate
    @patch("app.tools.sentiment_tool.OpenAI")
    def test_invalid_sentiment_defaults_to_neutral(self, mock_openai_cls):
        responses.add(
            responses.POST,
            "https://google.serper.dev/news",
            json=MOCK_SERPER_NEWS,
            status=200,
        )

        bad_response = {
            "sentiment": "very_bullish",  # invalid
            "sentiment_strength": 0.5,
            "confidence": 0.5,
            "reasoning": "test",
            "news_headlines": [],
            "themes": [],
        }

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=json.dumps(bad_response)))
        ]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_cls.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            result = self.tool.run(query="bitcoin")

        assert result["sentiment"] == "neutral"
