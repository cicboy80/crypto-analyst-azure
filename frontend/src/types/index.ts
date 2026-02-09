export interface AnalysisRequest {
  crypto_name: string;
  currency: string;
  days: number;
}

export interface MarketData {
  symbol: string;
  currency: string;
  latest_price: number;
  volume_24h: number;
  market_cap: number | null;
  change_24h_pct: number | null;
  high_24h: number | null;
  low_24h: number | null;
  circulating_supply: number | null;
  market_cap_rank: number | null;
  name: string;
  image: string | null;
  error?: string;
}

export interface HistoricalData {
  symbol: string;
  currency: string;
  days: number;
  start_price: number;
  end_price: number;
  pct_change: number;
  volatility_pct: number;
  trend: "upward" | "downward" | "sideways";
  price_history: Array<{ date: string; price: number }>;
  error?: string;
}

export interface SentimentData {
  sentiment: "bullish" | "bearish" | "neutral";
  sentiment_strength: number;
  confidence: number;
  reasoning: string;
  news_headlines: string[];
  themes: string[];
  news_error?: string | null;
}

export interface AnalyticsData {
  price: number;
  pct_change: number;
  volatility_pct: number;
  trend: string;
  sentiment: string;
  sentiment_strength: number;
  sentiment_confidence: number;
  effective_sentiment: number;
  alignment: "aligned" | "divergent";
  composite_score: number;
  overall_score: number;
  market_score: number;
  trend_score: number;
  sentiment_score: number;
  contrarian_score: number;
  signal: "buy" | "hold" | "sell";
  summary: string;
  error?: string;
}

export interface StrategyData {
  action: "ACCUMULATE" | "HOLD" | "REDUCE";
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  confidence: number;
  time_horizon: string;
  rationale: string;
  key_factors: string[];
}

export interface AnalysisState {
  status: "idle" | "running" | "completed" | "error";
  currentStep: string | null;
  stepsCompleted: number;
  threadId: string | null;
  marketData: MarketData | null;
  historicalData: HistoricalData | null;
  sentimentData: SentimentData | null;
  analyticsData: AnalyticsData | null;
  strategyData: StrategyData | null;
  report: string | null;
  error: string | null;
}

export interface SSENodeStartEvent {
  node: string;
  step: number;
  total_steps: number;
}

export interface SSENodeCompleteEvent {
  node: string;
  step: number;
  total_steps: number;
  result: Record<string, unknown>;
}

export interface SSECompleteEvent {
  report: string;
  all_data: {
    market_data: MarketData | null;
    historical_data: HistoricalData | null;
    sentiment_data: SentimentData | null;
    analytics_data: AnalyticsData | null;
    strategy_data: StrategyData | null;
    report: string | null;
  };
}

export interface SSEErrorEvent {
  error: string;
}
