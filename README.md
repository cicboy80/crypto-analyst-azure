# Crypto Analyst Agent — Azure Edition

LangGraph-powered multi-agent cryptocurrency analysis system with a React dashboard, deployed on Azure Container Apps.

## Overview

Crypto Analyst Agent is a production-oriented, multi-agent analytics system that produces real-time cryptocurrency market intelligence by combining live market data, historical analysis, news-driven sentiment extraction, and LLM-based synthesis.

The system is designed to demonstrate **agentic workflows**, **state-driven orchestration**, and **streaming AI outputs**, rather than single-prompt analysis.

## Design Focus

- Deterministic, state-driven agent orchestration using LangGraph
- Progressive result streaming via Server-Sent Events (SSE)
- Clear separation between data retrieval, analysis, and synthesis
- Resilient external API integration with graceful degradation
- Production-style frontend/backend separation

## Architecture

```
┌─────────────────────────┐       ┌──────────────────────────────┐
│   Frontend (React+Vite) │──SSE──│   Backend (FastAPI)          │
│   shadcn/ui + Tailwind  │       │   LangGraph pipeline         │
│   Served via nginx      │       │   6 nodes, 4 tools           │
│   Port 80               │       │   astream_events() → SSE     │
└─────────────────────────┘       └──────────────────────────────┘
         │                                   │
         └──── Docker Compose / Azure Container Apps ────┘
```

### Agent Pipeline (LangGraph sequential graph)

Each node operates on a typed shared state, progressively enriching the analysis:

```
User Input (crypto name, currency, lookback days)
  → Market Node (CoinGecko)        → live price, volume, market cap, 24h high/low
  → Historical Node (CoinGecko)    → price history, % change, volatility, trend
  → Sentiment Node (Serper + GPT)  → news headlines, sentiment score, confidence
  → Analytics Node (computation)   → composite score, sub-scores, signal
  → Strategy Node (GPT-4.1)        → trading bias, risk guidance, key factors
  → Report Node (GPT-4.1)          → final Markdown narrative report
```

### Frontend Dashboard (3-column layout)

The frontend is designed to surface *intermediate agent outputs* as well as final results, enabling transparency into the agent pipeline.

- **Left sidebar**: Analysis form (crypto, currency, period, submit) + progress stepper
- **Center**: Markdown report (Report/Debug tabs) + price chart (Recharts)
- **Right sidebar**: Market overview, analytics scores, sentiment gauge, strategy card

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- API keys: `OPENAI_API_KEY`, `SERPER_API_KEY`, `COINGECKO_API_KEY` (optional)

### Local Development (no Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env  # Fill in API keys
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev  # http://localhost:5173
```

### Docker (Local)

```bash
cp .env.example .env  # Fill in API keys
docker compose up --build
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

## Testing

```bash
# Backend (41 tests)
cd backend
pip install pytest pytest-asyncio httpx responses
pytest -v

# Frontend (45 tests)
cd frontend
npm run test -- --run
```

## Azure Deployment

### 1. Create Azure Resources

```bash
az group create --name crypto-analyst-rg --location eastus
az acr create --name cryptoanalystacr --resource-group crypto-analyst-rg --sku Basic
az containerapp env create --name crypto-analyst-env --resource-group crypto-analyst-rg --location eastus
```

### 2. Deploy via GitHub Actions

Set these GitHub repository secrets:
- `AZURE_CLIENT_ID` — Service principal client ID
- `AZURE_TENANT_ID` — Azure AD tenant ID
- `AZURE_SUBSCRIPTION_ID` — Azure subscription ID

Push to `main` to trigger deployment via `.github/workflows/deploy.yml`.

### 3. Set API Keys as Container App Secrets

```bash
az containerapp secret set --name crypto-analyst-backend \
  --resource-group crypto-analyst-rg \
  --secrets openai-api-key=<key> serper-api-key=<key> coingecko-api-key=<key>
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | GPT-4.1 access for sentiment, strategy, and report |
| `SERPER_API_KEY` | Yes | Serper search API for crypto news |
| `COINGECKO_API_KEY` | No | CoinGecko API key (recommended for rate limits) |

## Tech Stack

- **Backend**: FastAPI, LangGraph, LangChain, OpenAI, Pydantic
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, Recharts
- **Infrastructure**: Docker, nginx, Azure Container Apps, GitHub Actions

## Intended Audience

This project is intended for engineers interested in:
- Agentic AI systems and multi-step LLM workflows
- Streaming AI applications
- Production deployment of LLM-backed services
- Applied analytics systems beyond prompt-only demos
