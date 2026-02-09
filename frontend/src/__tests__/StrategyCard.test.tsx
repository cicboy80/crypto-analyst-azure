import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StrategyCard } from "@/components/StrategyCard";
import type { StrategyData } from "@/types";

const mockData: StrategyData = {
  action: "ACCUMULATE",
  risk_level: "MEDIUM",
  confidence: 0.75,
  time_horizon: "medium-term (1-3 months)",
  rationale: "Bullish sentiment aligned with upward trend supports accumulation.",
  key_factors: [
    "Strong ETF inflows",
    "Aligned trend and sentiment",
    "Moderate volatility acceptable",
  ],
};

describe("StrategyCard", () => {
  it("returns null when no data", () => {
    const { container } = render(<StrategyCard data={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders action badge", () => {
    render(<StrategyCard data={mockData} />);
    expect(screen.getByText("ACCUMULATE")).toBeInTheDocument();
  });

  it("renders HOLD action", () => {
    render(<StrategyCard data={{ ...mockData, action: "HOLD" }} />);
    expect(screen.getByText("HOLD")).toBeInTheDocument();
  });

  it("renders REDUCE action", () => {
    render(<StrategyCard data={{ ...mockData, action: "REDUCE" }} />);
    expect(screen.getByText("REDUCE")).toBeInTheDocument();
  });

  it("renders risk level", () => {
    render(<StrategyCard data={mockData} />);
    expect(screen.getByText("MEDIUM")).toBeInTheDocument();
  });

  it("renders confidence percentage", () => {
    render(<StrategyCard data={mockData} />);
    expect(screen.getByText("Confidence: 75%")).toBeInTheDocument();
  });

  it("renders time horizon", () => {
    render(<StrategyCard data={mockData} />);
    expect(
      screen.getByText("medium-term (1-3 months)")
    ).toBeInTheDocument();
  });

  it("renders rationale", () => {
    render(<StrategyCard data={mockData} />);
    expect(
      screen.getByText(
        "Bullish sentiment aligned with upward trend supports accumulation."
      )
    ).toBeInTheDocument();
  });

  it("renders key factors", () => {
    render(<StrategyCard data={mockData} />);
    expect(screen.getByText("Strong ETF inflows")).toBeInTheDocument();
    expect(
      screen.getByText("Aligned trend and sentiment")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Moderate volatility acceptable")
    ).toBeInTheDocument();
  });
});
