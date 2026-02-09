import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { AnalyticsData } from "@/types";

interface AnalyticsCardProps {
  data: AnalyticsData | null;
}

function signalVariant(signal: string) {
  switch (signal) {
    case "buy":
      return "success" as const;
    case "sell":
      return "danger" as const;
    default:
      return "warning" as const;
  }
}

function scoreColor(value: number): string {
  if (value >= 60) return "bg-emerald-500";
  if (value >= 40) return "bg-amber-500";
  return "bg-red-500";
}

export function AnalyticsCard({ data }: AnalyticsCardProps) {
  if (!data) return null;

  const subScores = [
    { label: "Market Score", value: data.market_score },
    { label: "Trend Score", value: data.trend_score },
    { label: "Sentiment Score", value: data.sentiment_score },
    { label: "Contrarian Score", value: data.contrarian_score, color: "bg-violet-500" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Analytics</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Overall score */}
        <div className="mb-4 flex items-center justify-between">
          <div>
            <span className="text-3xl font-bold">{data.overall_score}</span>
            <span className="text-sm text-slate-500">/100</span>
          </div>
          <Badge variant={signalVariant(data.signal)}>
            {data.signal.toUpperCase()}
          </Badge>
        </div>

        {/* Alignment */}
        <div className="mb-4 text-xs text-slate-400">
          Trend &amp; sentiment are{" "}
          <span
            className={
              data.alignment === "aligned"
                ? "text-emerald-400"
                : "text-amber-400"
            }
          >
            {data.alignment}
          </span>
        </div>

        {/* Sub-score bars */}
        <div className="space-y-3">
          {subScores.map((s) => (
            <div key={s.label}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-slate-400">{s.label}</span>
                <span className="text-slate-300">{s.value}</span>
              </div>
              <Progress
                value={s.value}
                indicatorClassName={"color" in s ? s.color : scoreColor(s.value)}
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
