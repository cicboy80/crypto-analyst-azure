# CLAUDE.md

## Project Overview

LangGraph-based multi-agent cryptocurrency analysis system with a React dashboard frontend, FastAPI backend, Docker containerization, and Azure Container Apps deployment. Migrated from CrewAI + Gradio.

## Commands

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Tests
cd backend && pytest -v
cd frontend && npm run test -- --run

# Lint
cd backend && ruff check app/
cd frontend && npm run lint

# Docker
docker compose up --build
```

## Required Environment Variables

Set in `.env` at the project root:
- `OPENAI_API_KEY` — GPT-4.1 for sentiment analysis, strategy, and report generation
- `SERPER_API_KEY` — Serper search API for fetching crypto news
- `COINGECKO_API_KEY` — CoinGecko market data (optional but recommended)

## Architecture

### Backend (`backend/app/`)

**Entry point**: `main.py` — FastAPI app with CORS, includes analysis + health routers.

**LangGraph Pipeline** (`graph/`):
- `state.py` — `AnalysisState` TypedDict defining the shared state schema
- `nodes.py` — 6 node functions: market, historical, sentiment, analytics, strategy, report
- `pipeline.py` — Builds `StateGraph`, compiles with `MemorySaver` checkpointer

**Tools** (`tools/`):
| Tool | API | Returns |
|------|-----|---------|
| `MarketDataTool` | CoinGecko `/simple/price` + `/coins/{id}` | Price, volume, market cap, 24h high/low, supply, rank |
| `HistoricalDataTool` | CoinGecko `/market_chart` | Price history array, pct_change, volatility, trend |
| `SentimentTool` | Serper + OpenAI GPT-4.1 | Sentiment label, strength, confidence, headlines, themes |
| `AnalyticsTool` | None (computation) | Composite score, sub-scores (market/trend/sentiment 0-100), signal |

**Routers** (`routers/`):
- `POST /api/analysis` — Start analysis, returns thread_id (202)
- `GET /api/analysis/{id}/stream` — SSE endpoint streaming node results
- `GET /api/analysis/{id}` — Polling fallback for current state
- `GET /api/health` — Health check

### Frontend (`frontend/src/`)

**3-column dashboard layout** with dark theme:
- Left: `AnalysisForm` + `ProgressTracker`
- Center: `ReportDisplay` (Markdown + Debug tabs) + `PriceChart` (Recharts)
- Right: `MarketOverviewCard`, `AnalyticsCard`, `SentimentCard`, `StrategyCard`

**SSE data flow**: `useAnalysis` hook opens EventSource, populates per-node state as `node_complete` events arrive, triggering cards to render progressively.

### Key Patterns

- Tools use 10-second HTTP timeouts and return error dicts on failure
- Sentiment tool has multi-layer fallbacks (missing API keys → neutral, bad JSON → substring extraction)
- SSE events carry structured node data (not just progress) so cards populate in real-time
- Historical data's `price_history` array excluded from per-node SSE (sent in final `complete` event)
- Frontend proxy: Vite dev server proxies `/api` → `localhost:8000`; nginx does the same in production

## Deployment

Docker Compose for local development. Azure Container Apps for production:
- Backend: internal ingress, secrets from Key Vault
- Frontend: external ingress with auto-TLS, nginx proxies `/api` to backend
- CI/CD: GitHub Actions with OIDC federation
