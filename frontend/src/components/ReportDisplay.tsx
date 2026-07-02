import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FileText, Code, Copy, Check } from "lucide-react";
import { memo, useEffect, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

interface ReportDisplayProps {
  report: string | null;
  debugData: Record<string, unknown> | null;
}

export const ReportDisplay = memo(function ReportDisplay({
  report,
  debugData,
}: ReportDisplayProps) {
  const [copied, setCopied] = useState(false);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
    },
    []
  );

  async function handleCopy() {
    if (!report) return;
    try {
      await navigator.clipboard.writeText(report);
    } catch {
      return;
    }
    setCopied(true);
    if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
    copyTimeoutRef.current = setTimeout(() => setCopied(false), 2000);
  }

  if (!report && !debugData) {
    return (
      <Card className="flex min-h-[400px] items-center justify-center">
        <CardContent className="text-center">
          <FileText className="mx-auto mb-3 h-10 w-10 text-slate-700" />
          <p className="text-sm text-slate-500">
            Run an analysis to generate your intelligence report
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-5">
        <Tabs defaultValue="report">
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="report">
                <FileText className="mr-1.5 h-3.5 w-3.5" />
                Report
              </TabsTrigger>
              <TabsTrigger value="debug">
                <Code className="mr-1.5 h-3.5 w-3.5" />
                Debug Data
              </TabsTrigger>
            </TabsList>

            {report && (
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200"
              >
                {copied ? (
                  <Check className="h-3 w-3" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
                {copied ? "Copied" : "Copy"}
              </button>
            )}
          </div>

          <TabsContent value="report">
            {report ? (
              <article className="prose prose-invert prose-sm max-w-none prose-headings:text-blue-400 prose-headings:border-b prose-headings:border-slate-800 prose-headings:pb-2 prose-p:text-slate-300 prose-p:leading-relaxed">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {report}
                </ReactMarkdown>
              </article>
            ) : (
              <p className="text-sm text-slate-500">
                Report is being generated...
              </p>
            )}
          </TabsContent>

          <TabsContent value="debug">
            {debugData ? (
              <pre className="max-h-[600px] overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-300">
                {JSON.stringify(debugData, null, 2)}
              </pre>
            ) : (
              <p className="text-sm text-slate-500">
                No debug data available yet
              </p>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
});
