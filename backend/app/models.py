from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    crypto_name: str = Field(
        default="bitcoin", description="CoinGecko crypto ID"
    )
    currency: str = Field(
        default="usd", description="Fiat currency code"
    )
    days: int = Field(
        default=365, ge=30, le=730, description="Historical lookback days"
    )


class AnalysisStatus(BaseModel):
    thread_id: str
    status: Literal["pending", "running", "completed", "error"]
    current_step: Optional[str] = None
    steps_completed: int = 0
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
