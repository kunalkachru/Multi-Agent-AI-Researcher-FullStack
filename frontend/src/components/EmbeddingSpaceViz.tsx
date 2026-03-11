import { useMemo, useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, Legend, ResponsiveContainer, Cell } from "recharts";
import { PCA } from "ml-pca";
import type { RunContextDTO } from "../api/client";
import type { RetrievedChunk } from "../api/client";

interface EmbeddingSpaceVizProps {
  context: RunContextDTO["data"] | null;
}

interface Point {
  x: number;
  y: number;
  type: "query" | "web" | "corpus";
  label: string;
  score?: number;
  text?: string;
  id?: string;
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

    for (const c of withEmbedding) {
      allEmb.push(c.embedding!);
      types.push(c.is_web ? "web" : "corpus");
      labels.push(c.metadata?.title ?? c.id ?? "doc");
      scores.push(c.final_score);
      texts.push(c.text?.slice(0, 200) ?? "");
      ids.push(c.id);
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

    const points: Point[] = rows.map((row, i) => ({
      x: row[0] ?? 0,
      y: (row[1] ?? 0),
      type: types[i]!,
      label: labels[i]!.slice(0, 40),
      score: scores[i],
      text: texts[i],
      id: ids[i],
    }));

    return { points, variance };
  }, [context]);

  const queryPoint = points.find((p) => p.type === "query");
  const webPoints = points.filter((p) => p.type === "web");
  const corpusPoints = points.filter((p) => p.type === "corpus");

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
              label={{ value: "PC1", position: "bottom", fill: "#94a3b8" }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="PC2"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              label={{ value: "PC2", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
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
                name="Web"
                data={webPoints}
                fill="#22c55e"
                shape="diamond"
                onClick={(p) => setSelected(p as Point)}
              />
            )}
            {corpusPoints.length > 0 && (
              <Scatter
                name="Your docs"
                data={corpusPoints}
                fill="#38bdf8"
                shape="circle"
                onClick={(p) => setSelected(p as Point)}
              >
                {corpusPoints.map((_, i) => (
                  <Cell key={i} fill="#38bdf8" fillOpacity={0.6 + (corpusPoints[i]?.score ?? 0) * 0.4} />
                ))}
              </Scatter>
            )}
          </ScatterChart>
        </ResponsiveContainer>
        <p className="embedding-variance-caption">
          PC1: {(variance[0] * 100).toFixed(1)}% variance, PC2: {(variance[1] * 100).toFixed(1)}% variance
        </p>
      </div>
      {selected && (
        <div className="embedding-snippet-panel">
          <div className="embedding-snippet-title">
            {selected.type === "query" ? "Query" : selected.type === "web" ? "Web" : "Your docs"} · {selected.label}
          </div>
          {selected.score != null && <div className="embedding-snippet-meta">Score: {selected.score.toFixed(3)}</div>}
          {selected.text && <div className="embedding-snippet-text">{selected.text}</div>}
          <button type="button" className="embedding-snippet-close" onClick={() => setSelected(null)}>
            Close
          </button>
        </div>
      )}
    </div>
  );
}
