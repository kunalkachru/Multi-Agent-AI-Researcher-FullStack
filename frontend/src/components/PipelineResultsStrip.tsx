import type { PipelineStateSummary } from "../api/client";
import type { RunContextDTO } from "../api/client";

interface PipelineResultsStripProps {
  runState: PipelineStateSummary;
  context: RunContextDTO["data"] | null;
}

function MetricCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string | number;
  icon: string;
}) {
  return (
    <div className="metric-card">
      <div className="metric-card__icon">{icon}</div>
      <div className="metric-card__value">{value}</div>
      <div className="metric-card__label">{label}</div>
    </div>
  );
}

export function PipelineResultsStrip({ runState, context }: PipelineResultsStripProps) {
  const meta = context?.retrieval_metadata;
  const totalChunks = meta?.total_chunks ?? 0;
  const claims = context?.claims ?? [];
  const factResults = context?.fact_check_results ?? [];
  const verified = factResults.filter((r) => r.verdict === "verified").length;
  const themes = context?.themes ?? [];

  return (
    <section className="pipeline-results-strip">
      <h2>Run summary</h2>
      <div className="metric-cards">
        <MetricCard
          label="Time elapsed"
          value={`${runState.total_elapsed.toFixed(1)}s`}
          icon="⏱️"
        />
        <MetricCard
          label="Sources used"
          value={String(totalChunks)}
          icon="📄"
        />
        <MetricCard
          label="Claims found"
          value={String(claims.length)}
          icon="📝"
        />
        <MetricCard
          label="Claims verified"
          value={String(verified)}
          icon="✅"
        />
        <MetricCard
          label="Themes identified"
          value={String(themes.length)}
          icon="💡"
        />
      </div>
    </section>
  );
}
