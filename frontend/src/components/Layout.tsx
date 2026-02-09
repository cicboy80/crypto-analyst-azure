import type { ReactNode } from "react";
import { Activity } from "lucide-react";

interface LayoutProps {
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
}

export function Layout({ left, center, right }: LayoutProps) {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-50">
      {/* Top nav */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-[1600px] items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-500" />
            <span className="text-lg font-semibold tracking-tight">
              Crypto Intelligence
            </span>
          </div>
          <span className="text-xs text-slate-500">
            LangGraph + React
          </span>
        </div>
      </header>

      {/* 3-column grid */}
      <main className="mx-auto max-w-[1600px] p-4">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr_320px]">
          {/* Left sidebar */}
          <aside className="space-y-4">{left}</aside>

          {/* Center */}
          <section className="min-w-0 space-y-4">{center}</section>

          {/* Right sidebar */}
          <aside className="space-y-4">{right}</aside>
        </div>
      </main>
    </div>
  );
}
