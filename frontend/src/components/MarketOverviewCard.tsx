import { memo } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatPrice, formatNumber } from "@/lib/utils";
import type { MarketData } from "@/types";

interface MarketOverviewCardProps {
  data: MarketData | null;
}

export const MarketOverviewCard = memo(function MarketOverviewCard({ data }: MarketOverviewCardProps) {
  if (!data) return null;

  const isPositive = (data.change_24h_pct ?? 0) >= 0;

  const stats = [
    { label: "Market Cap", value: formatNumber(data.market_cap) },
    { label: "24h Volume", value: formatNumber(data.volume_24h) },
    { label: "24h High", value: formatPrice(data.high_24h, data.currency) },
    { label: "24h Low", value: formatPrice(data.low_24h, data.currency) },
    {
      label: "Circulating",
      value: formatNumber(data.circulating_supply),
    },
    {
      label: "Rank",
      value: data.market_cap_rank ? `#${data.market_cap_rank}` : "N/A",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market Overview</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Price + name */}
        <div className="mb-4">
          <div className="flex items-center gap-2">
            {data.image && (
              <img
                src={data.image}
                alt={data.name}
                className="h-6 w-6 rounded-full"
              />
            )}
            <span className="text-sm text-slate-400">
              {data.name ?? data.symbol.toUpperCase()}
            </span>
          </div>
          <div className="mt-1 flex items-baseline gap-3">
            <span className="text-2xl font-bold">
              {formatPrice(data.latest_price, data.currency)}
            </span>
            <Badge variant={isPositive ? "success" : "danger"}>
              {isPositive ? (
                <TrendingUp className="mr-1 h-3 w-3" />
              ) : (
                <TrendingDown className="mr-1 h-3 w-3" />
              )}
              {data.change_24h_pct != null
                ? `${isPositive ? "+" : ""}${data.change_24h_pct.toFixed(2)}%`
                : "N/A"}
            </Badge>
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-3">
          {stats.map((s) => (
            <div key={s.label}>
              <div className="text-[10px] uppercase tracking-wider text-slate-500">
                {s.label}
              </div>
              <div className="text-sm font-medium text-slate-200">
                {s.value}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
});
