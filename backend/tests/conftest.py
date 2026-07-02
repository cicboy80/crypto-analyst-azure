import pytest

from app.services.job_manager import job_manager


@pytest.fixture(autouse=True)
def _clean_job_manager():
    """Keep the module-level job_manager singleton isolated between tests."""
    job_manager.clear()
    yield
    job_manager.clear()


# Mock coin details from CoinGecko /coins/{id}
MOCK_COINGECKO_COIN = {
    "name": "Bitcoin",
    "market_cap_rank": 1,
    "image": {"small": "https://example.com/btc.png"},
    "market_data": {
        "current_price": {"usd": 69114},
        "total_volume": {"usd": 47530000000},
        "market_cap": {"usd": 1382130000000},
        "price_change_percentage_24h_in_currency": {"usd": 2.45},
        "high_24h": {"usd": 71850},
        "low_24h": {"usd": 68480},
        "circulating_supply": 19500000,
    },
}

# Mock historical market chart
MOCK_COINGECKO_CHART = {
    "prices": [
        [1704067200000, 42000.0],  # 2024-01-01
        [1704153600000, 42500.0],
        [1704240000000, 43200.0],
        [1704326400000, 42800.0],
        [1704412800000, 44100.0],
        [1704499200000, 44800.0],
        [1704585600000, 45500.0],
    ]
}

# Mock Serper news response
MOCK_SERPER_NEWS = {
    "news": [
        {"title": "Bitcoin surges past $69K amid ETF optimism"},
        {"title": "Institutional adoption of Bitcoin accelerates"},
        {"title": "Fed rate decision impacts crypto markets"},
        {"title": "Bitcoin mining difficulty reaches all-time high"},
        {"title": "Crypto regulatory clarity emerging in US"},
    ]
}

# Mock OpenAI sentiment response
MOCK_SENTIMENT_LLM = {
    "sentiment": "bullish",
    "sentiment_strength": 0.65,
    "confidence": 0.78,
    "reasoning": "Strong institutional interest and ETF momentum drive positive sentiment.",
    "news_headlines": [
        "Bitcoin surges past $69K amid ETF optimism",
        "Institutional adoption of Bitcoin accelerates",
    ],
    "themes": ["ETF", "institutional adoption", "regulation"],
}

# Mock strategy LLM response
MOCK_STRATEGY_LLM = {
    "action": "ACCUMULATE",
    "risk_level": "MEDIUM",
    "confidence": 0.75,
    "time_horizon": "medium-term (1-3 months)",
    "rationale": "Bullish sentiment aligned with upward trend supports accumulation.",
    "key_factors": [
        "Strong ETF inflows",
        "Aligned trend and sentiment",
        "Moderate volatility acceptable",
    ],
}


@pytest.fixture
def mock_market_data():
    """Pre-built market data dict as returned by MarketDataTool."""
    return {
        "symbol": "bitcoin",
        "currency": "usd",
        "latest_price": 69114,
        "volume_24h": 47530000000,
        "market_cap": 1382130000000,
        "change_24h_pct": 2.45,
        "high_24h": 71850,
        "low_24h": 68480,
        "circulating_supply": 19500000,
        "market_cap_rank": 1,
        "name": "Bitcoin",
        "image": "https://example.com/btc.png",
    }


@pytest.fixture
def mock_historical_data():
    """Pre-built historical data dict as returned by HistoricalDataTool."""
    return {
        "symbol": "bitcoin",
        "currency": "usd",
        "days": 7,
        "start_price": 42000.0,
        "end_price": 45500.0,
        "pct_change": 8.33,
        "volatility_pct": 1.42,
        "trend": "upward",
        "price_history": [
            {"date": "2024-01-01", "price": 42000.0},
            {"date": "2024-01-02", "price": 42500.0},
            {"date": "2024-01-03", "price": 43200.0},
            {"date": "2024-01-04", "price": 42800.0},
            {"date": "2024-01-05", "price": 44100.0},
            {"date": "2024-01-06", "price": 44800.0},
            {"date": "2024-01-07", "price": 45500.0},
        ],
    }


@pytest.fixture
def mock_sentiment_data():
    """Pre-built sentiment data dict as returned by SentimentTool."""
    return {
        "sentiment": "bullish",
        "sentiment_strength": 0.65,
        "confidence": 0.78,
        "reasoning": "Strong institutional interest and ETF momentum.",
        "news_headlines": [
            "Bitcoin surges past $69K amid ETF optimism",
            "Institutional adoption of Bitcoin accelerates",
        ],
        "themes": ["ETF", "institutional adoption", "regulation"],
        "news_error": None,
    }
