import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ProgressTracker } from "./ProgressTracker";
import type { AnalysisRequest } from "@/types";

const POPULAR_CRYPTOS = [
  { id: "bitcoin", label: "BTC - Bitcoin" },
  { id: "ethereum", label: "ETH - Ethereum" },
  { id: "solana", label: "SOL - Solana" },
  { id: "cardano", label: "ADA - Cardano" },
  { id: "ripple", label: "XRP - Ripple" },
  { id: "polkadot", label: "DOT - Polkadot" },
  { id: "chainlink", label: "LINK - Chainlink" },
  { id: "avalanche-2", label: "AVAX - Avalanche" },
];

const CURRENCIES = [
  { id: "usd", label: "USD" },
  { id: "eur", label: "EUR" },
  { id: "gbp", label: "GBP" },
];

interface AnalysisFormProps {
  onSubmit: (request: AnalysisRequest) => void;
  isRunning: boolean;
  activeNodes: string[];
  completedNodes: string[];
}

export function AnalysisForm({
  onSubmit,
  isRunning,
  activeNodes,
  completedNodes,
}: AnalysisFormProps) {
  const [crypto, setCrypto] = useState("bitcoin");
  const [currency, setCurrency] = useState("usd");
  const [days, setDays] = useState(365);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({ crypto_name: crypto, currency, days });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Crypto selection */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">
              Cryptocurrency
            </label>
            <select
              value={crypto}
              onChange={(e) => setCrypto(e.target.value)}
              disabled={isRunning}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none focus:border-blue-500 disabled:opacity-50"
            >
              {POPULAR_CRYPTOS.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Currency */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">
              Display Currency
            </label>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              disabled={isRunning}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none focus:border-blue-500 disabled:opacity-50"
            >
              {CURRENCIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Days slider */}
          <div>
            <label className="mb-1.5 flex items-center justify-between text-xs font-medium text-slate-400">
              <span>Analysis Period</span>
              <span className="text-slate-300">{days} days</span>
            </label>
            <input
              type="range"
              min={30}
              max={730}
              step={15}
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              disabled={isRunning}
              className="w-full accent-blue-500"
            />
            <div className="mt-1 flex justify-between text-[10px] text-slate-600">
              <span>30d</span>
              <span>1y</span>
              <span>2y</span>
            </div>
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={isRunning}
            aria-label="Run Analysis"
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Search className="h-4 w-4" />
                Run Analysis
              </>
            )}
          </button>
        </form>

        {/* Progress tracker shown during analysis */}
        {isRunning && (
          <div className="mt-4 border-t border-slate-800 pt-4">
            <ProgressTracker
              activeNodes={activeNodes}
              completedNodes={completedNodes}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
