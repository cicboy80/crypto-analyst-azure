import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SentimentCard } from "@/components/SentimentCard";
import type { SentimentData } from "@/types";

const mockData: SentimentData = {
  sentiment: "bullish",
  sentiment_strength: 0.65,
  confidence: 0.78,
  reasoning: "Strong ETF momentum.",
  news_headlines: [
    "Bitcoin surges past $69K amid ETF optimism",
    "Institutional adoption of Bitcoin accelerates",
    "Fed rate decision impacts crypto markets",
  ],
  themes: ["ETF", "institutional adoption", "regulation"],
};

describe("SentimentCard", () => {
  it("returns null when no data", () => {
    const { container } = render(<SentimentCard data={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders sentiment label", () => {
    render(<SentimentCard data={mockData} />);
    expect(screen.getByText("BULLISH")).toBeInTheDocument();
  });

  it("renders confidence percentage", () => {
    render(<SentimentCard data={mockData} />);
    expect(screen.getByText("Confidence: 78%")).toBeInTheDocument();
  });

  it("renders headlines", () => {
    render(<SentimentCard data={mockData} />);
    expect(
      screen.getByText("Bitcoin surges past $69K amid ETF optimism")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Institutional adoption of Bitcoin accelerates")
    ).toBeInTheDocument();
  });

  it("renders theme badges", () => {
    render(<SentimentCard data={mockData} />);
    expect(screen.getByText("ETF")).toBeInTheDocument();
    expect(screen.getByText("institutional adoption")).toBeInTheDocument();
    expect(screen.getByText("regulation")).toBeInTheDocument();
  });

  it("renders bearish sentiment", () => {
    const bearish = { ...mockData, sentiment: "bearish" as const };
    render(<SentimentCard data={bearish} />);
    expect(screen.getByText("BEARISH")).toBeInTheDocument();
  });
});
