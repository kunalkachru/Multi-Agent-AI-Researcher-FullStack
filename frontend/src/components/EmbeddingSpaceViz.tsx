import { useMemo, useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, Legend, ResponsiveContainer, Cell } from "recharts";
import { PCA } from "ml-pca";
import type { RunContextDTO } from "../api/client";
import type { RetrievedChunk } from "../api/client";

interface EmbeddingSpaceVizProps {
  context: RunContextDTO["data"] | null;
}

function corpusScoreToColor(score: number): string {
  const t = Math.max(0, Math.min(1, score));
  const r = Math.round(147 + (29 - 147) * t);
  const g = Math.round(197 + (78 - 197) * t);
  const b = Math.round(253 + (212 - 253) * t);
  return `rgb(${r},${g},${b})`;
}

interface Point {
  x: number;
  y: number;
  z?: number;
  type: "query" | "web" | "corpus";
  label: string;
  score?: number;
  text?: string;
  id?: string;
  url?: string;
}

export function EmbeddingSpaceViz({ context }: EmbeddingSpaceVizProps) {
  const [selected, setSelected] = useState<Point | null>(null);

  const { points, variance } = useMemo(() => {
    const queryEmb = context?.query_embedding;
    const chunks = context?.retrieved_chunks ?? [];
    const withEmbedding = chunks.filter((c): c is RetrievedChunk => !!c.embedding && Array.isArray(c.embedding));
    if (!queryEmb?.length || withEmbedding.length === 0) {
      return { points: [] as Point[], variance: [0, 0] as [number, number] };
    }

    const allEmb: number[][] = [queryEmb];
    const types: ("query" | "web" | "corpus")[] = ["query"];
    const labels: string[] = ["Query"];
    const scores: (number | undefined)[] = [undefined];
    const texts: string[] = [context?.query ?? ""];
    const ids: (string | undefined)[] = [undefined];
    const urls: (string | undefined)[] = [undefined];

    for (const c of withEmbedding) {
      allEmb.push(c.embedding!);
      types.push(c.is_web ? "web" : "corpus");
      labels.push(c.metadata?.title ?? c.id ?? "doc");
      scores.push(c.final_score);
      texts.push(c.text?.slice(0, 200) ?? "");
      ids.push(c.id);
      urls.push(c.is_web ? (c.metadata?.url as string | undefined) : undefined);
    }

    const n = allEmb.length;
    const dim = allEmb[0].length;
    const nComp = Math.min(2, n - 1, dim);
    if (nComp < 1) return { points: [] as Point[], variance: [0, 0] as [number, number] };

    let pca: PCA;
    try {
      pca = new PCA(allEmb, { center: true, scale: false });
    } catch {
      return { points: [] as Point[], variance: [0, 0] as [number, number] };
    }

    const explained = pca.getExplainedVariance();
    const variance: [number, number] = [explained[0] ?? 0, explained[1] ?? 0];

    const projected = pca.predict(allEmb, { nComponents: 2 });
    const mat = projected as { to2DArray?: () => number[][]; getRow?: (i: number) => number[]; rows?: number };
    const rows = mat.to2DArray?.() ?? (mat.rows != null && mat.getRow
      ? Array.from({ length: mat.rows }, (_, i) => mat.getRow!(i))
      : []);

    const points: Point[] = rows.map((row, i) => {
      const type = types[i]!;
      const score = scores[i] ?? 0.5;
      const z = type === "query" ? 120 : type === "web" ? Math.max(60, (score ?? 0.5) * 220) : Math.max(50, (score ?? 0.5) * 180);
      return {
        x: row[0] ?? 0,
        y: (row[1] ?? 0),
        z,
        type,
        label: labels[i]!.slice(0, 40),
        score: scores[i],
        text: texts[i],
        id: ids[i],
        url: urls[i],
      };
    });

    return { points, variance };
  }, [context]);

  const queryPoint = points.find((p) => p.type === "query");
  const webPoints = points.filter((p) => p.type === "web");
  const corpusPoints = points.filter((p) => p.type === "corpus");

  const jumpOptions: { label: string; point: Point }[] = [
    ...(queryPoint ? [{ label: "📌 Query", point: queryPoint }] : []),
    ...webPoints.map((p) => ({ label: `🌐 ${p.label}`, point: p })),
    ...corpusPoints.map((p) => ({ label: `📦 ${p.label}`, point: p })),
  ];

  if (points.length === 0) {
    return (
      <div className="viz-placeholder">
        No source map yet. Start a research run to see how your question relates to sources.
      </div>
    );
  }

  return (
    <div className="embedding-space-viz">
      <h3>Your question vs web results vs your documents</h3>
      <div className="embedding-space-chart">
        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart margin={{ top: 16, right: 120, bottom: 24, left: 24 }}>
            <XAxis
              type="number"
              dataKey="x"
              name="PC1"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              label={{ value: `PC1 (${(variance[0] * 100).toFixed(1)}% variance)`, position: "bottom", fill: "#94a3b8" }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="PC2"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              label={{ value: `PC2 (${(variance[1] * 100).toFixed(1)}% variance)`, angle: -90, position: "insideLeft", fill: "#94a3b8" }}
            />
            <ZAxis range={[50, 400]} />
            <Tooltip
              content={({ payload }) => {
                const p = payload?.[0]?.payload as Point | undefined;
                if (!p) return null;
                return (
                  <div className="embedding-tooltip">
                    <strong>{p.type === "query" ? "Query" : p.type === "web" ? "Web" : "Your docs"}</strong>
                    <div>{p.label}</div>
                    {p.score != null && <div>Score: {p.score.toFixed(3)}</div>}
                    {p.text && <div className="embedding-tooltip-text">{p.text.slice(0, 120)}…</div>}
                  </div>
                );
              }}
            />
            <Legend layout="vertical" verticalAlign="middle" align="right" />
            {queryPoint && (
              <Scatter
                name="Query"
                data={[queryPoint]}
                fill="#ef4444"
                shape="star"
                onClick={() => setSelected(queryPoint)}
              />
            )}
            {webPoints.length > 0 && (
              <Scatter
                name="Web Results (Tavily)"
                data={webPoints}
                fill="#22c55e"
                shape="diamond"
                onClick={(p) => setSelected(p as Point)}
              />
            )}
            {corpusPoints.length > 0 && (
              <Scatter
                name="Vector DB Docs"
                data={corpusPoints}
                fill="#38bdf8"
                shape="circle"
                onClick={(p) => setSelected(p as Point)}
              >
                {corpusPoints.map((_, i) => (
                  <Cell key={i} fill={corpusScoreToColor(corpusPoints[i]?.score ?? 0)} fillOpacity={0.85} />
                ))}
              </Scatter>
            )}
          </ScatterChart>
        </ResponsiveContainer>
        <p className="embedding-variance-caption">
          PC1: {(variance[0] * 100).toFixed(1)}% variance, PC2: {(variance[1] * 100).toFixed(1)}% variance
        </p>
      </div>
      {jumpOptions.length > 0 && (
        <div className="embedding-jump-row">
          <label htmlFor="embedding-jump-select" className="embedding-jump-label">Jump to document…</label>
          <select
            id="embedding-jump-select"
            className="embedding-jump-select"
            value={selected ? jumpOptions.findIndex((o) => o.point === selected) : ""}
            onChange={(e) => {
              const idx = Number(e.target.value);
              if (Number.isFinite(idx) && idx >= 0 && jumpOptions[idx]) setSelected(jumpOptions[idx].point);
              else setSelected(null);
            }}
          >
            <option value="">— Click a point or choose document —</option>
            {jumpOptions.map((opt, i) => (
              <option key={i} value={i}>{opt.label}</option>
            ))}
          </select>
        </div>
      )}
      {selected && (
        <div className="embedding-snippet-panel">
          <div className="embedding-snippet-title">
            {selected.type === "query" ? "📌 Query" : selected.type === "web" ? "🌐 Web" : "📦 Vector DB"} · {selected.label}
          </div>
          {selected.score != null && (
            <div className="embedding-snippet-meta">
              Score: {selected.score.toFixed(3)}
              {selected.type === "web" && selected.url && (
                <> | <a href={selected.url} target="_blank" rel="noopener noreferrer" className="embedding-snippet-link">{selected.url.slice(0, 60)}…</a></>
              )}
            </div>
          )}
          {!selected.score && selected.type === "web" && selected.url && (
            <div className="embedding-snippet-meta">
              <a href={selected.url} target="_blank" rel="noopener noreferrer" className="embedding-snippet-link">{selected.url.slice(0, 80)}…</a>
            </div>
          )}
          {selected.text && <div className="embedding-snippet-text">{selected.text}</div>}
          <button type="button" className="embedding-snippet-close" onClick={() => setSelected(null)}>
            Clear selection
          </button>
        </div>
      )}
      <details className="embedding-document-snippets">
        <summary>📋 Document Snippets (click to expand)</summary>
        <DocumentSnippetsList context={context} />
      </details>
    </div>
  );
}

function DocumentSnippetsList({ context }: { context: RunContextDTO["data"] | null }) {
  const chunks = context?.retrieved_chunks ?? [];
  const withEmbedding = chunks.filter((c): c is RetrievedChunk => !!c.embedding && Array.isArray(c.embedding));
  const webChunks = withEmbedding.filter((c) => c.is_web);
  const corpusChunks = withEmbedding.filter((c) => !c.is_web);

  if (webChunks.length === 0 && corpusChunks.length === 0) {
    return <p className="embedding-snippets-empty">No document snippets available.</p>;
  }

  return (
    <div className="embedding-snippets-list">
      {webChunks.length > 0 && (
        <div className="embedding-snippets-group">
          <strong>🌐 Web Sources</strong>
          {webChunks.slice(0, 5).map((chunk, i) => {
            const title = chunk.metadata?.title ?? chunk.id ?? "Web";
            const url = chunk.metadata?.url as string | undefined;
            const score = chunk.final_score ?? 0;
            const text = (chunk.text ?? "").slice(0, 180);
            return (
              <div key={chunk.id ?? i} className="embedding-snippet-row">
                <span className="embedding-snippet-row-score">{score.toFixed(3)}</span>
                <span className="embedding-snippet-row-text">
                  {url ? (
                    <a href={url} target="_blank" rel="noopener noreferrer" className="embedding-snippet-link">🌐 {title}</a>
                  ) : (
                    <>🌐 {title}</>
                  )}
                  : {text}…
                </span>
              </div>
            );
          })}
        </div>
      )}
      {corpusChunks.length > 0 && (
        <div className="embedding-snippets-group">
          <strong>📦 Vector DB Sources</strong>
          {corpusChunks.slice(0, 5).map((chunk, i) => {
            const score = chunk.final_score ?? 0;
            const text = (chunk.text ?? "").slice(0, 180);
            return (
              <div key={chunk.id ?? i} className="embedding-snippet-row">
                <span className="embedding-snippet-row-score">{score.toFixed(3)}</span>
                <span className="embedding-snippet-row-text">📦 <em>{chunk.id ?? "doc"}</em>: {text}…</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
