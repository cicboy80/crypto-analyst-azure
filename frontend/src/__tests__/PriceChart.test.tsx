import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PriceChart } from "@/components/PriceChart";

// Mock ResizeObserver for recharts
class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserver;

describe("PriceChart", () => {
  const mockHistory = [
    { date: "2024-01-01", price: 42000 },
    { date: "2024-01-02", price: 42500 },
    { date: "2024-01-03", price: 43200 },
    { date: "2024-01-04", price: 44100 },
    { date: "2024-01-05", price: 45500 },
  ];

  it("returns null when no data", () => {
    const { container } = render(<PriceChart priceHistory={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null for empty array", () => {
    const { container } = render(<PriceChart priceHistory={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders chart container with data", () => {
    render(<PriceChart priceHistory={mockHistory} />);
    expect(screen.getByText("Price History")).toBeInTheDocument();
  });
});
