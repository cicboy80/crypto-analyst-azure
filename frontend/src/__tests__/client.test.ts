import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { startAnalysis, createAnalysisStream } from "@/api/client";

const server = setupServer(
  http.post("/api/analysis", () =>
    HttpResponse.json({ thread_id: "abc-123", status: "pending" }, { status: 202 })
  )
);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const REQUEST = { crypto_name: "bitcoin", currency: "usd", days: 30 };

describe("startAnalysis", () => {
  it("returns the thread_id from a successful POST", async () => {
    const threadId = await startAnalysis(REQUEST);
    expect(threadId).toBe("abc-123");
  });

  it("sends the request payload as JSON", async () => {
    let body: unknown;
    server.use(
      http.post("/api/analysis", async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ thread_id: "abc-123" }, { status: 202 });
      })
    );

    await startAnalysis(REQUEST);
    expect(body).toEqual(REQUEST);
  });

  it("throws with the status code on a failed POST", async () => {
    server.use(
      http.post("/api/analysis", () => new HttpResponse(null, { status: 500 }))
    );

    await expect(startAnalysis(REQUEST)).rejects.toThrow(
      "Failed to start analysis: 500"
    );
  });
});

describe("createAnalysisStream", () => {
  it("opens an EventSource at the stream URL with no query params", () => {
    const ctor = vi.fn();
    vi.stubGlobal(
      "EventSource",
      class {
        constructor(url: string) {
          ctor(url);
        }
      }
    );

    createAnalysisStream("abc-123");
    expect(ctor).toHaveBeenCalledWith("/api/analysis/abc-123/stream");

    vi.unstubAllGlobals();
  });
});
