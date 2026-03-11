"""
Custom CSS for Astraeus 2.0 — Multi-Agent AI Deep Researcher.
Neon pipeline UI: per-agent colors, glowing borders, corner icons, progress bars.
"""


def get_custom_css() -> str:
    """Return the full custom CSS for the app."""
    return """
<style>
/* ── Global ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: #f8fafc;
}

/* ── Hero section ────────────────────────────────────────────────────── */
.hero-section {
    margin: 12px 0 16px 0;
    padding: 12px 16px;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.06) 0%, rgba(139, 92, 246, 0.06) 100%);
    border-radius: 12px;
    border-left: 4px solid #6366f1;
}
.hero-text {
    margin: 0;
    font-size: 0.95rem;
    color: #475569;
    line-height: 1.5;
}

/* ── Completion celebration banner ───────────────────────────────────── */
.pipeline-complete-banner {
    margin: 16px 0 24px 0;
    padding: 16px 24px;
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.12) 0%, rgba(34, 211, 238, 0.1) 100%);
    border-radius: 12px;
    border: 1px solid rgba(34, 197, 94, 0.35);
    text-align: center;
    animation: banner-pulse 2.5s ease-in-out 2;
}
.pipeline-complete-banner .banner-icon {
    font-size: 1.5rem;
    margin-right: 8px;
}
.pipeline-complete-banner .banner-text {
    font-size: 1rem;
    font-weight: 600;
    color: #15803d;
}
@keyframes banner-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.2); }
    50% { box-shadow: 0 0 20px 4px rgba(34, 197, 94, 0.25); }
}

/* ── Embedding snippet panel (selected document) ─────────────────────── */
.embedding-snippet-panel {
    margin: 12px 0;
    padding: 14px 18px;
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-radius: 12px;
    border: 1px solid rgba(0, 0, 0, 0.08);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.embedding-snippet-title {
    font-weight: 600;
    font-size: 0.9rem;
    color: #1e293b;
    margin-bottom: 6px;
}
.embedding-snippet-meta {
    font-size: 0.78rem;
    color: #64748b;
    margin-bottom: 8px;
}
.embedding-snippet-text {
    font-size: 0.85rem;
    color: #475569;
    line-height: 1.5;
}

/* ── Agent Card Base (light theme) ───────────────────────────────────── */
.agent-card {
    border-radius: 16px;
    padding: 20px;
    min-height: 300px;
    width: 100%;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
}

.agent-card .agent-corner-icon {
    position: absolute;
    top: 12px;
    right: 12px;
    padding: 8px;
    border-radius: 10px;
    font-size: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.agent-card .agent-icon-wrap {
    text-align: center;
    margin: 24px 0 12px 0;
}

.agent-card .agent-icon {
    font-size: 3rem;
    display: inline-block;
    filter: drop-shadow(0 0 8px currentColor);
}

.agent-card .agent-name {
    font-size: 0.9rem;
    font-weight: 600;
    text-align: center;
    margin-bottom: 8px;
    color: #1e293b;
}

.agent-card .agent-subtitle {
    font-size: 0.7rem;
    opacity: 0.8;
    text-align: center;
    margin-bottom: 12px;
    color: #475569;
}

.agent-card .agent-status-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 0.8rem;
    font-weight: 500;
    margin: 10px 0;
    color: #334155;
}

.agent-card .agent-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.agent-card .agent-activity {
    font-size: 0.72rem;
    min-height: 36px;
    padding: 8px;
    border-radius: 8px;
    background: rgba(0,0,0,0.04);
    margin-bottom: 8px;
    color: #475569;
}

.agent-card .agent-output {
    font-size: 0.7rem;
    padding: 8px;
    border-radius: 8px;
    background: rgba(0,0,0,0.05);
    max-height: 60px;
    overflow-y: auto;
    color: #334155;
}

.agent-card .agent-execution {
    font-size: 0.7rem;
    text-align: center;
    opacity: 0.8;
    margin-top: 8px;
    color: #64748b;
}

.agent-card .agent-card-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: rgba(0,0,0,0.08);
    border-radius: 0 0 16px 16px;
    overflow: hidden;
}

.agent-card .agent-card-progress-fill {
    height: 100%;
    border-radius: 0 0 0 16px;
    transition: width 0.5s ease;
}

/* ── State: not_started (dim) ────────────────────────────────────────── */
.agent-card.not-started {
    opacity: 0.6;
}

.agent-card.not-started .agent-icon {
    filter: grayscale(80%) opacity(0.5);
}

/* ── State: waiting (dashed, subtle) ─────────────────────────────────── */
.agent-card.waiting {
    border-style: dashed;
    animation: marchingAnts 1s linear infinite;
}

@keyframes marchingAnts {
    0%   { border-image-slice: 1; }
    100% { border-image-slice: 1; }
}

.agent-card.waiting .agent-card-progress-fill {
    width: 0% !important;
}

/* ── State: working (pulse glow) ─────────────────────────────────────── */
.agent-card.working {
    animation: neonPulse 2s ease-in-out infinite;
}

@keyframes neonPulse {
    0%, 100% { filter: brightness(1); }
    50%      { filter: brightness(1.15); }
}

.agent-card.working .agent-card-progress-fill {
    animation: progressIndeterminate 1.5s ease-in-out infinite;
}

@keyframes progressIndeterminate {
    0%   { width: 20% !important; margin-left: 0%; }
    50%  { width: 40% !important; margin-left: 30%; }
    100% { width: 20% !important; margin-left: 80%; }
}

/* ── State: complete (soft glow) ─────────────────────────────────────── */
.agent-card.complete {
    animation: completionFlash 0.6s ease-out;
}

@keyframes completionFlash {
    0%   { transform: scale(1.02); }
    100% { transform: scale(1); }
}

/* ── State: error ────────────────────────────────────────────────────── */
.agent-card.error {
    border-color: #ef4444 !important;
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.4) !important;
}

/* ── Inter-Agent Arrows ───────────────────────────────────────────────── */
.arrow-container {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
    min-height: 40px;
}

.arrow-inactive {
    color: #94a3b8;
    font-size: 1.5rem;
    opacity: 0.5;
}

.arrow-flowing {
    color: #64748b;
    font-size: 1.5rem;
    animation: arrowPulse 1s ease-in-out infinite;
}

.arrow-complete {
    color: #22c55e;
    font-size: 1.5rem;
    animation: arrowGlow 2s ease-in-out infinite;
}

@keyframes arrowPulse {
    0%, 100% { opacity: 0.6; transform: translateX(0); }
    50%      { opacity: 1; transform: translateX(3px); }
}

@keyframes arrowGlow {
    0%, 100% { opacity: 0.7; }
    50%      { opacity: 1; }
}

/* ── Pipeline Progress Bar (agent-themed segments) ────────────────────── */
.pipeline-progress {
    display: flex;
    gap: 4px;
    margin: 16px 0;
    height: 10px;
    border-radius: 5px;
    overflow: hidden;
    background: #e2e8f0;
}

.pipeline-progress-segment {
    flex: 1;
    border-radius: 3px;
    transition: all 0.3s;
}

.pipeline-progress-segment.dim {
    opacity: 0.3;
}

.pipeline-progress-segment.pulse {
    animation: segmentPulse 1s infinite;
}

@keyframes segmentPulse {
    0%, 100% { opacity: 0.8; }
    50%      { opacity: 1; }
}

/* ── Top bar ────────────────────────────────────────────────────────── */
.top-bar {
    background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.app-title {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}

.app-tagline {
    font-size: 0.85rem;
    color: #64748b;
    letter-spacing: 1px;
}

/* ── Visualization containers ───────────────────────────────────────── */
.viz-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* ── Report area ────────────────────────────────────────────────────── */
.report-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px;
    margin-top: 24px;
    max-height: 600px;
    overflow-y: auto;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* ── Metrics row ────────────────────────────────────────────────────── */
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-label {
    font-size: 0.75rem;
    color: #64748b;
    margin-top: 4px;
}
</style>
"""
