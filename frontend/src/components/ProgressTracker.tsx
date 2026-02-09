import { Check, Loader2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS = [
  { key: "market", label: "Market Data" },
  { key: "historical", label: "Historical Analysis" },
  { key: "sentiment", label: "Sentiment Analysis" },
  { key: "analytics", label: "Analytics" },
  { key: "strategy", label: "Strategy" },
  { key: "report", label: "Report Generation" },
];

interface ProgressTrackerProps {
  currentStep: string | null;
  stepsCompleted: number;
}

export function ProgressTracker({
  currentStep,
  stepsCompleted,
}: ProgressTrackerProps) {
  return (
    <div className="space-y-2">
      {STEPS.map((step, i) => {
        const stepNum = i + 1;
        const isCompleted = stepsCompleted >= stepNum;
        const isActive = currentStep === step.key && !isCompleted;

        return (
          <div key={step.key} className="flex items-center gap-2.5">
            <div
              className={cn(
                "flex h-5 w-5 items-center justify-center rounded-full",
                isCompleted && "bg-emerald-600",
                isActive && "bg-blue-600",
                !isCompleted && !isActive && "bg-slate-800"
              )}
            >
              {isCompleted ? (
                <Check className="h-3 w-3 text-white" />
              ) : isActive ? (
                <Loader2 className="h-3 w-3 animate-spin text-white" />
              ) : (
                <Circle className="h-2.5 w-2.5 text-slate-600" />
              )}
            </div>
            <span
              className={cn(
                "text-xs",
                isCompleted && "text-emerald-400",
                isActive && "text-blue-400 font-medium",
                !isCompleted && !isActive && "text-slate-600"
              )}
            >
              {step.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
