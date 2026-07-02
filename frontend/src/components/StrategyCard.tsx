import { memo } from "react";
import { Shield, Clock } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { StrategyData } from "@/types";

interface StrategyCardProps {
  data: StrategyData | null;
}

function actionVariant(action: string) {
  switch (action) {
    case "ACCUMULATE":
      return "success" as const;
    case "REDUCE":
      return "danger" as const;
    default:
      return "warning" as const;
  }
}

function riskColor(risk: string) {
  switch (risk) {
    case "LOW":
      return "text-emerald-400";
    case "HIGH":
      return "text-red-400";
    default:
      return "text-amber-400";
  }
}

export const StrategyCard = memo(function StrategyCard({ data }: StrategyCardProps) {
  if (!data) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Strategy</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Action badge */}
        <div className="mb-4 flex items-center justify-between">
          <Badge variant={actionVariant(data.action)} className="text-sm">
            {data.action}
          </Badge>
          <span className="text-xs text-slate-500">
            Confidence: {Math.round(data.confidence * 100)}%
          </span>
        </div>

        {/* Risk + time */}
        <div className="mb-4 space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <Shield className="h-3.5 w-3.5 text-slate-500" />
            <span className="text-slate-400">Risk:</span>
            <span className={riskColor(data.risk_level)}>
              {data.risk_level}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-3.5 w-3.5 text-slate-500" />
            <span className="text-slate-400">Horizon:</span>
            <span className="text-slate-300">{data.time_horizon}</span>
          </div>
        </div>

        {/* Rationale */}
        {data.rationale && (
          <p className="mb-3 text-xs leading-relaxed text-slate-400">
            {data.rationale}
          </p>
        )}

        {/* Key factors */}
        {data.key_factors && data.key_factors.length > 0 && (
          <div>
            <div className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-slate-500">
              Key Factors
            </div>
            <ul className="space-y-1">
              {data.key_factors.map((f, i) => (
                <li
                  key={i}
                  className="flex items-start gap-1.5 text-xs text-slate-300"
                >
                  <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-blue-500" />
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
});
