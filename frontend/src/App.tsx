import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  configureEmbedding,
  getHealth,
  getMeta,
  getReportMarkdown,
  getReportPdfBlob,
  getRunContext,
  startRun,
  testEmbedding,
  testLlmKey,
  testTavilyKey,
  uploadFiles,
  type MetaDTO,
  type AgentStatusDTO,
  type AgentState,
  type SearchType,
} from "./api/client";
import { usePipelineRun } from "./api/usePipelineRun";
import { PipelineResultsStrip } from "./components/PipelineResultsStrip";
import { EmbeddingSpaceViz } from "./components/EmbeddingSpaceViz";
import { RetrievalWaterfallViz } from "./components/RetrievalWaterfallViz";
import { ClaimsEvidenceViz } from "./components/ClaimsEvidenceViz";

// Match the 6 Streamlit agents from config.AGENTS
const AGENT_META: Record<
  string,
  { corner: string; subtitle: string; tone: "pink" | "blue" | "purple" | "green" | "amber" | "cyan" }
> = {
  coordinator: {
    corner: "🎯",
    subtitle: "Query Analysis & Expansion",
    tone: "pink",
  },
  retriever: {
    corner: "📋",
    subtitle: "Vector Search & Ranking",
    tone: "blue",
  },
  critical_analysis: {
    corner: "🔍",
    subtitle: "Claims & Contradictions",
    tone: "purple",
  },
  fact_checker: {
    corner: "✓",
    subtitle: "Source Credibility",
    tone: "green",
  },
  insight_generator: {
    corner: "💡",
    subtitle: "Themes & Gaps",
    tone: "amber",
  },
  report_builder: {
    corner: "📄",
    subtitle: "Final Report & Citations",
    tone: "cyan",
  },
};

function stateLabel(s: AgentState): string {
  const map: Record<AgentState, string> = {
    not_started: "Pending",
    waiting: "Waiting",
    working: "Working…",
    complete: "Done",
    error: "Error",
  };
  return map[s] ?? s;
}

function RobotIcon({ idSuffix }: { idSuffix: string }) {
  const faceId = `robotFace-${idSuffix}`;
  const bodyId = `robotBody-${idSuffix}`;
  return (
    <svg
      className="agent-card__robot-icon"
      viewBox="0 0 64 64"
      aria-hidden="true"
      focusable="false"
      style={{ display: "block", flexShrink: 0 }}
    >
      <defs>
        <linearGradient id={faceId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f97316" />
          <stop offset="100%" stopColor="#fb923c" />
        </linearGradient>
        <linearGradient id={bodyId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#0f172a" />
          <stop offset="100%" stopColor="#1f2937" />
        </linearGradient>
      </defs>
      {/* Head shell */}
      <path
        d="M20 10h24c4 0 7 3 7 7v10c0 6.5-5.5 12-19 12s-19-5.5-19-12V17c0-4 3-7 7-7z"
        fill={`url(#${bodyId})`}
        stroke="#38bdf8"
        strokeWidth="1.5"
      />
      {/* Ear pieces */}
      <rect x="10" y="20" width="6" height="12" rx="3" fill="#020617" stroke="#38bdf8" strokeWidth="1" />
      <rect x="48" y="20" width="6" height="12" rx="3" fill="#020617" stroke="#38bdf8" strokeWidth="1" />
      {/* Face window */}
      <rect x="22" y="16" width="20" height="16" rx="6" fill="#020617" stroke="#0ea5e9" strokeWidth="1" />
      {/* Brain glow */}
      <ellipse cx="32" cy="24" rx="9" ry="6" fill={`url(#${faceId})`} opacity="0.9" />
      <path
        d="M25 24c1.5-3 3.5-4 7-4s5.5 1 7 4"
        fill="none"
        stroke="#fed7aa"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
      {/* Body plate */}
      <path
        d="M20 32h24v16c0 4-3.5 7-12 7s-12-3-12-7V32z"
        fill={`url(#${bodyId})`}
        stroke="#38bdf8"
        strokeWidth="1"
      />
      {/* Chest indicator lights */}
      <circle cx="26" cy="38" r="2" fill="#22c55e" />
      <circle cx="32" cy="38" r="2" fill="#eab308" />
      <circle cx="38" cy="38" r="2" fill="#ef4444" />
    </svg>
  );
}

function AgentCard({ agent }: { agent: AgentStatusDTO }) {
  const meta = AGENT_META[agent.agent_id] ?? {
    corner: "✨",
    subtitle: "",
    tone: "blue" as const,
  };
  const label = stateLabel(agent.state);
  const isActive = agent.state === "working" || agent.state === "waiting";
  const isDone = agent.state === "complete";
  const isError = agent.state === "error";

  return (
    <div
      className={`agent-card agent-card--tone-${meta.tone} ${
        isActive ? "agent-card--active" : ""
      } ${isDone ? "agent-card--done" : ""} ${isError ? "agent-card--error" : ""}`}
    >
      <div className="agent-card__avatar">
        <RobotIcon idSuffix={agent.agent_id || agent.name.replace(/\s+/g, "-")} />
        <span className="agent-card__corner">{meta.corner}</span>
      </div>
      <div className="agent-card__body">
        <div className="agent-card__name">{agent.name}</div>
        {meta.subtitle && <div className="agent-card__subtitle">{meta.subtitle}</div>}
        <div className="agent-card__state">
          {isDone && <span className="agent-card__state-dot" aria-hidden />}
          {label}
        </div>
        {agent.elapsed_seconds > 0 && (
          <div className="agent-card__elapsed">
            Execution: {agent.elapsed_seconds.toFixed(1)}s
          </div>
        )}
        {agent.progress > 0 && agent.progress < 1 && (
          <div className="agent-card__progress">
            <div
              className="agent-card__progress-fill"
              style={{ width: `${agent.progress * 100}%` }}
            />
          </div>
        )}
        {agent.output_summary && (
          <div className="agent-card__summary" title={agent.output_summary}>{agent.output_summary}</div>
        )}
        {agent.error_message && (
          <div className="agent-card__error">{agent.error_message}</div>
        )}
      </div>
      {isDone && <div className="agent-card__done-bar" aria-hidden />}
    </div>
  );
}

export const App = () => {
  const [health, setHealth] = useState<string>("Checking API...");
  const [apiError, setApiError] = useState<string | null>(null);
  const [meta, setMeta] = useState<MetaDTO | null>(null);
  const [query, setQuery] = useState("");
  const [llmModel, setLlmModel] = useState<string>("");
  const [runId, setRunId] = useState<string | null>(null);
  const [launchError, setLaunchError] = useState<string | null>(null);
  const [runContext, setRunContext] = useState<Awaited<ReturnType<typeof getRunContext>> | null>(null);
  const [contextRunId, setContextRunId] = useState<string | null>(null);
  const [reportMd, setReportMd] = useState<string | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState<1 | 2 | 3>(1);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [uploadInputKey, setUploadInputKey] = useState(0);
  const [ragTab, setRagTab] = useState<"embedding" | "waterfall" | "claims">("embedding");
  const [mainContentTab, setMainContentTab] = useState<"summary" | "sources">("summary");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchType, setSearchType] = useState<SearchType>("both");
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof window === "undefined") return "dark";
    const stored = localStorage.getItem("theme") as "dark" | "light" | null;
    return stored === "light" || stored === "dark" ? stored : "dark";
  });
  const [sidebarWidth, setSidebarWidth] = useState(260);
  const [isDesktop, setIsDesktop] = useState(
    () => typeof window !== "undefined" && window.innerWidth >= 768
  );
  useEffect(() => {
    const m = window.matchMedia("(min-width: 768px)");
    const handler = () => setIsDesktop(m.matches);
    m.addEventListener("change", handler);
    return () => m.removeEventListener("change", handler);
  }, []);

  useEffect(() => {
    if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }, []);

  const handleSidebarResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = sidebarWidth;
    const onMove = (ev: MouseEvent) => {
      const delta = ev.clientX - startX;
      const minW = 200;
      const maxW = Math.min(520, window.innerWidth * 0.5);
      setSidebarWidth(Math.min(maxW, Math.max(minW, startWidth + delta)));
    };
    const onUp = () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      resizeDragRef.current = null;
    };
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  };
  const [userApiKey, setUserApiKey] = useState("");
  const [llmTestStatus, setLlmTestStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [llmTestMessage, setLlmTestMessage] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("");
  const [embeddingHfToken, setEmbeddingHfToken] = useState("");
  const [embeddingTestStatus, setEmbeddingTestStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [embeddingTestMessage, setEmbeddingTestMessage] = useState("");
  const [userTavilyKey, setUserTavilyKey] = useState("");
  const [tavilyTestStatus, setTavilyTestStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [tavilyTestMessage, setTavilyTestMessage] = useState("");

  const { data: runState, error: runError, isLoading: runLoading, isPolling } = usePipelineRun(runId);

  const lastHealthSuccessAt = useRef<number>(0);
  const uploadingRef = useRef<boolean>(false); // ← CHANGED: track upload state in a ref accessible inside closures

  useEffect(() => {
    const check = () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      getHealth(controller.signal)
        .then((res) => {
          lastHealthSuccessAt.current = Date.now();
          setHealth(res.status === "ok" ? "Backend connected" : res.status);
          setApiError(null);
        })
        .catch(() => {
          if (uploadingRef.current) return; // ← CHANGED: don't show disconnected while uploading
          lastHealthSuccessAt.current = 0;
          setHealth("Backend disconnected");
          setApiError("Could not reach Astraeus 2.0 API. Is the server running on port 8765?");
        })
        .finally(() => clearTimeout(timeoutId));
    };
    check();
    const interval = setInterval(check, 1500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const STALE_MS = 4000;
    const id = setInterval(() => {
      if (uploadingRef.current) return; // ← CHANGED: don't mark stale while uploading
      if (lastHealthSuccessAt.current === 0) return;
      if (Date.now() - lastHealthSuccessAt.current > STALE_MS) {
        lastHealthSuccessAt.current = 0;
        setHealth("Backend disconnected");
        setApiError("Could not reach Astraeus 2.0 API. Is the server running on port 8765?");
      }
    }, 1500);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    getMeta()
      .then((m) => {
        setMeta(m);
        if (m.llm_models.length > 0 && !llmModel) {
          setLlmModel(m.llm_models[0].id);
        }
        if (m.embedding_models?.length) {
          const currentInList = m.embedding_models.some((em) => em.id === m.embedding_model);
          if (currentInList && !embeddingModel) setEmbeddingModel(m.embedding_model);
          else if (!embeddingModel) setEmbeddingModel(m.embedding_models[0].id);
        }
        setLlmTestStatus("idle");
        setLlmTestMessage("");
        setTavilyTestStatus("idle");
        setTavilyTestMessage("");
      })
      .catch(() => {});
  }, []);

  const handleTestEmbedding = useCallback(async () => {
    setEmbeddingTestMessage("");
    setEmbeddingTestStatus("testing");
    const modelId = embeddingModel || meta?.embedding_model;
    const token = meta?.embedding_hf_configured ? undefined : embeddingHfToken;
    try {
      const res = await testEmbedding({ model_id: modelId, token });
      if (res.ok) {
        setEmbeddingTestStatus("success");
        setEmbeddingTestMessage("Model loaded successfully.");
      } else {
        setEmbeddingTestStatus("error");
        setEmbeddingTestMessage(res.detail || "Test failed.");
      }
    } catch (e) {
      setEmbeddingTestStatus("error");
      setEmbeddingTestMessage(e instanceof Error ? e.message : String(e));
    }
  }, [embeddingModel, embeddingHfToken, meta?.embedding_model, meta?.embedding_hf_configured]);

  const handleConfigureEmbedding = useCallback(async () => {
    const modelId = embeddingModel || meta?.embedding_model;
    if (!modelId) return;
    const token = meta?.embedding_hf_configured ? undefined : embeddingHfToken;
    try {
      await configureEmbedding(modelId, token);
      const m = await getMeta();
      setMeta(m);
      setEmbeddingTestMessage("Model in use. Re-upload documents if you changed the model.");
    } catch (e) {
      setEmbeddingTestMessage(e instanceof Error ? e.message : String(e));
    }
  }, [embeddingModel, embeddingHfToken, meta?.embedding_model, meta?.embedding_hf_configured]);

  useEffect(() => {
    if (!meta?.llm_configured || llmTestStatus !== "idle") return;
    testLlmKey(undefined)
      .then((res) => {
        if (res.ok) setLlmTestStatus("success");
        else {
          setLlmTestStatus("error");
          setLlmTestMessage(res.detail || "Key test failed.");
        }
      })
      .catch(() => {
        setLlmTestStatus("error");
        setLlmTestMessage("Could not reach API.");
      });
  }, [meta?.llm_configured, llmTestStatus]);

  useEffect(() => {
    if (!meta?.tavily_configured || tavilyTestStatus !== "idle") return;
    testTavilyKey(undefined)
      .then((res) => {
        if (res.ok) setTavilyTestStatus("success");
        else {
          setTavilyTestStatus("error");
          setTavilyTestMessage(res.detail || "Connection test failed.");
        }
      })
      .catch(() => {
        setTavilyTestStatus("error");
        setTavilyTestMessage("Could not reach API.");
      });
  }, [meta?.tavily_configured, tavilyTestStatus]);

  const handleTestTavily = useCallback(async () => {
    setTavilyTestMessage("");
    setTavilyTestStatus("testing");
    const keyToTest = meta?.tavily_configured ? undefined : userTavilyKey;
    try {
      const res = await testTavilyKey(keyToTest);
      if (res.ok) {
        setTavilyTestStatus("success");
        setTavilyTestMessage("Connection working.");
      } else {
        setTavilyTestStatus("error");
        setTavilyTestMessage(res.detail || "Test failed.");
      }
    } catch (e) {
      setTavilyTestStatus("error");
      setTavilyTestMessage(e instanceof Error ? e.message : String(e));
    }
  }, [meta?.tavily_configured, userTavilyKey]);

  const handleTestKey = useCallback(async () => {
    setLlmTestMessage("");
    setLlmTestStatus("testing");
    const keyToTest = meta?.llm_configured ? undefined : userApiKey;
    try {
      const res = await testLlmKey(keyToTest);
      if (res.ok) {
        setLlmTestStatus("success");
        setLlmTestMessage("Key is valid.");
      } else {
        setLlmTestStatus("error");
        setLlmTestMessage(res.detail || "Test failed.");
      }
    } catch (e) {
      setLlmTestStatus("error");
      setLlmTestMessage(e instanceof Error ? e.message : String(e));
    }
  }, [meta?.llm_configured, userApiKey]);

  const handleLaunch = useCallback(async () => {
    const q = (query || "").trim();
    if (!q) {
      setLaunchError("Please enter a research question.");
      return;
    }
    setLaunchError(null);
    // Clear run and RAG/report state so every new search starts with a blank slate (no stale data from previous run).
    setRunId(null);
    setRunContext(null);
    setContextRunId(null);
    setReportMd(null);
    setReportError(null);
    const openrouterKey = !meta?.llm_configured && userApiKey.trim() ? userApiKey.trim() : undefined;
    const tavilyKey = !meta?.tavily_configured && userTavilyKey.trim() ? userTavilyKey.trim() : undefined;
    try {
      const { run_id } = await startRun({
        query: q,
        llm_model: llmModel || undefined,
        openrouter_api_key: openrouterKey,
        tavily_api_key: tavilyKey,
        search_type: searchType,
      });
      setRunId(run_id);
      setMainContentTab("summary");
    } catch (e) {
      setLaunchError(e instanceof Error ? e.message : String(e));
    }
  }, [query, llmModel, searchType, meta?.llm_configured, meta?.tavily_configured, userApiKey, userTavilyKey]);

  useEffect(() => {
    if (!runId || !runState?.is_complete || runState.has_error) return;
    const runIdForContext = runId;
    getRunContext(runId)
      .then((ctx) => {
        setRunContext(ctx);
        setContextRunId(runIdForContext);
        const md = ctx.data.report_markdown;
        if (typeof md === "string" && md) setReportMd(md);
        else getReportMarkdown(runId).then(setReportMd).catch(() => {});
      })
      .catch(() => {
        getReportMarkdown(runId).then(setReportMd).catch((e) => setReportError(e instanceof Error ? e.message : String(e)));
      });
  }, [runId, runState?.is_complete, runState?.has_error]);

  const handleDownloadMarkdown = useCallback(async () => {
    if (!runId) return;
    try {
      const text = await getReportMarkdown(runId);
      const blob = new Blob([text], { type: "text/markdown" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `astraeus-2-report-${runId.slice(0, 8)}.md`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      setReportError(e instanceof Error ? e.message : String(e));
    }
  }, [runId]);

  const handleDownloadPdf = useCallback(async () => {
    if (!runId) return;
    try {
      const blob = await getReportPdfBlob(runId);
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `astraeus-2-report-${runId.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      setReportError(e instanceof Error ? e.message : String(e));
    }
  }, [runId]);

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files?.length) return;

      uploadingRef.current = true; // ← CHANGED: set ref before upload starts
      setUploading(true);
      setUploadResult(null);
      setUploadStep(1);

      const interval = window.setInterval(() => {
        setUploadStep((prev) => (prev < 3 ? (prev + 1) as 1 | 2 | 3 : prev));
      }, 8000);

      uploadFiles(Array.from(files))
        .then((r) => {
          window.clearInterval(interval);
          setUploadStep(3);
          setUploadResult(
            `${r.success} document(s) added, ${r.total_chunks} sections indexed. ${r.failed ? `Failed: ${r.failed}.` : ""}`
          );
          getMeta().then(setMeta);
        })
        .catch((err) => {
          window.clearInterval(interval);
          setUploadStep(3);
          setUploadResult(`Upload failed. ${err instanceof Error ? err.message : String(err)} Try again or check file format (PDF, TXT, MD).`);
        })
        .finally(() => {
          uploadingRef.current = false; // ← CHANGED: clear ref when upload finishes
          setUploading(false);
          e.target.value = "";
        });
    },
    []
  );

  const handleReset = useCallback(() => {
    setRunId(null);
    setRunContext(null);
    setContextRunId(null);
    setReportMd(null);
    setReportError(null);
    setLaunchError(null);
    setQuery("");
    setMainContentTab("summary");
    setUploadResult(null);
    setUploadStep(1);
    setUploadInputKey((k) => k + 1);
  }, []);

  const SUGGESTIONS = [
    { label: "RAG & hallucinations", query: "What are best practices to reduce hallucinations in RAG systems?" },
    { label: "Vector DBs comparison", query: "Compare leading vector databases for semantic search." },
    { label: "Multi-agent AI", query: "How do multi-agent AI systems coordinate and what are the trade-offs?" },
    { label: "RAG chunking", query: "What chunking strategies work best for RAG and why?" },
    { label: "Query expansion", query: "Techniques and trade-offs for query expansion in retrieval." },
  ] as const;

  return (
    <div className="app-root">
      <header className="app-header">
        <button
          type="button"
          className="header-menu-btn"
          onClick={() => setSidebarOpen(true)}
          aria-label="Open menu"
        >
          <span className="header-menu-icon" aria-hidden>☰</span>
        </button>
        <div className="header-brand">
          <div className="logo">🔬 Astraeus 2.0</div>
          <p className="header-subtitle">Multi-Agent AI Deep Researcher – 6 Agents – RAG-Powered</p>
        </div>
        <div className="header-right" title={apiError ? `${health}. Start the API server (e.g. uvicorn server.api:app --reload --port 8765) to connect.` : health}>
          <button
            type="button"
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            <span className="theme-toggle-icon" aria-hidden>
              {theme === "dark" ? "☀️" : "🌙"}
            </span>
          </button>
          <span className={`status-dot ${apiError ? "status-dot--off" : "status-dot--on"}`} aria-hidden />
          <span className="tagline">{health}</span>
        </div>
      </header>

      <div
        className={`sidebar-backdrop ${sidebarOpen ? "sidebar-backdrop--open" : ""}`}
        aria-hidden={!sidebarOpen}
        onClick={() => setSidebarOpen(false)}
      />

      <div className="app-layout">
        <aside
          className={`app-sidebar ${sidebarOpen ? "app-sidebar--open" : ""}`}
          style={isDesktop ? { width: sidebarWidth } : undefined}
        >
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close menu"
          >
            ✕
          </button>
          <div className="sidebar-block">
            <h3>System status</h3>
            {meta && (
              <ul className="metrics-list">
                <li>Documents in index: <strong>{meta.doc_count}</strong></li>
                <li>Embedding: <strong>{meta.embedding_models?.find((em) => em.id === meta.embedding_model)?.name ?? meta.embedding_model}</strong></li>
              </ul>
            )}
          </div>
          <div className="sidebar-block">
            <h3>Embedding model</h3>
          {meta?.embedding_models?.length ? (
            <>
              <p className="sidebar-embedding-notice">
                All models work without a token. Without one you may see rate limit or unauthenticated-request messages in server logs; adding a token avoids this.
              </p>
              <label className="sidebar-label">Model</label>
              <select
                className="sidebar-select"
                value={embeddingModel || meta.embedding_model}
                onChange={(e) => setEmbeddingModel(e.target.value)}
              >
                {meta.embedding_models.map((em) => (
                  <option key={em.id} value={em.id}>
                    {em.name} ({em.dimension}d)
                  </option>
                ))}
              </select>
              {!meta.embedding_hf_configured && (
                <>
                  <label className="sidebar-label">Hugging Face token (optional)</label>
                  <input
                    type="password"
                    className="sidebar-input"
                    placeholder="hf_…"
                    value={embeddingHfToken}
                    onChange={(e) => setEmbeddingHfToken(e.target.value)}
                    disabled={!!apiError}
                    autoComplete="off"
                  />
                  <p className="sidebar-hint">Add in .env as HF_TOKEN or paste here</p>
                </>
              )}
              <button
                type="button"
                className="btn btn-secondary sidebar-test-btn"
                onClick={handleConfigureEmbedding}
                disabled={!!apiError}
              >
                Use this model
              </button>
              <details className="sidebar-details-advanced">
                <summary className="sidebar-details-summary">Advanced: test model load</summary>
                <div className="sidebar-details-content">
                  <button
                    type="button"
                    className="btn btn-secondary sidebar-test-btn"
                    onClick={handleTestEmbedding}
                    disabled={embeddingTestStatus === "testing" || !!apiError}
                  >
                    {embeddingTestStatus === "testing" ? "Testing…" : "Test embedding"}
                  </button>
                  {embeddingTestStatus === "success" && <p className="sidebar-result sidebar-result--success">✓ {embeddingTestMessage}</p>}
                  {embeddingTestStatus === "error" && <p className="sidebar-result sidebar-result--error">{embeddingTestMessage}</p>}
                  {embeddingTestMessage && embeddingTestStatus !== "success" && embeddingTestStatus !== "error" && (
                    <p className="sidebar-result">{embeddingTestMessage}</p>
                  )}
                </div>
              </details>
            </>
          ) : (
            <p className="sidebar-llm-status">—</p>
          )}
          </div>
          <div className="sidebar-block">
            <h3>Language model</h3>
            <p className="sidebar-llm-status">
              {meta?.llm_configured ? "OpenRouter API key: from environment" : "API key required"}
            </p>
          {!meta?.llm_configured && (
            <>
              <label className="sidebar-label">OpenRouter API key</label>
              <input
                type="password"
                className="sidebar-input"
                placeholder="sk-…"
                value={userApiKey}
                onChange={(e) => setUserApiKey(e.target.value)}
                disabled={!!apiError}
                autoComplete="off"
              />
              <p className="sidebar-hint">Required if not set in .env</p>
            </>
          )}
          <button
            type="button"
            className="btn btn-secondary sidebar-test-btn"
            onClick={handleTestKey}
            disabled={llmTestStatus === "testing" || !!apiError}
          >
            {llmTestStatus === "testing" ? "Testing…" : "Test key"}
          </button>
          {llmTestStatus === "success" && <p className="sidebar-result sidebar-result--success">✓ Key is valid</p>}
          {llmTestStatus === "error" && <p className="sidebar-result sidebar-result--error">{llmTestMessage}</p>}
          <label className="sidebar-label">Research model</label>
          <select
            className="sidebar-select"
            value={llmModel}
            onChange={(e) => setLlmModel(e.target.value)}
          >
            {meta?.llm_models?.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
            {(!meta?.llm_models?.length) && <option value="">—</option>}
          </select>
          {meta?.llm_models?.length > 0 && (() => {
            const selected = meta.llm_models.find((m) => m.id === llmModel) ?? meta.llm_models[0];
            return (
              <div className="sidebar-model-cost">
                <h4 className="sidebar-model-cost-title">Model cost & use</h4>
                <p className="sidebar-model-cost-line">
                  Input: ${selected.input_per_1m}/1M tokens · Output: ${selected.output_per_1m}/1M tokens
                </p>
                {selected.hint && <p className="sidebar-model-cost-hint">{selected.hint}</p>}
              </div>
            );
          })()}
          </div>
          <div className="sidebar-block">
            <h3>Web search (Tavily)</h3>
            {meta?.tavily_available && tavilyTestStatus !== "success" && (
              <p className="sidebar-llm-status">Status: Available</p>
            )}
            <p className="sidebar-llm-status">
              {meta?.tavily_configured ? "Tavily API key: from environment" : "API key required"}
            </p>
          {!meta?.tavily_configured && (
            <>
              <label className="sidebar-label">Tavily API key</label>
              <input
                type="password"
                className="sidebar-input"
                placeholder="tvly-…"
                value={userTavilyKey}
                onChange={(e) => setUserTavilyKey(e.target.value)}
                disabled={!!apiError}
                autoComplete="off"
              />
              <p className="sidebar-hint">Required for web search. Set TAVILY_API_KEY in .env or paste here.</p>
            </>
          )}
          <button
            type="button"
            className="btn btn-secondary sidebar-test-btn"
            onClick={handleTestTavily}
            disabled={tavilyTestStatus === "testing" || !!apiError}
          >
            {tavilyTestStatus === "testing" ? "Testing…" : "Test connection"}
          </button>
          {tavilyTestStatus === "success" && <p className="sidebar-result sidebar-result--success">✓ {tavilyTestMessage}</p>}
          {tavilyTestStatus === "error" && <p className="sidebar-result sidebar-result--error">{tavilyTestMessage}</p>}
          </div>
          <div className="sidebar-block sidebar-llm-usage-block">
            <h3>LLM Usage</h3>
            {runId && runContext && contextRunId === runId && runContext.data?.llm_usage ? (() => {
              const usage = runContext.data.llm_usage;
              const prompt = usage.prompt_tokens ?? 0;
              const completion = usage.completion_tokens ?? 0;
              const total = prompt + completion;
              const modelId = (runContext.data as { llm_model?: string }).llm_model ?? runState?.llm_model;
              const modelMeta = meta?.llm_models?.find((m) => m.id === modelId);
              const cost = modelMeta && total > 0
                ? (prompt / 1e6) * modelMeta.input_per_1m + (completion / 1e6) * modelMeta.output_per_1m
                : null;
              return (
                <>
                  <div className="sidebar-llm-usage">
                    <div className="sidebar-llm-usage__metric">
                      <span className="sidebar-llm-usage__label">Prompt Tokens</span>
                      <span className="sidebar-llm-usage__value">{prompt.toLocaleString()}</span>
                    </div>
                    <div className="sidebar-llm-usage__metric">
                      <span className="sidebar-llm-usage__label">Completion Tokens</span>
                      <span className="sidebar-llm-usage__value">{completion.toLocaleString()}</span>
                    </div>
                    <div className="sidebar-llm-usage__metric">
                      <span className="sidebar-llm-usage__label">Total Tokens</span>
                      <span className="sidebar-llm-usage__value">{total.toLocaleString()}</span>
                    </div>
                    <div className="sidebar-llm-usage__metric">
                      <span className="sidebar-llm-usage__label">Est. Cost (USD)</span>
                      <span className="sidebar-llm-usage__value">
                        {cost != null ? `$${cost.toFixed(6)}` : "—"}
                      </span>
                    </div>
                  </div>
                  <p className="sidebar-llm-usage-disclaimer">
                    Pricing approximate; see{" "}
                    <a href="https://openrouter.ai/pricing" target="_blank" rel="noopener noreferrer">openrouter.ai/pricing</a>
                  </p>
                </>
              );
            })() : (
              <p className="sidebar-llm-usage-empty">Run a search to see LLM usage.</p>
            )}
          </div>
        </aside>

        <div
          className="sidebar-resize-handle"
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize sidebar"
          onMouseDown={handleSidebarResizeStart}
        />

        <main className="app-main">
          <section className="add-documents-section">
            <h2 className="add-documents-section__title">Add Documents to Knowledge Base</h2>
            <input
              key={uploadInputKey}
              type="file"
              multiple
              accept=".pdf,.txt,.md"
              onChange={handleFileUpload}
              disabled={uploading || !!apiError}
              className="add-documents-section__input"
            />
            {uploading && (
              <div className="upload-progress">
                <div className="upload-spinner" />
                <div className="upload-steps">
                  <div className={`upload-step ${uploadStep >= 1 ? "upload-step--active" : ""}`}>
                    <span className="upload-step-dot" />
                    <span className="upload-step-label">Uploading files</span>
                  </div>
                  <div className={`upload-step ${uploadStep >= 2 ? "upload-step--active" : ""}`}>
                    <span className="upload-step-dot" />
                    <span className="upload-step-label">Processing & indexing</span>
                  </div>
                  <div className={`upload-step ${uploadStep >= 3 ? "upload-step--active" : ""}`}>
                    <span className="upload-step-dot" />
                    <span className="upload-step-label">Updating search index</span>
                  </div>
                </div>
              </div>
            )}
            {uploadResult && !uploading && <p className="add-documents-section__result">{uploadResult}</p>}
          </section>

          <section className="hero">
            <h1>Start a research run</h1>
            <p>Enter your research question. We&apos;ll search your documents and the web, analyze claims, and generate a report.</p>
          </section>

          <section className="launch-card">
            <div className="launch-row">
              <label className="launch-label">Research question</label>
              <textarea
                className="launch-query"
                placeholder="Enter a research question and our 6-agent pipeline will retrieve, analyze, fact-check, and produce a cited report in under 2 minutes."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={2}
              />
            </div>
            <div className="launch-suggestions">
              {SUGGESTIONS.map(({ label, query: presetQuery }) => (
                <button
                  key={label}
                  type="button"
                  className="launch-suggestion-btn"
                  onClick={() => setQuery(presetQuery)}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="launch-row launch-row--search-type">
              <span className="launch-label">Search type</span>
              <div className="search-type-options" role="radiogroup" aria-label="Search type">
                <label className="search-type-option">
                  <input
                    type="radio"
                    name="searchType"
                    value="both"
                    checked={searchType === "both"}
                    onChange={() => setSearchType("both")}
                  />
                  <span>Both (RAG + Web)</span>
                </label>
                <label className="search-type-option">
                  <input
                    type="radio"
                    name="searchType"
                    value="rag_only"
                    checked={searchType === "rag_only"}
                    onChange={() => setSearchType("rag_only")}
                  />
                  <span>RAG only</span>
                </label>
                <label className="search-type-option">
                  <input
                    type="radio"
                    name="searchType"
                    value="web_only"
                    checked={searchType === "web_only"}
                    onChange={() => setSearchType("web_only")}
                  />
                  <span>Web search only</span>
                </label>
              </div>
            </div>
            <div className="launch-row launch-row--actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleLaunch}
                disabled={
                  runLoading ||
                  isPolling ||
                  llmTestStatus !== "success" ||
                  (searchType !== "rag_only" && tavilyTestStatus !== "success")
                }
              >
                {runLoading || isPolling ? "Research in progress…" : "Start research"}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleReset}
                aria-label="Reset search and run"
              >
                <span className="btn-icon" aria-hidden>↻</span> Reset
              </button>
              {llmTestStatus !== "success" && (
                <p className="launch-hint">Test your LLM key in the sidebar first to enable Start research.</p>
              )}
              {llmTestStatus === "success" && searchType !== "rag_only" && tavilyTestStatus !== "success" && (
                <p className="launch-hint">Test your Tavily connection in the sidebar to use web search.</p>
              )}
            </div>
            {launchError && <p className="launch-error">{launchError}</p>}
          </section>

          {runError && (
            <section className="status-card status-card--error">
              <p>{runError}</p>
            </section>
          )}

          {runId && runState && (
            <>
            <section className="pipeline-section">
              <h2>Research pipeline</h2>
              <div className="pipeline-meta">
                Run <code>{runId.slice(0, 8)}</code>
                {runState.total_elapsed > 0 && (
                  <> · {runState.total_elapsed.toFixed(1)}s total</>
                )}
                {isPolling && <span className="pipeline-live">Updating</span>}
              </div>
              {runState.is_complete && runId && runContext && contextRunId === runId && (
                <PipelineResultsStrip runState={runState} context={runContext.data} />
              )}
              {runState.agents.length > 0 && (
                <>
                  {runState.is_complete && (
                    <p className="pipeline-status-line">
                      {runState.agents.filter((a) => a.state === "complete").length}/{runState.agents.length} agents complete
                    </p>
                  )}
                  <div className="pipeline-bar-and-cards">
                    {runState.agents.map((a, idx) => {
                      const isComplete = a.state === "complete";
                      const isActive = a.state === "working" || a.state === "waiting";
                      const isError = a.state === "error";
                      const cls = [
                        "pipeline-bar__segment",
                        isComplete ? "pipeline-bar__segment--complete" : "",
                        isActive ? "pipeline-bar__segment--active" : "",
                        isError ? "pipeline-bar__segment--error" : "",
                      ]
                        .filter(Boolean)
                        .join(" ");
                      return (
                        <div key={`bar-${a.agent_id || idx}`} className="pipeline-bar__cell">
                          <div className={cls} />
                        </div>
                      );
                    })}
                    {runState.agents.map((a) => (
                      <div key={a.agent_id} className="pipeline-agent-cell">
                        <AgentCard agent={a} />
                      </div>
                    ))}
                  </div>
                  {runState.is_complete && (
                    <div className="pipeline-complete-banner" role="status">
                      ✓ Research complete – Your report is ready below
                    </div>
                  )}
                </>
              )}
            </section>

            {runState.is_complete && runId && (
              <>
                <div className="main-tabs">
                  <button
                    type="button"
                    className={`main-tab ${mainContentTab === "summary" ? "main-tab--active" : ""}`}
                    onClick={() => setMainContentTab("summary")}
                  >
                    Summary
                  </button>
                  <button
                    type="button"
                    className={`main-tab ${mainContentTab === "sources" ? "main-tab--active" : ""}`}
                    onClick={() => setMainContentTab("sources")}
                  >
                    Sources
                  </button>
                </div>
                {mainContentTab === "summary" && (
                  <section className="report-section">
                    <h2>Research report</h2>
                    {reportError && <p className="report-error">{reportError}</p>}
                    <div className="report-actions">
                      <button type="button" className="btn btn-secondary" onClick={handleDownloadMarkdown}>
                        Download as Markdown
                      </button>
                      <button type="button" className="btn btn-secondary" onClick={handleDownloadPdf}>
                        Download as PDF
                      </button>
                    </div>
                    {reportMd && (
                      <div className="report-preview markdown-preview">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            a: ({ href, children }) => {
                              const safeHref = href && /^https?:\/\//i.test(href) ? href : "#";
                              return (
                                <a
                                  href={safeHref}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="report-link"
                                >
                                  {children}
                                </a>
                              );
                            },
                          }}
                        >
                          {reportMd}
                        </ReactMarkdown>
                      </div>
                    )}
                  </section>
                )}
                {mainContentTab === "sources" && runContext && contextRunId === runId && (
                  <section className="rag-viz-section">
                    <h2>How we used your sources</h2>
                    {(() => {
                      const chunks = runContext.data?.retrieved_chunks ?? [];
                      const claims = runContext.data?.claims ?? [];
                      const hasRagData = chunks.length > 0 || claims.length > 0;
                      if (!hasRagData) {
                        return (
                          <p className="rag-empty-state">No document or web sources were used for this run.</p>
                        );
                      }
                      return (
                        <>
                          <div className="rag-tabs">
                            <button
                              type="button"
                              className={`rag-tab ${ragTab === "embedding" ? "rag-tab--active" : ""}`}
                              onClick={() => setRagTab("embedding")}
                            >
                              🗺️ Embedding Space
                            </button>
                            <button
                              type="button"
                              className={`rag-tab ${ragTab === "waterfall" ? "rag-tab--active" : ""}`}
                              onClick={() => setRagTab("waterfall")}
                            >
                              🏗️ Retrieval Waterfall
                            </button>
                            <button
                              type="button"
                              className={`rag-tab ${ragTab === "claims" ? "rag-tab--active" : ""}`}
                              onClick={() => setRagTab("claims")}
                            >
                              ✅ Claims & Evidence
                            </button>
                          </div>
                          <div className="rag-tab-panel">
                            {ragTab === "embedding" && <EmbeddingSpaceViz context={runContext.data} />}
                            {ragTab === "waterfall" && <RetrievalWaterfallViz context={runContext.data} />}
                            {ragTab === "claims" && <ClaimsEvidenceViz context={runContext.data} />}
                          </div>
                        </>
                      );
                    })()}
                  </section>
                )}
              </>
            )}
            </>
          )}

        </main>
      </div>
    </div>
  );
};
