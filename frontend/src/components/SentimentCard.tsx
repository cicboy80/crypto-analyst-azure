import { memo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { SentimentData } from "@/types";

interface SentimentCardProps {
  data: SentimentData | null;
}

function sentimentVariant(sentiment: string) {
  switch (sentiment) {
    case "bullish":
      return "success" as const;
    case "bearish":
      return "danger" as const;
    default:
      return "warning" as const;
  }
}

export const SentimentCard = memo(function SentimentCard({ data }: SentimentCardProps) {
  if (!data) return null;

  // Map strength from [-1, 1] to [0, 100] for the progress bar
  const strengthPct = Math.round((data.sentiment_strength + 1) * 50);
  const confidencePct = Math.round(data.confidence * 100);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sentiment</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Sentiment label */}
        <div className="mb-4 flex items-center justify-between">
          <Badge variant={sentimentVariant(data.sentiment)}>
            {data.sentiment.toUpperCase()}
          </Badge>
          <span className="text-xs text-slate-500">
            Confidence: {confidencePct}%
          </span>
        </div>

        {/* Strength bar */}
        <div className="mb-4">
          <div className="mb-1 flex justify-between text-xs text-slate-400">
            <span>Bearish</span>
            <span>Strength</span>
            <span>Bullish</span>
          </div>
          <Progress
            value={strengthPct}
            indicatorClassName={
              strengthPct >= 60
                ? "bg-emerald-500"
                : strengthPct <= 40
                  ? "bg-red-500"
                  : "bg-amber-500"
            }
          />
        </div>

        {/* Headlines */}
        {data.news_headlines.length > 0 && (
          <div className="mb-3">
            <div className="mb-2 text-xs font-medium text-slate-400">
              Top Headlines
            </div>
            <ul className="max-h-[120px] space-y-1 overflow-y-auto">
              {data.news_headlines.slice(0, 5).map((h, i) => (
                <li
                  key={i}
                  className="text-xs leading-snug text-slate-300"
                >
                  {h}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Themes */}
        {data.themes.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {data.themes.map((t, i) => (
              <Badge key={i} variant="outline" className="text-[10px]">
                {t}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
});
