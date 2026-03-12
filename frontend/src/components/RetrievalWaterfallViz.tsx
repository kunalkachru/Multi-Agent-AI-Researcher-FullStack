import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { RunContextDTO } from "../api/client";

interface RetrievalWaterfallVizProps {
  context: RunContextDTO["data"] | null;
}

const STAGE_COLORS = ["#60a5fa", "#818cf8", "#a78bfa", "#22c55e"];

const SOURCE_COLORS: Record<string, string> = {
  arxiv: "#3b82f6",
  blog: "#f59e0b",
  documentation: "#22c55e",
  news: "#a78bfa",
  "web (Tavily)": "#ec4899",
  web: "#ec4899",
  government: "#14b8a6",
  unknown: "#6b7280",
};

function getSourceColor(name: string): string {
  return SOURCE_COLORS[name] ?? "#6b7280";
}

export function RetrievalWaterfallViz({ context }: RetrievalWaterfallVizProps) {
  const metadata = context?.retrieval_metadata;
  const stageCounts = metadata?.stage_counts;
  const sourceDist = context?.source_distribution ?? {};

  const stages = stageCounts
    ? [
        { name: "Queries Sent", value: stageCounts.queries ?? 0 },
        { name: "Dense Candidates", value: stageCounts.dense_candidates ?? 0 },
        { name: "After Re-ranking", value: stageCounts.after_rerank ?? 0 },
        { name: "Final Chunks", value: stageCounts.final_chunks ?? 0 },
      ].filter((s) => s.value >= 0)
    : [];

  const sourceData = Object.entries(sourceDist).map(([name, count]) => ({ name, count }));

  if (stages.length === 0) {
    return (
      <div className="viz-placeholder">
        No retrieval data yet. Start a research run to see how we narrowed to top sources.
      </div>
    );
  }

  return (
    <div className="retrieval-waterfall-viz">
      <h3>From your queries to final sources</h3>
      <div className="waterfall-chart">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart
            data={stages}
            layout="vertical"
            margin={{ top: 8, right: 24, bottom: 8, left: 120 }}
          >
            <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <YAxis type="category" dataKey="name" width={110} tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <Tooltip
              content={({ payload }) => {
                const p = payload?.[0]?.payload;
                if (!p) return null;
                const total = stages[0]?.value ?? 1;
                const pct = total ? ((p.value / total) * 100).toFixed(0) : "0";
                return (
                  <div className="viz-tooltip">
                    {p.name}: {p.value} ({pct}% of initial)
                  </div>
                );
              }}
            />
            <Bar dataKey="value" name="Count" radius={[0, 6, 6, 0]} label={{ position: "right", fill: "#e2e8f0", fontSize: 11 }}>
              {stages.map((_, i) => (
                <Cell key={i} fill={STAGE_COLORS[i % STAGE_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      {sourceData.length > 0 && (
        <>
          <h4>Source Distribution</h4>
          <div className="source-dist-chart">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={sourceData}
                layout="vertical"
                margin={{ top: 8, right: 48, bottom: 8, left: 80 }}
              >
                <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={76} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <Tooltip content={({ payload }) => payload?.[0] && (
                  <div className="viz-tooltip">
                    {payload[0].payload.name}: {payload[0].value}
                  </div>
                )} />
                <Bar dataKey="count" name="Count" radius={[0, 4, 4, 0]}>
                  {sourceData.map((entry, i) => (
                    <Cell key={entry.name} fill={getSourceColor(entry.name)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
