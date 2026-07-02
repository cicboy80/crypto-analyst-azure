import { useMemo } from "react";
import { RotateCcw } from "lucide-react";
import { Layout } from "@/components/Layout";
import { AnalysisForm } from "@/components/AnalysisForm";
import { ReportDisplay } from "@/components/ReportDisplay";
import { PriceChart } from "@/components/PriceChart";
import { MarketOverviewCard } from "@/components/MarketOverviewCard";
import { AnalyticsCard } from "@/components/AnalyticsCard";
import { SentimentCard } from "@/components/SentimentCard";
import { StrategyCard } from "@/components/StrategyCard";
import { useAnalysis } from "@/hooks/useAnalysis";

export default function App() {
  const { state, runAnalysis, reset } = useAnalysis();

  const debugData = useMemo(
    () =>
      state.marketData || state.historicalData || state.sentimentData
        ? {
            market: state.marketData,
            historical: state.historicalData
              ? {
                  ...state.historicalData,
                  price_history: `[${state.historicalData.price_history?.length ?? 0} points]`,
                }
              : null,
            sentiment: state.sentimentData,
            analytics: state.analyticsData,
            strategy: state.strategyData,
          }
        : null,
    [
      state.marketData,
      state.historicalData,
      state.sentimentData,
      state.analyticsData,
      state.strategyData,
    ]
  );

  return (
    <Layout
      left={
        <>
          <AnalysisForm
            onSubmit={runAnalysis}
            isRunning={state.status === "running"}
            activeNodes={state.activeNodes}
            completedNodes={state.completedNodes}
          />
          {(state.status === "completed" || state.status === "error") && (
            <button
              onClick={reset}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-800"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              New Analysis
            </button>
          )}
        </>
      }
      center={
        <>
          {state.error && (
            <div className="rounded-lg border border-red-900 bg-red-950/50 p-4 text-sm text-red-400">
              {state.error}
            </div>
          )}
          {state.warnings.length > 0 && (
            <div className="rounded-lg border border-amber-900 bg-amber-950/50 p-4 text-sm text-amber-400">
              {state.warnings.join("; ")}
            </div>
          )}
          <ReportDisplay report={state.report} debugData={debugData} />
          <PriceChart
            priceHistory={state.historicalData?.price_history ?? null}
            currency={state.historicalData?.currency}
          />
        </>
      }
      right={
        <>
          <MarketOverviewCard data={state.marketData} />
          <AnalyticsCard data={state.analyticsData} />
          <SentimentCard data={state.sentimentData} />
          <StrategyCard data={state.strategyData} />
        </>
      }
    />
  );
}
