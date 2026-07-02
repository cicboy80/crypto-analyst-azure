import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProgressTracker } from "@/components/ProgressTracker";

describe("ProgressTracker", () => {
  it("renders all 6 steps", () => {
    render(<ProgressTracker activeNodes={[]} completedNodes={[]} />);

    expect(screen.getByText("Market Data")).toBeInTheDocument();
    expect(screen.getByText("Historical Analysis")).toBeInTheDocument();
    expect(screen.getByText("Sentiment Analysis")).toBeInTheDocument();
    expect(screen.getByText("Analytics")).toBeInTheDocument();
    expect(screen.getByText("Strategy")).toBeInTheDocument();
    expect(screen.getByText("Report Generation")).toBeInTheDocument();
  });

  it("marks completed steps", () => {
    render(
      <ProgressTracker
        activeNodes={["sentiment"]}
        completedNodes={["market", "historical"]}
      />
    );

    const marketStep = screen.getByText("Market Data");
    const historicalStep = screen.getByText("Historical Analysis");
    expect(marketStep).toHaveClass("text-emerald-400");
    expect(historicalStep).toHaveClass("text-emerald-400");
  });

  it("highlights active step", () => {
    render(
      <ProgressTracker
        activeNodes={["sentiment"]}
        completedNodes={["market", "historical"]}
      />
    );

    const sentimentStep = screen.getByText("Sentiment Analysis");
    expect(sentimentStep).toHaveClass("text-blue-400");
  });

  it("supports multiple simultaneously active steps", () => {
    render(
      <ProgressTracker
        activeNodes={["market", "historical", "sentiment"]}
        completedNodes={[]}
      />
    );

    expect(screen.getByText("Market Data")).toHaveClass("text-blue-400");
    expect(screen.getByText("Historical Analysis")).toHaveClass(
      "text-blue-400"
    );
    expect(screen.getByText("Sentiment Analysis")).toHaveClass(
      "text-blue-400"
    );
  });

  it("shows pending steps as inactive", () => {
    render(<ProgressTracker activeNodes={["market"]} completedNodes={[]} />);

    const strategyStep = screen.getByText("Strategy");
    expect(strategyStep).toHaveClass("text-slate-600");
  });
});
