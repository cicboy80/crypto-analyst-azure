import os
import json
import requests
from typing import List, Any, Dict, Optional

from openai import OpenAI


SERPER_API_KEY = os.getenv("SERPER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class SentimentTool:
    """Fetches recent crypto news via Serper and produces aggregated sentiment
    using GPT-4.1."""

    def _fetch_news(
        self, query: str, max_results: int = 12
    ) -> tuple[List[str], Optional[str]]:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return [], "SERPER_API_KEY missing"

        url = "https://google.serper.dev/news"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": f"{query} cryptocurrency", "num": max_results}

        try:
            resp = requests.post(
                url, headers=headers, json=payload, timeout=10
            )
            resp.raise_for_status()
            news_items = resp.json().get("news", []) or []
            titles = [
                n.get("title", "").strip()
                for n in news_items
                if n.get("title")
            ]

            seen, unique = set(), []
            for t in titles:
                if t not in seen:
                    seen.add(t)
                    unique.append(t)

            return unique, None

        except Exception as e:
            return [], f"Serper error: {str(e)}"

    def _analyze_with_llm(
        self, coin: str, headlines: List[str]
    ) -> Dict[str, Any]:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if not headlines:
            return {
                "sentiment": "neutral",
                "sentiment_strength": 0.0,
                "confidence": 0.0,
                "reasoning": "No news available; defaulting to neutral.",
                "news_headlines": [],
                "themes": [],
            }

        headlines_block = "\n".join(
            f"{i+1}. {h}" for i, h in enumerate(headlines)
        )

        prompt = f"""
You are a professional crypto macro-sentiment analyst.

Analyze the following recent news headlines about "{coin}" and determine
aggregate sentiment.

Headlines:
{headlines_block}

Return STRICT JSON ONLY in this format:

{{
  "sentiment": "bullish" | "bearish" | "neutral",
  "sentiment_strength": number,   // -1.0 to +1.0
  "confidence": number,           // 0.0 to 1.0
  "reasoning": "short explanation",
  "news_headlines": [...],
  "themes": [...]
}}

Rules:
- Consider macro context, price action, regulatory tone, adoption, and risk sentiment.
- No extra text. JSON only.
"""

        try:
            completion = client.chat.completions.create(
                model="gpt-4.1",
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": "Return ONLY valid JSON. You are precise.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            raw = completion.choices[0].message.content.strip()

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                start, end = raw.find("{"), raw.rfind("}")
                if start == -1 or end == -1:
                    raise ValueError("No JSON found in model output.")
                parsed = json.loads(raw[start : end + 1])

            sentiment = parsed.get("sentiment", "neutral").lower()
            if sentiment not in {"bullish", "bearish", "neutral"}:
                sentiment = "neutral"

            def clip(val, lo, hi, default):
                try:
                    v = float(val)
                    return max(lo, min(hi, v))
                except (TypeError, ValueError):
                    return default

            strength = clip(
                parsed.get("sentiment_strength"), -1.0, 1.0, 0.0
            )
            confidence = clip(parsed.get("confidence"), 0.0, 1.0, 0.0)

            themes = parsed.get("themes", [])
            if not isinstance(themes, list):
                themes = []

            used = parsed.get("news_headlines", headlines)
            if not isinstance(used, list) or not used:
                used = headlines

            return {
                "sentiment": sentiment,
                "sentiment_strength": strength,
                "confidence": confidence,
                "reasoning": parsed.get("reasoning", ""),
                "news_headlines": used,
                "themes": themes,
            }

        except Exception as e:
            return {
                "sentiment": "neutral",
                "sentiment_strength": 0.0,
                "confidence": 0.0,
                "reasoning": f"LLM sentiment failure: {str(e)}",
                "news_headlines": headlines,
                "themes": [],
            }

    def run(self, query: str = "bitcoin") -> Dict[str, Any]:
        if not os.getenv("OPENAI_API_KEY"):
            return {
                "sentiment": "neutral",
                "sentiment_strength": 0.0,
                "confidence": 0.0,
                "reasoning": "OPENAI_API_KEY missing; neutral fallback.",
                "news_headlines": [],
                "themes": [],
            }

        headlines, news_error = self._fetch_news(query)

        if news_error and not headlines:
            return {
                "sentiment": "neutral",
                "sentiment_strength": 0.0,
                "confidence": 0.0,
                "reasoning": f"No news available: {news_error}",
                "news_headlines": [],
                "themes": [],
            }

        sentiment = self._analyze_with_llm(query, headlines)
        sentiment["news_error"] = news_error
        return sentiment
