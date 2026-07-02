import { useState, useCallback, useEffect, useRef } from "react";
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

export const NODE_NAMES = [
  "market",
  "historical",
  "sentiment",
  "analytics",
  "strategy",
  "report",
];

const INITIAL_STATE: AnalysisState = {
  status: "idle",
  activeNodes: [],
  completedNodes: [],
  threadId: null,
  warnings: [],
  marketData: null,
  historicalData: null,
  sentimentData: null,
  analyticsData: null,
  strategyData: null,
  report: null,
  error: null,
};

function safeParse<T>(raw: string): T | null {
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>(INITIAL_STATE);
  const eventSourceRef = useRef<EventSource | null>(null);
  const runIdRef = useRef(0);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  // Close the stream when the consuming component unmounts
  useEffect(() => cleanup, [cleanup]);

  const runAnalysis = useCallback(
    async (request: AnalysisRequest) => {
      const runId = ++runIdRef.current;
      cleanup();

      setState({
        ...INITIAL_STATE,
        status: "running",
      });

      try {
        const threadId = await startAnalysis(request);
        // A newer run started while the POST was in flight — abandon this one
        if (runIdRef.current !== runId) return;

        setState((prev) => ({ ...prev, threadId }));

        const es = createAnalysisStream(threadId);
        eventSourceRef.current = es;

        es.addEventListener("node_start", (e: MessageEvent) => {
          const data = safeParse<SSENodeStartEvent>(e.data);
          if (!data) return;
          setState((prev) => ({
            ...prev,
            activeNodes: prev.activeNodes.includes(data.node)
              ? prev.activeNodes
              : [...prev.activeNodes, data.node],
          }));
        });

        es.addEventListener("node_complete", (e: MessageEvent) => {
          const data = safeParse<SSENodeCompleteEvent>(e.data);
          if (!data) return;

          setState((prev) => {
            const updates: Partial<AnalysisState> = {
              activeNodes: prev.activeNodes.filter((n) => n !== data.node),
              completedNodes: prev.completedNodes.includes(data.node)
                ? prev.completedNodes
                : [...prev.completedNodes, data.node],
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
          const data = safeParse<SSECompleteEvent>(e.data);
          if (!data) return;

          setState((prev) => ({
            ...prev,
            status: "completed",
            report: data.report,
            activeNodes: [],
            completedNodes: NODE_NAMES,
            warnings: data.errors ?? [],
            // Backfill full historical data (with price_history) from the complete event
            historicalData:
              (data.all_data
                ?.historical_data as unknown as HistoricalData) ??
              prev.historicalData,
          }));

          cleanup();
        });

        // Handles both server-sent `event: error` frames (which carry JSON
        // data) and native EventSource connection errors (which don't)
        es.addEventListener("error", (e: Event) => {
          const raw = (e as MessageEvent).data;
          const parsed =
            typeof raw === "string" ? safeParse<SSEErrorEvent>(raw) : null;

          setState((prev) => {
            // A connection drop after normal completion is not an error
            if (!parsed && prev.status === "completed") return prev;
            return {
              ...prev,
              status: "error",
              error: parsed?.error ?? "Connection to analysis server lost",
            };
          });

          cleanup();
        });
      } catch (err) {
        if (runIdRef.current !== runId) return;
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
    runIdRef.current++;
    cleanup();
    setState(INITIAL_STATE);
  }, [cleanup]);

  return { state, runAnalysis, reset };
}
