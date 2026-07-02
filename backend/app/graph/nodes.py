import json
import os

from openai import OpenAI

from app.graph.state import AnalysisState
from app.tools.analytics_tool import AnalyticsTool
from app.tools.historical_data_tool import HistoricalDataTool
from app.tools.json_utils import extract_json
from app.tools.market_data import MarketDataTool
from app.tools.sentiment_tool import SentimentTool

NODE_NAMES = [
    "market",
    "historical",
    "sentiment",
    "analytics",
    "strategy",
    "report",
]


def _get_openai_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60.0, max_retries=2)


def has_fatal_error(state: AnalysisState) -> bool:
    """True when a required upstream node failed and LLM stages should be skipped.

    Sentiment failure is non-fatal (the tool falls back to neutral)."""
    market = state.get("market_data") or {}
    historical = state.get("historical_data") or {}
    analytics = state.get("analytics_data") or {}
    return (
        ("error" in market and "latest_price" not in market)
        or ("error" in historical and "price_history" not in historical)
        or ("error" in analytics and "composite_score" not in analytics)
    )


# ── Node 1: Market Data ──────────────────────────────────────────────

def market_node(state: AnalysisState) -> dict:
    tool = MarketDataTool()
    result = tool.run(
        symbol=state["crypto_name"],
        currency=state["currency"],
    )

    if "error" in result and "latest_price" not in result:
        return {"market_data": result, "errors": [f"market: {result['error']}"]}

    return {"market_data": result}


# ── Node 2: Historical Data ──────────────────────────────────────────

def historical_node(state: AnalysisState) -> dict:
    tool = HistoricalDataTool()
    result = tool.run(
        symbol=state["crypto_name"],
        currency=state["currency"],
        days=state["days"],
    )

    if "error" in result and "price_history" not in result:
        return {"historical_data": result, "errors": [f"historical: {result['error']}"]}

    return {"historical_data": result}


# ── Node 3: Sentiment Analysis ───────────────────────────────────────

def sentiment_node(state: AnalysisState) -> dict:
    tool = SentimentTool()
    result = tool.run(query=state["crypto_name"])
    return {"sentiment_data": result}


# ── Node 4: Analytics ────────────────────────────────────────────────

def analytics_node(state: AnalysisState) -> dict:
    tool = AnalyticsTool()
    result = tool.run(
        market_data=state.get("market_data", {}),
        historical_data=state.get("historical_data", {}),
        sentiment_data=state.get("sentiment_data", {}),
    )

    if "error" in result and "composite_score" not in result:
        return {"analytics_data": result, "errors": [f"analytics: {result['error']}"]}

    return {"analytics_data": result}


# ── Node 5: Strategy ─────────────────────────────────────────────────

def strategy_node(state: AnalysisState) -> dict:
    client = _get_openai_client()

    context = {
        "market_data": state.get("market_data", {}),
        "historical_data": {
            k: v
            for k, v in (state.get("historical_data") or {}).items()
            if k != "price_history"
        },
        "sentiment_data": state.get("sentiment_data", {}),
        "analytics_data": state.get("analytics_data", {}),
    }

    prompt = f"""Based on the following structured analytics for {state['crypto_name']},
produce an actionable trading stance.

Data:
{json.dumps(context, indent=2, default=str)}

Return STRICT JSON ONLY in this format:
{{
  "action": "ACCUMULATE" | "HOLD" | "REDUCE",
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "confidence": number (0.0 to 1.0),
  "time_horizon": "short-term (1-4 weeks)" | "medium-term (1-3 months)" | "long-term (3-6 months)",
  "rationale": "brief explanation of the trading stance",
  "key_factors": ["factor1", "factor2", "factor3"]
}}

Rules:
- Integrate sentiment, volatility, risk, opportunity, and alignment.
- If contrarian_score is high (≥50), this indicates oversold conditions with
  extreme fear — weigh toward HOLD or ACCUMULATE rather than REDUCE, as it
  signals a potential mean-reversion opportunity.
- Be specific about risk guidance.
- JSON only, no extra text."""

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a crypto strategist experienced in forming actionable plans. "
                        "Return ONLY valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        raw = completion.choices[0].message.content.strip()
        strategy = extract_json(raw)

        return {"strategy_data": strategy}

    except Exception as e:
        return {
            "strategy_data": {
                "action": "HOLD",
                "risk_level": "HIGH",
                "confidence": 0.0,
                "time_horizon": "unknown",
                "rationale": f"Strategy generation failed: {str(e)}",
                "key_factors": [],
            },
            "errors": [f"strategy: {e}"],
        }


# ── Node 6: Report Generation ────────────────────────────────────────

def report_node(state: AnalysisState) -> dict:
    client = _get_openai_client()

    context = {
        "crypto_name": state["crypto_name"],
        "currency": state["currency"],
        "market_data": state.get("market_data", {}),
        "historical_data": {
            k: v
            for k, v in (state.get("historical_data") or {}).items()
            if k != "price_history"
        },
        "sentiment_data": state.get("sentiment_data", {}),
        "analytics_data": state.get("analytics_data", {}),
        "strategy_data": state.get("strategy_data", {}),
    }

    prompt = f"""Using the outputs from all analysis agents below, write a cohesive, high-quality market report
in Markdown format. Each section must be written as narrative paragraphs, not bullet or numbered lists.
You must synthesize insights, explain context, and avoid repeating raw field names.

Data:
{json.dumps(context, indent=2, default=str)}

Required sections with H2 Markdown headings (##):

## Market Overview
Explain current price, recent movement, and key context in paragraph form.

## Historical Performance
Summarize recent price trajectory, volatility, and trend using smooth narrative sentences.

## Sentiment Analysis
Describe market sentiment, referencing sentiment sources in prose, not lists.

## Analytical Summary
Interpret composite metrics and explain what they mean for traders.
If the contrarian_score is elevated, discuss potential mean-reversion or
"blood in the streets" buying opportunities alongside the momentum signals.

## Strategy Outlook
Provide clear strategy insights in paragraph format — no bullet points.

## Final Takeaways
Conclude with high-level insights in polished prose.

IMPORTANT: Do NOT output bullet points or lists. Use flowing paragraphs."""

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            temperature=0.4,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior market strategist and financial writer for institutional clients. "
                        "Your writing style is polished, narrative, and insight-driven — not bullet-point lists. "
                        "You blend market data, sentiment, and strategy into clear, flowing paragraphs."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        report_text = completion.choices[0].message.content.strip()
        return {"report": report_text}

    except Exception as e:
        return {
            "report": f"## Error\n\nReport generation failed: {str(e)}",
            "errors": [f"report: {e}"],
        }
