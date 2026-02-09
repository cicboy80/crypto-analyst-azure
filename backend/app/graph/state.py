from typing import TypedDict, Optional


class AnalysisState(TypedDict, total=False):
    # Input parameters
    crypto_name: str
    currency: str
    days: int

    # Node outputs
    market_data: Optional[dict]
    historical_data: Optional[dict]
    sentiment_data: Optional[dict]
    analytics_data: Optional[dict]
    strategy_data: Optional[dict]
    report: Optional[str]

    # Progress tracking
    current_step: str
    error: Optional[str]
