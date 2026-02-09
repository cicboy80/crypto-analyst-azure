import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AnalysisForm } from "@/components/AnalysisForm";

describe("AnalysisForm", () => {
  const defaultProps = {
    onSubmit: vi.fn(),
    isRunning: false,
    currentStep: null,
    stepsCompleted: 0,
  };

  it("renders form inputs", () => {
    render(<AnalysisForm {...defaultProps} />);

    expect(screen.getByText("Cryptocurrency")).toBeInTheDocument();
    expect(screen.getByText("Display Currency")).toBeInTheDocument();
    expect(screen.getByText("Analysis Period")).toBeInTheDocument();
    expect(screen.getByText("Run Analysis")).toBeInTheDocument();
  });

  it("calls onSubmit with form values", () => {
    const onSubmit = vi.fn();
    render(<AnalysisForm {...defaultProps} onSubmit={onSubmit} />);

    const form = document.querySelector("form")!;
    fireEvent.submit(form);

    expect(onSubmit).toHaveBeenCalledWith({
      crypto_name: "bitcoin",
      currency: "usd",
      days: 365,
    });
  });

  it("disables button when running", () => {
    render(<AnalysisForm {...defaultProps} isRunning={true} />);

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(screen.getByText("Analyzing...")).toBeInTheDocument();
  });

  it("shows progress tracker when running", () => {
    render(
      <AnalysisForm
        {...defaultProps}
        isRunning={true}
        currentStep="market"
        stepsCompleted={0}
      />
    );

    expect(screen.getByText("Market Data")).toBeInTheDocument();
    expect(screen.getByText("Historical Analysis")).toBeInTheDocument();
  });
});
