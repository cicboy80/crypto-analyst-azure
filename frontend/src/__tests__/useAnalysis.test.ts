import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useAnalysis, NODE_NAMES } from "@/hooks/useAnalysis";
import { startAnalysis, createAnalysisStream } from "@/api/client";

vi.mock("@/api/client");

type Listener = (e: MessageEvent) => void;

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  url: string;
  listeners = new Map<string, Listener[]>();
  closed = false;

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  addEventListener(type: string, cb: Listener) {
    const list = this.listeners.get(type) ?? [];
    list.push(cb);
    this.listeners.set(type, list);
  }

  close() {
    this.closed = true;
  }

  emit(type: string, data?: string) {
    for (const cb of this.listeners.get(type) ?? []) {
      cb({ data } as MessageEvent);
    }
  }
}

const REQUEST = { crypto_name: "bitcoin", currency: "usd", days: 30 };

function lastStream(): FakeEventSource {
  return FakeEventSource.instances[FakeEventSource.instances.length - 1];
}

async function startRun(result: ReturnType<typeof renderHook<ReturnType<typeof useAnalysis>, unknown>>["result"]) {
  await act(async () => {
    await result.current.runAnalysis(REQUEST);
  });
  return lastStream();
}

beforeEach(() => {
  FakeEventSource.instances = [];
  vi.mocked(startAnalysis).mockResolvedValue("thread-1");
  vi.mocked(createAnalysisStream).mockImplementation(
    (threadId: string) =>
      new FakeEventSource(`/api/analysis/${threadId}/stream`) as unknown as EventSource
  );
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("useAnalysis", () => {
  it("populates node data and completion sets from SSE events", async () => {
    const { result } = renderHook(() => useAnalysis());
    const es = await startRun(result);

    act(() => {
      es.emit("node_start", JSON.stringify({ node: "market", total_steps: 6 }));
      es.emit("node_start", JSON.stringify({ node: "historical", total_steps: 6 }));
    });
    expect(result.current.state.activeNodes).toEqual(["market", "historical"]);

    act(() => {
      es.emit(
        "node_complete",
        JSON.stringify({
          node: "market",
          completed: 1,
          total_steps: 6,
          result: { latest_price: 100 },
        })
      );
    });

    expect(result.current.state.completedNodes).toEqual(["market"]);
    expect(result.current.state.activeNodes).toEqual(["historical"]);
    expect(result.current.state.marketData).toEqual({ latest_price: 100 });
    expect(result.current.state.status).toBe("running");
  });

  it("completes, backfills historical data, and closes the stream", async () => {
    const { result } = renderHook(() => useAnalysis());
    const es = await startRun(result);

    act(() => {
      es.emit(
        "complete",
        JSON.stringify({
          report: "## Done",
          all_data: {
            historical_data: { price_history: [{ date: "d", price: 1 }] },
          },
          errors: ["strategy: fallback used"],
        })
      );
    });

    expect(result.current.state.status).toBe("completed");
    expect(result.current.state.report).toBe("## Done");
    expect(result.current.state.completedNodes).toEqual(NODE_NAMES);
    expect(result.current.state.warnings).toEqual(["strategy: fallback used"]);
    expect(result.current.state.historicalData?.price_history).toHaveLength(1);
    expect(es.closed).toBe(true);
  });

  it("ignores malformed JSON frames without corrupting state", async () => {
    const { result } = renderHook(() => useAnalysis());
    const es = await startRun(result);

    act(() => {
      es.emit("node_start", "not-json{{{");
      es.emit("node_complete", "also-not-json");
    });

    expect(result.current.state.status).toBe("running");
    expect(result.current.state.activeNodes).toEqual([]);
    expect(result.current.state.error).toBeNull();
  });

  it("handles a server error frame", async () => {
    const { result } = renderHook(() => useAnalysis());
    const es = await startRun(result);

    act(() => {
      es.emit("error", JSON.stringify({ error: "market: coin not found" }));
    });

    expect(result.current.state.status).toBe("error");
    expect(result.current.state.error).toBe("market: coin not found");
    expect(es.closed).toBe(true);
  });

  it("treats a connection drop mid-run as an error", async () => {
    const { result } = renderHook(() => useAnalysis());
    const es = await startRun(result);

    act(() => {
      es.emit("error", undefined);
    });

    expect(result.current.state.status).toBe("error");
    expect(result.current.state.error).toBe(
      "Connection to analysis server lost"
    );
  });

  it("ignores a connection drop after completion", async () => {
    const { result } = renderHook(() => useAnalysis());
    const es = await startRun(result);

    act(() => {
      es.emit(
        "complete",
        JSON.stringify({ report: "## Done", all_data: {} })
      );
      es.emit("error", undefined);
    });

    expect(result.current.state.status).toBe("completed");
    expect(result.current.state.error).toBeNull();
  });

  it("sets error state when the POST fails", async () => {
    vi.mocked(startAnalysis).mockRejectedValue(new Error("HTTP 500"));
    const { result } = renderHook(() => useAnalysis());

    await act(async () => {
      await result.current.runAnalysis(REQUEST);
    });

    expect(result.current.state.status).toBe("error");
    expect(result.current.state.error).toBe("HTTP 500");
    expect(FakeEventSource.instances).toHaveLength(0);
  });

  it("closes the EventSource on unmount", async () => {
    const { result, unmount } = renderHook(() => useAnalysis());
    const es = await startRun(result);

    unmount();
    expect(es.closed).toBe(true);
  });

  it("abandons a run superseded while its POST is in flight", async () => {
    let resolveFirst!: (id: string) => void;
    vi.mocked(startAnalysis)
      .mockImplementationOnce(
        () => new Promise<string>((resolve) => (resolveFirst = resolve))
      )
      .mockResolvedValueOnce("thread-2");

    const { result } = renderHook(() => useAnalysis());

    let firstRun!: Promise<void>;
    act(() => {
      firstRun = result.current.runAnalysis(REQUEST);
    });
    // Second submit while the first POST is pending
    await act(async () => {
      await result.current.runAnalysis(REQUEST);
    });
    // First POST finally resolves — must NOT open a second stream
    await act(async () => {
      resolveFirst("thread-1");
      await firstRun;
    });

    expect(FakeEventSource.instances).toHaveLength(1);
    expect(FakeEventSource.instances[0].url).toContain("thread-2");
    expect(result.current.state.threadId).toBe("thread-2");
  });

  it("reset clears state and closes the stream", async () => {
    const { result } = renderHook(() => useAnalysis());
    const es = await startRun(result);

    act(() => {
      result.current.reset();
    });

    expect(es.closed).toBe(true);
    expect(result.current.state.status).toBe("idle");
    await waitFor(() =>
      expect(result.current.state.threadId).toBeNull()
    );
  });
});
