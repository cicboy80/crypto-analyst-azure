import type { AnalysisRequest } from "@/types";

const API_BASE = "/api";

export async function startAnalysis(
  request: AnalysisRequest
): Promise<string> {
  const res = await fetch(`${API_BASE}/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    throw new Error(`Failed to start analysis: ${res.status}`);
  }

  const data = await res.json();
  return data.thread_id;
}

export function createAnalysisStream(threadId: string): EventSource {
  return new EventSource(`${API_BASE}/analysis/${threadId}/stream`);
}
