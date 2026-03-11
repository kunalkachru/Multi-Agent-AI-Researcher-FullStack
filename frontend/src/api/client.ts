/**
 * Astraeus 2.0 API client — typed calls for all FastAPI endpoints.
 */

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8765";

function apiUrl(path: string): string {
  const base = API_BASE.replace(/\/$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

async function handleResponse<T>(res: Response, parseJson = true): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    let detail = body;
    try {
      const j = JSON.parse(body);
      if (j.detail) detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      // use body as-is
    }
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  if (!parseJson) return res as unknown as T;
  return res.json();
}

// ─── Types (match API spec / Pydantic) ───────────────────────────────────

export interface HealthResponse {
  status: string;
}

export type AgentState =
  | "not_started"
  | "waiting"
  | "working"
  | "complete"
  | "error";

export interface AgentStatusDTO {
  agent_id: string;
  name: string;
  state: AgentState;
  progress: number;
  elapsed_seconds: number;
  output_summary: string;
  error_message: string;
}

export interface PipelineStateSummary {
  run_id: string;
  query: string;
  llm_model: string;
  is_running: boolean;
  is_complete: boolean;
  has_error: boolean;
  total_elapsed: number;
  agents: AgentStatusDTO[];
}

export interface RetrievedChunk {
  id: string;
  text: string;
  metadata?: { title?: string; url?: string; source?: string; [k: string]: unknown };
  final_score?: number;
  embedding?: number[] | null;
  is_web?: boolean;
}

export interface FactCheckResult {
  verdict?: string;
  claim?: string;
  credibility_score?: number;
  evidence_type?: string;
  source_credibility?: string;
  supporting_sources?: number;
  [k: string]: unknown;
}

export interface RunContextDTO {
  data: {
    query?: string;
    query_embedding?: number[];
    retrieval_metadata?: {
      total_chunks?: number;
      stage_counts?: {
        queries?: number;
        dense_candidates?: number;
        after_rerank?: number;
        final_chunks?: number;
      };
      [k: string]: unknown;
    };
    retrieved_chunks?: RetrievedChunk[];
    source_distribution?: Record<string, number>;
    web_results?: unknown[];
    claims?: unknown[];
    fact_check_results?: FactCheckResult[];
    credibility_summary?: { verdict_breakdown?: Record<string, number>; [k: string]: unknown };
    evidence_chains?: { claim?: string; source_id?: string; strength?: string; confidence?: number; evidence_type?: string; [k: string]: unknown }[];
    themes?: unknown[];
    gaps?: unknown[];
    hypotheses?: unknown[];
    key_insights?: string[];
    report_markdown?: string;
    report_metadata?: Record<string, unknown>;
    llm_usage?: { prompt_tokens?: number; completion_tokens?: number; [k: string]: unknown };
    pipeline_error?: { agent?: string; error?: string; traceback?: string };
  };
}

export interface UploadResult {
  success: number;
  failed: number;
  total_chunks: number;
  errors: string[];
  doc_count: number;
}

export interface EmbeddingModelMeta {
  id: string;
  name: string;
  dimension: number;
  hint: string;
}

export interface LLMModelMeta {
  id: string;
  name: string;
  input_per_1m: number;
  output_per_1m: number;
  hint: string;
}

export interface MetaDTO {
  embedding_model: string;
  embedding_models: EmbeddingModelMeta[];
  embedding_hf_configured: boolean;
  llm_models: LLMModelMeta[];
  doc_count: number;
  tavily_available: boolean;
  tavily_configured: boolean;
  llm_available: boolean;
  llm_configured: boolean;
}

export interface LLMTestResponse {
  ok: boolean;
  detail: string;
}

// ─── API functions ──────────────────────────────────────────────────────

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const url = `${apiUrl("/api/health")}?t=${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const res = await fetch(url, {
    method: "GET",
    signal,
    cache: "no-store",
    credentials: "omit",
    headers: {
      "Cache-Control": "no-cache, no-store, must-revalidate",
      Pragma: "no-cache",
      "X-Health-Check": String(Date.now()),
    },
  });
  return handleResponse<HealthResponse>(res);
}

export type SearchType = "both" | "rag_only" | "web_only";

export interface StartRunParams {
  query: string;
  llm_model?: string | null;
  openrouter_api_key?: string | null;
  tavily_api_key?: string | null;
  search_type?: SearchType | null;
}

export interface TavilyTestResponse {
  ok: boolean;
  detail: string;
}

export async function startRun(params: StartRunParams): Promise<{ run_id: string }> {
  const body: Record<string, unknown> = {
    query: (params.query || "").trim(),
    llm_model: params.llm_model ?? undefined,
    search_type: params.search_type ?? "both",
  };
  if (params.openrouter_api_key?.trim()) {
    body.openrouter_api_key = params.openrouter_api_key.trim();
  }
  if (params.tavily_api_key?.trim()) {
    body.tavily_api_key = params.tavily_api_key.trim();
  }
  const res = await fetch(apiUrl("/api/run"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<{ run_id: string }>(res);
}

export async function testLlmKey(apiKey?: string | null): Promise<LLMTestResponse> {
  const res = await fetch(apiUrl("/api/llm/test"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(apiKey?.trim() ? { api_key: apiKey.trim() } : {}),
  });
  return handleResponse<LLMTestResponse>(res);
}

export async function testTavilyKey(apiKey?: string | null): Promise<TavilyTestResponse> {
  const res = await fetch(apiUrl("/api/tavily/test"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(apiKey?.trim() ? { api_key: apiKey.trim() } : {}),
  });
  return handleResponse<TavilyTestResponse>(res);
}

export async function getRun(runId: string): Promise<PipelineStateSummary> {
  const res = await fetch(apiUrl(`/api/run/${encodeURIComponent(runId)}`));
  return handleResponse<PipelineStateSummary>(res);
}

export async function getRunContext(runId: string): Promise<RunContextDTO> {
  const res = await fetch(apiUrl(`/api/run/${encodeURIComponent(runId)}/context`));
  return handleResponse<RunContextDTO>(res);
}

export async function getReportMarkdown(runId: string): Promise<string> {
  const res = await fetch(apiUrl(`/api/run/${encodeURIComponent(runId)}/report/markdown`));
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || `Failed: ${res.status}`);
  }
  return res.text();
}

export async function getReportPdfBlob(runId: string): Promise<Blob> {
  const res = await fetch(apiUrl(`/api/run/${encodeURIComponent(runId)}/report/pdf`));
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || `Failed: ${res.status}`);
  }
  return res.blob();
}

export async function uploadFiles(files: File[]): Promise<UploadResult> {
  const form = new FormData();
  for (const f of files) {
    form.append("files", f);
  }
  const res = await fetch(apiUrl("/api/uploads"), {
    method: "POST",
    body: form,
  });
  return handleResponse<UploadResult>(res);
}

export async function getMeta(): Promise<MetaDTO> {
  const res = await fetch(apiUrl("/api/meta"));
  return handleResponse<MetaDTO>(res);
}

export interface EmbeddingTestParams {
  model_id?: string | null;
  token?: string | null;
}

export interface EmbeddingTestResponse {
  ok: boolean;
  detail: string;
}

export async function testEmbedding(params?: EmbeddingTestParams | null): Promise<EmbeddingTestResponse> {
  const body: Record<string, string> = {};
  if (params?.model_id?.trim()) body.model_id = params.model_id.trim();
  if (params?.token?.trim()) body.token = params.token.trim();
  const res = await fetch(apiUrl("/api/embedding/test"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<EmbeddingTestResponse>(res);
}

export async function configureEmbedding(modelId: string, token?: string | null): Promise<{ status: string; embedding_model: string }> {
  const body: Record<string, unknown> = { model_id: modelId.trim() };
  if (token?.trim()) body.token = token.trim();
  const res = await fetch(apiUrl("/api/embedding/configure"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<{ status: string; embedding_model: string }>(res);
}
