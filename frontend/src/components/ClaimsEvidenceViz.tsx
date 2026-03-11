import type { RunContextDTO } from "../api/client";
import type { FactCheckResult } from "../api/client";

interface ClaimsEvidenceVizProps {
  context: RunContextDTO["data"] | null;
}

const VERDICT_ICONS: Record<string, string> = {
  verified: "✅",
  partially_verified: "🟡",
  unverified: "❓",
  disputed: "⚠️",
};

function barColor(score: number): string {
  if (score >= 0.7) return "#22c55e";
  if (score >= 0.5) return "#f59e0b";
  return "#ef4444";
}

export function ClaimsEvidenceViz({ context }: ClaimsEvidenceVizProps) {
  const factResults = (context?.fact_check_results ?? []) as FactCheckResult[];
  const evidenceChains = context?.evidence_chains ?? [];

  if (factResults.length === 0) {
    return (
      <div className="viz-placeholder">
        No claims yet. Start a research run to see fact-check results.
      </div>
    );
  }

  return (
    <div className="claims-evidence-viz">
      <h3>Fact-check results</h3>
      <div className="claims-list">
        {factResults.slice(0, 15).map((r, i) => {
          const verdict = r.verdict ?? "unknown";
          const icon = VERDICT_ICONS[verdict] ?? "❔";
          const score = r.credibility_score ?? 0;
          const claimText = (r.claim ?? "").slice(0, 200);
          const barWidth = Math.round(score * 100);
          return (
            <div
              key={i}
              className="claim-card"
              style={{ borderLeftColor: barColor(score) }}
            >
              <div className="claim-card__header">
                <span className="claim-card__verdict">{icon} {String(verdict).replace(/_/g, " ")}</span>
                <span className="claim-card__meta">
                  Score: {score.toFixed(2)} | {r.evidence_type ?? "—"} | {r.supporting_sources ?? 0} supporting
                </span>
              </div>
              <div className="claim-card__claim">{claimText}</div>
              <div className="claim-card__bar">
                <div
                  className="claim-card__bar-fill"
                  style={{ width: `${barWidth}%`, backgroundColor: barColor(score) }}
                />
              </div>
            </div>
          );
        })}
      </div>
      {evidenceChains.length > 0 && (
        <details className="evidence-chains">
          <summary>Evidence Chains</summary>
          <div className="evidence-chains-list">
            {evidenceChains.slice(0, 6).map((chain, i) => (
              <div key={i} className="evidence-chain-item">
                <strong>{String(chain.claim ?? "").slice(0, 120)}</strong>
                <div className="evidence-chain-meta">
                  Source: <code>{chain.source_id ?? "?"}</code> | Confidence: {chain.confidence ?? 0} | Strength: {chain.strength ?? "—"}
                </div>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
