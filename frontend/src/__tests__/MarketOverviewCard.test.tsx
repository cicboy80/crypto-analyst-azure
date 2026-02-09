import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MarketOverviewCard } from "@/components/MarketOverviewCard";
import type { MarketData } from "@/types";

const mockData: MarketData = {
  symbol: "bitcoin",
  currency: "usd",
  latest_price: 69114,
  volume_24h: 47530000000,
  market_cap: 1382130000000,
  change_24h_pct: 2.45,
  high_24h: 71850,
  low_24h: 68480,
  circulating_supply: 19500000,
  market_cap_rank: 1,
  name: "Bitcoin",
  image: null,
};

describe("MarketOverviewCard", () => {
  it("returns null when no data", () => {
    const { container } = render(<MarketOverviewCard data={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders price", () => {
    render(<MarketOverviewCard data={mockData} />);
    expect(screen.getByText(/69/)).toBeInTheDocument();
  });

  it("renders coin name", () => {
    render(<MarketOverviewCard data={mockData} />);
    expect(screen.getByText("Bitcoin")).toBeInTheDocument();
  });

  it("renders positive 24h change as green badge", () => {
    render(<MarketOverviewCard data={mockData} />);
    expect(screen.getByText(/\+2\.45%/)).toBeInTheDocument();
  });

  it("renders negative 24h change as red badge", () => {
    const negData = { ...mockData, change_24h_pct: -3.2 };
    render(<MarketOverviewCard data={negData} />);
    expect(screen.getByText(/-3\.20%/)).toBeInTheDocument();
  });

  it("renders stats grid labels", () => {
    render(<MarketOverviewCard data={mockData} />);

    expect(screen.getByText("Market Cap")).toBeInTheDocument();
    expect(screen.getByText("24h Volume")).toBeInTheDocument();
    expect(screen.getByText("24h High")).toBeInTheDocument();
    expect(screen.getByText("24h Low")).toBeInTheDocument();
    expect(screen.getByText("Circulating")).toBeInTheDocument();
    expect(screen.getByText("Rank")).toBeInTheDocument();
  });

  it("renders rank with # prefix", () => {
    render(<MarketOverviewCard data={mockData} />);
    expect(screen.getByText("#1")).toBeInTheDocument();
  });
});
