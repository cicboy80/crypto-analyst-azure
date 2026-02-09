import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AnalyticsCard } from "@/components/AnalyticsCard";
import type { AnalyticsData } from "@/types";

const mockData: AnalyticsData = {
  price: 69114,
  pct_change: 8.33,
  volatility_pct: 1.42,
  trend: "upward",
  sentiment: "bullish",
  sentiment_strength: 0.65,
  sentiment_confidence: 0.78,
  effective_sentiment: 0.507,
  alignment: "aligned",
  composite_score: 0.58,
  overall_score: 79,
  market_score: 56,
  trend_score: 62,
  sentiment_score: 75,
  contrarian_score: 0,
  signal: "buy",
  summary: "Test",
};

describe("AnalyticsCard", () => {
  it("returns null when no data", () => {
    const { container } = render(<AnalyticsCard data={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders overall score", () => {
    render(<AnalyticsCard data={mockData} />);
    expect(screen.getByText("79")).toBeInTheDocument();
    expect(screen.getByText("/100")).toBeInTheDocument();
  });

  it("renders BUY signal badge", () => {
    render(<AnalyticsCard data={mockData} />);
    expect(screen.getByText("BUY")).toBeInTheDocument();
  });

  it("renders SELL signal badge", () => {
    render(<AnalyticsCard data={{ ...mockData, signal: "sell" }} />);
    expect(screen.getByText("SELL")).toBeInTheDocument();
  });

  it("renders HOLD signal badge", () => {
    render(<AnalyticsCard data={{ ...mockData, signal: "hold" }} />);
    expect(screen.getByText("HOLD")).toBeInTheDocument();
  });

  it("renders sub-score labels", () => {
    render(<AnalyticsCard data={mockData} />);

    expect(screen.getByText("Market Score")).toBeInTheDocument();
    expect(screen.getByText("Trend Score")).toBeInTheDocument();
    expect(screen.getByText("Sentiment Score")).toBeInTheDocument();
    expect(screen.getByText("Contrarian Score")).toBeInTheDocument();
  });

  it("renders sub-score values", () => {
    render(<AnalyticsCard data={mockData} />);

    expect(screen.getByText("56")).toBeInTheDocument();
    expect(screen.getByText("62")).toBeInTheDocument();
    expect(screen.getByText("75")).toBeInTheDocument();
  });

  it("shows alignment status", () => {
    render(<AnalyticsCard data={mockData} />);
    expect(screen.getByText("aligned")).toBeInTheDocument();
  });
});
