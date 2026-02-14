"""
Custom CSS for Astraeus — Multi-Agent AI Deep Researcher.
4-state card styles, colors, animations (marching ants, glow pulse, progress shimmer).
"""


def get_custom_css() -> str:
    """Return the full custom CSS for the app."""
    return """
<style>
/* ── Global ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    font-family: 'Inter', sans-serif;
}

/* ── Agent Card Base ────────────────────────────────────────────────── */
.agent-card {
    border-radius: 16px;
    padding: 20px;
    min-height: 300px;
    width: 100%;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

/* ── State: Not Started ─────────────────────────────────────────────── */
.agent-card.not-started {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 2px solid #2a2a4a;
    color: #6b7280;
    opacity: 0.7;
}

.agent-card.not-started .agent-icon {
    filter: grayscale(100%);
    opacity: 0.5;
}

/* ── State: Waiting ─────────────────────────────────────────────────── */
.agent-card.waiting {
    background: linear-gradient(135deg, #1a1a2e 0%, #2d2208 100%);
    border: 2px dashed #f59e0b;
    color: #fbbf24;
    animation: marchingAnts 1s linear infinite;
}

@keyframes marchingAnts {
    0%   { border-dash-offset: 0; }
    100% { border-dash-offset: 20; }
}

.agent-card.waiting::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(245, 158, 11, 0.05), transparent);
    animation: shimmer 2s infinite;
}

/* ── State: Working ─────────────────────────────────────────────────── */
.agent-card.working {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    border: 2px solid #3b82f6;
    color: #93c5fd;
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.3), 0 0 40px rgba(59, 130, 246, 0.1);
    animation: glowPulse 2s ease-in-out infinite;
}

@keyframes glowPulse {
    0%, 100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.3), 0 0 40px rgba(59, 130, 246, 0.1); }
    50%      { box-shadow: 0 0 30px rgba(59, 130, 246, 0.5), 0 0 60px rgba(59, 130, 246, 0.2); }
}

.agent-card.working::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 200%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.08), transparent);
    animation: progressShimmer 1.5s infinite;
}

@keyframes progressShimmer {
    0%   { transform: translateX(-50%); }
    100% { transform: translateX(50%); }
}

/* ── State: Complete ────────────────────────────────────────────────── */
.agent-card.complete {
    background: linear-gradient(135deg, #0f2419 0%, #14532d 100%);
    border: 2px solid #22c55e;
    color: #86efac;
    animation: completionFlash 0.6s ease-out;
}

@keyframes completionFlash {
    0%   { transform: scale(1.02); box-shadow: 0 0 30px rgba(34, 197, 94, 0.5); }
    100% { transform: scale(1); box-shadow: 0 0 10px rgba(34, 197, 94, 0.2); }
}

/* ── State: Error ───────────────────────────────────────────────────── */
.agent-card.error {
    background: linear-gradient(135deg, #2d0f0f 0%, #4a1111 100%);
    border: 2px solid #ef4444;
    color: #fca5a5;
}

/* ── Agent Card Zones ───────────────────────────────────────────────── */
.agent-header {
    text-align: center;
    margin-bottom: 12px;
}

.agent-icon {
    font-size: 2.5rem;
    display: block;
    margin-bottom: 8px;
    transition: all 0.3s;
}

.agent-name {
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 2px;
}

.agent-subtitle {
    font-size: 0.75rem;
    opacity: 0.7;
}

.agent-status {
    text-align: center;
    margin: 10px 0;
    padding: 6px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 500;
}

.agent-activity {
    font-size: 0.75rem;
    min-height: 40px;
    padding: 8px;
    border-radius: 8px;
    background: rgba(255,255,255,0.03);
    margin-bottom: 8px;
}

.agent-output {
    font-size: 0.72rem;
    padding: 8px;
    border-radius: 8px;
    background: rgba(255,255,255,0.05);
    max-height: 80px;
    overflow-y: auto;
}

/* ── Inter-Agent Arrows ─────────────────────────────────────────────── */
.arrow-container {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
    min-height: 40px;
}

.arrow-inactive {
    color: #4b5563;
    font-size: 1.5rem;
    opacity: 0.4;
}

.arrow-flowing {
    color: #3b82f6;
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

/* ── Pipeline Progress Bar ──────────────────────────────────────────── */
.pipeline-progress {
    display: flex;
    gap: 4px;
    margin: 16px 0;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    background: #1f2937;
}

.progress-segment {
    flex: 1;
    border-radius: 2px;
    transition: background-color 0.3s;
}

.progress-segment.not-started { background: #374151; }
.progress-segment.waiting     { background: #f59e0b; animation: segmentPulse 1s infinite; }
.progress-segment.working     { background: #3b82f6; animation: segmentPulse 0.8s infinite; }
.progress-segment.complete    { background: #22c55e; }
.progress-segment.error       { background: #ef4444; }

@keyframes segmentPulse {
    0%, 100% { opacity: 0.7; }
    50%      { opacity: 1; }
}

@keyframes shimmer {
    0%   { transform: translateX(0); }
    100% { transform: translateX(200%); }
}

/* ── Status badges ──────────────────────────────────────────────────── */
.status-not-started { background: rgba(107, 114, 128, 0.2); color: #9ca3af; }
.status-waiting     { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
.status-working     { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }
.status-complete    { background: rgba(34, 197, 94, 0.2); color: #86efac; }
.status-error       { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }

/* ── Top bar ────────────────────────────────────────────────────────── */
.top-bar {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    border: 1px solid #334155;
}

.app-title {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}

.app-tagline {
    font-size: 0.85rem;
    color: #94a3b8;
    letter-spacing: 1px;
}

/* ── Visualization containers ───────────────────────────────────────── */
.viz-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
}

/* ── Report area ────────────────────────────────────────────────────── */
.report-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 24px;
    margin-top: 24px;
    max-height: 600px;
    overflow-y: auto;
}

/* ── Metrics row ────────────────────────────────────────────────────── */
.metric-card {
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-label {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-top: 4px;
}
</style>
"""
