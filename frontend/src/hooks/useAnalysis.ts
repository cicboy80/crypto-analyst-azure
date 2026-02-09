import { useState, useCallback, useRef } from "react";
import { startAnalysis, createAnalysisStream } from "@/api/client";
import type {
  AnalysisRequest,
  AnalysisState,
  MarketData,
  HistoricalData,
  SentimentData,
  AnalyticsData,
  StrategyData,
  SSENodeStartEvent,
  SSENodeCompleteEvent,
  SSECompleteEvent,
  SSEErrorEvent,
} from "@/types";

const INITIAL_STATE: AnalysisState = {
  status: "idle",
  currentStep: null,
  stepsCompleted: 0,
  threadId: null,
  marketData: null,
  historicalData: null,
  sentimentData: null,
  analyticsData: null,
  strategyData: null,
  report: null,
  error: null,
};

export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>(INITIAL_STATE);
  const eventSourceRef = useRef<EventSource | null>(null);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  const runAnalysis = useCallback(
    async (request: AnalysisRequest) => {
      cleanup();

      setState({
        ...INITIAL_STATE,
        status: "running",
      });

      try {
        const threadId = await startAnalysis(request);
        setState((prev) => ({ ...prev, threadId }));

        const es = createAnalysisStream(threadId, request);
        eventSourceRef.current = es;

        es.addEventListener("node_start", (e: MessageEvent) => {
          const data: SSENodeStartEvent = JSON.parse(e.data);
          setState((prev) => ({
            ...prev,
            currentStep: data.node,
          }));
        });

        es.addEventListener("node_complete", (e: MessageEvent) => {
          const data: SSENodeCompleteEvent = JSON.parse(e.data);

          setState((prev) => {
            const updates: Partial<AnalysisState> = {
              stepsCompleted: data.step,
            };

            switch (data.node) {
              case "market":
                updates.marketData = data.result as unknown as MarketData;
                break;
              case "historical":
                updates.historicalData =
                  data.result as unknown as HistoricalData;
                break;
              case "sentiment":
                updates.sentimentData =
                  data.result as unknown as SentimentData;
                break;
              case "analytics":
                updates.analyticsData =
                  data.result as unknown as AnalyticsData;
                break;
              case "strategy":
                updates.strategyData =
                  data.result as unknown as StrategyData;
                break;
              case "report":
                if (typeof data.result === "string") {
                  updates.report = data.result;
                }
                break;
            }

            return { ...prev, ...updates };
          });
        });

        es.addEventListener("complete", (e: MessageEvent) => {
          const data: SSECompleteEvent = JSON.parse(e.data);

          setState((prev) => ({
            ...prev,
            status: "completed",
            report: data.report,
            stepsCompleted: 6,
            // Backfill full historical data (with price_history) from the complete event
            historicalData:
              (data.all_data
                ?.historical_data as unknown as HistoricalData) ??
              prev.historicalData,
          }));

          cleanup();
        });

        es.addEventListener("error", (e: MessageEvent) => {
          let errorMsg = "Analysis failed";
          try {
            const data: SSEErrorEvent = JSON.parse(e.data);
            errorMsg = data.error;
          } catch {
            // SSE connection error (no JSON body)
          }

          setState((prev) => ({
            ...prev,
            status: "error",
            error: errorMsg,
          }));

          cleanup();
        });

        es.onerror = () => {
          // Only treat as error if we haven't completed
          setState((prev) => {
            if (prev.status === "completed") return prev;
            return {
              ...prev,
              status: "error",
              error: "Connection to analysis server lost",
            };
          });
          cleanup();
        };
      } catch (err) {
        setState((prev) => ({
          ...prev,
          status: "error",
          error: err instanceof Error ? err.message : "Unknown error",
        }));
      }
    },
    [cleanup]
  );

  const reset = useCallback(() => {
    cleanup();
    setState(INITIAL_STATE);
  }, [cleanup]);

  return { state, runAnalysis, reset };
}
