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
  const { state, runAnalysis } = useAnalysis();

  const debugData =
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
      : null;

  return (
    <Layout
      left={
        <AnalysisForm
          onSubmit={runAnalysis}
          isRunning={state.status === "running"}
          currentStep={state.currentStep}
          stepsCompleted={state.stepsCompleted}
        />
      }
      center={
        <>
          {state.error && (
            <div className="rounded-lg border border-red-900 bg-red-950/50 p-4 text-sm text-red-400">
              {state.error}
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
