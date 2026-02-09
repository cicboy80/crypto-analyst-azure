import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReportDisplay } from "@/components/ReportDisplay";

describe("ReportDisplay", () => {
  it("shows placeholder when no data", () => {
    render(<ReportDisplay report={null} debugData={null} />);

    expect(
      screen.getByText("Run an analysis to generate your intelligence report")
    ).toBeInTheDocument();
  });

  it("renders markdown report", () => {
    render(
      <ReportDisplay
        report={"## Market Overview\n\nBitcoin is at $69K."}
        debugData={null}
      />
    );

    // react-markdown in jsdom may render text with escaped newlines in a single element
    // so use a regex matcher to find the content
    const article = document.querySelector("article");
    expect(article).not.toBeNull();
    expect(article!.textContent).toContain("Market Overview");
  });

  it("switches between Report and Debug tabs", async () => {
    const debug = { market: { price: 69000 } };
    render(
      <ReportDisplay report="## Test Report" debugData={debug} />
    );

    // Report tab is active by default
    expect(screen.getByText("Test Report")).toBeInTheDocument();

    // Switch to debug tab
    await userEvent.click(screen.getByText("Debug Data"));
    expect(screen.getByText(/"price": 69000/)).toBeInTheDocument();
  });

  it("shows copy button when report exists", () => {
    render(<ReportDisplay report="## Report" debugData={null} />);

    expect(screen.getByText("Copy")).toBeInTheDocument();
  });
});
