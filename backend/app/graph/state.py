import operator
from typing import Annotated, Optional, TypedDict


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

    # Accumulated across nodes; list reducer so parallel branches can
    # each report errors without conflicting writes
    errors: Annotated[list[str], operator.add]
