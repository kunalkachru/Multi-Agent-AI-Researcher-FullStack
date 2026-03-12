import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
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

const VERDICT_DONUT_COLORS: Record<string, string> = {
  verified: "#22c55e",
  partially_verified: "#f59e0b",
  unverified: "#6b7280",
  disputed: "#ef4444",
};

const STRENGTH_COLORS: Record<string, string> = {
  strong: "#22c55e",
  moderate: "#f59e0b",
  weak: "#ef4444",
};

function barColor(score: number): string {
  if (score >= 0.7) return "#22c55e";
  if (score >= 0.5) return "#f59e0b";
  return "#ef4444";
}

function strengthBorderColor(strength: string): string {
  return STRENGTH_COLORS[strength] ?? "#6b7280";
}

export function ClaimsEvidenceViz({ context }: ClaimsEvidenceVizProps) {
  const factResults = (context?.fact_check_results ?? []) as FactCheckResult[];
  const evidenceChains = context?.evidence_chains ?? [];
  const verdictBreakdown = context?.credibility_summary?.verdict_breakdown ?? {};

  if (factResults.length === 0) {
    return (
      <div className="viz-placeholder">
        No claims yet. Start a research run to see fact-check results.
      </div>
    );
  }

  const donutData = Object.entries(verdictBreakdown).map(([verdict, count]) => ({
    name: verdict.replace(/_/g, " "),
    value: count,
    verdict,
  }));
  const totalClaims = donutData.reduce((s, d) => s + d.value, 0);

  return (
    <div className="claims-evidence-viz">
      <h3>Fact-check results</h3>
      <p className="viz-description">
        <strong>See which claims we trust and why.</strong>{" "}
        The donut shows how many claims were verified or disputed, and the list below shows each claim&apos;s score, evidence type, and supporting sources.
      </p>
      {donutData.length > 0 && (
        <div className="claims-verdict-donut">
          <div className="claims-donut-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={donutData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={2}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {donutData.map((entry) => (
                    <Cell key={entry.verdict} fill={VERDICT_DONUT_COLORS[entry.verdict] ?? "#6b7280"} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => [value, "Claims"]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
            <div className="claims-donut-center" aria-hidden="true">
              <span className="claims-donut-center-value">{totalClaims}</span>
              <span className="claims-donut-center-label">Claims</span>
            </div>
          </div>
        </div>
      )}
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
                  Score: {score.toFixed(2)} | {r.evidence_type ?? "—"} | {r.supporting_sources ?? 0} supporting source(s)
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
        <details className="evidence-chains" open={false}>
          <summary>🔗 Evidence Chains</summary>
          <div className="evidence-chains-list">
            {evidenceChains.slice(0, 6).map((chain, i) => {
              const strength = String(chain.strength ?? "unknown");
              const borderColor = strengthBorderColor(strength);
              return (
                <div
                  key={i}
                  className="evidence-chain-item"
                  style={{ borderLeftColor: borderColor }}
                >
                  <strong>{String(chain.claim ?? "").slice(0, 120)}</strong>
                  <div className="evidence-chain-meta">
                    📎 Source: <code>{chain.source_id ?? "?"}</code> | Confidence: {chain.confidence ?? 0} | Type: {chain.evidence_type ?? "—"} | Strength: <span style={{ color: borderColor }}>{strength}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </details>
      )}
    </div>
  );
}
