"""
PDF Export Utility
━━━━━━━━━━━━━━━━
Converts markdown research report to styled PDF for download.
Uses WeasyPrint when available; falls back to xhtml2pdf (no system deps).
"""

from __future__ import annotations
from datetime import datetime
import io
import re


def _markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to HTML using markdown library."""
    import markdown
    extensions = ["fenced_code", "tables", "nl2br", "sane_lists"]
    return markdown.markdown(markdown_text, extensions=extensions)


def _build_html_document(body_html: str, title: str = "Research Report") -> str:
    """Wrap body HTML in full document with styles."""
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    # Escape for HTML
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_title = safe_title[:80]

    css = """
    @page {
        size: A4;
        margin: 2cm;
        @bottom-center {
            content: counter(page) " / " counter(pages);
            font-size: 10px;
            color: #64748b;
        }
    }
    body {
        font-family: Georgia, 'Times New Roman', serif;
        font-size: 11pt;
        line-height: 1.5;
        color: #1e293b;
    }
    h1 {
        font-size: 24pt;
        margin-top: 0;
        margin-bottom: 12pt;
        color: #0f172a;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 8pt;
    }
    h2 {
        font-size: 18pt;
        margin-top: 20pt;
        margin-bottom: 10pt;
        color: #1e293b;
    }
    h3 {
        font-size: 14pt;
        margin-top: 14pt;
        margin-bottom: 8pt;
        color: #334155;
    }
    p {
        margin: 0 0 10pt 0;
    }
    ul, ol {
        margin: 0 0 10pt 0;
        padding-left: 24pt;
    }
    li {
        margin-bottom: 4pt;
    }
    a {
        color: #2563eb;
        text-decoration: underline;
    }
    code {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 10pt;
        background: #f1f5f9;
        padding: 2pt 6pt;
        border-radius: 4px;
    }
    pre {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 9pt;
        background: #f1f5f9;
        padding: 12pt;
        border-radius: 6px;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        page-break-inside: avoid;
    }
    pre code {
        background: none;
        padding: 0;
    }
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 16pt 0;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 12pt 0;
        page-break-inside: avoid;
    }
    th, td {
        border: 1px solid #e2e8f0;
        padding: 8pt 12pt;
        text-align: left;
    }
    th {
        background: #f8fafc;
        font-weight: 600;
    }
    .pdf-header {
        font-size: 9pt;
        color: #64748b;
        margin-bottom: 16pt;
        padding-bottom: 8pt;
        border-bottom: 1px solid #e2e8f0;
    }
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <style>{css}</style>
</head>
<body>
    <div class="pdf-header">Astraeus 2.0 Research Report · {safe_title} · {date_str}</div>
    {body_html}
</body>
</html>"""


def _pdf_via_weasyprint(html: str) -> bytes:
    """Generate PDF using WeasyPrint. Raises on failure."""
    from weasyprint import HTML
    return HTML(string=html).write_pdf()


def _pdf_via_xhtml2pdf(html: str) -> bytes:
    """Generate PDF using xhtml2pdf (pure Python, no system deps)."""
    from xhtml2pdf import pisa
    out = io.BytesIO()
    status = pisa.CreatePDF(html, dest=out, encoding="utf-8")
    if status.err:
        raise RuntimeError(f"xhtml2pdf failed: {status.err}")
    return out.getvalue()


def _build_html_simple(body_html: str, title: str) -> str:
    """Simpler HTML for xhtml2pdf (limited CSS support)."""
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")[:80]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{safe_title}</title>
    <style>
    body {{ font-family: Georgia, serif; font-size: 11pt; line-height: 1.5; color: #1e293b; }}
    h1 {{ font-size: 24pt; color: #0f172a; }}
    h2 {{ font-size: 18pt; }}
    h3 {{ font-size: 14pt; }}
    a {{ color: #2563eb; text-decoration: underline; }}
    pre, code {{ font-family: monospace; background: #f1f5f9; }}
    .pdf-header {{ font-size: 9pt; color: #64748b; margin-bottom: 16pt; }}
    </style>
</head>
<body>
    <div class="pdf-header">Astraeus 2.0 Research Report · {safe_title} · {date_str}</div>
    {body_html}
</body>
</html>"""


def markdown_to_pdf_bytes(
    markdown_text: str,
    title: str = "Research Report",
) -> bytes:
    """
    Convert markdown to PDF bytes.
    Uses WeasyPrint when available; falls back to xhtml2pdf (no system deps).
    """
    if not (markdown_text or "").strip():
        raise ValueError("Report is empty; nothing to export.")

    html_body = _markdown_to_html(markdown_text.strip())

    # Try WeasyPrint first (better quality)
    try:
        full_html = _build_html_document(html_body, title=title)
        return _pdf_via_weasyprint(full_html)
    except Exception:
        pass

    # Fallback to xhtml2pdf (pure Python)
    full_html = _build_html_simple(html_body, title=title)
    return _pdf_via_xhtml2pdf(full_html)


def is_pdf_export_available() -> bool:
    """Check if PDF export is available (weasyprint or xhtml2pdf)."""
    available, _ = get_pdf_export_status()
    return available


def get_pdf_export_status() -> tuple[bool, str | None]:
    """Return (available, error_message). Tries weasyprint first, then xhtml2pdf."""
    # Try WeasyPrint (better output, needs Cairo/Pango)
    try:
        from weasyprint import HTML  # noqa: F401
        return True, None
    except Exception:
        pass

    # Fallback: xhtml2pdf (pure Python, no system deps)
    try:
        from xhtml2pdf import pisa  # noqa: F401
        return True, None
    except ImportError:
        return False, "pip install xhtml2pdf"


def sanitize_filename_for_pdf(query: str, max_len: int = 40) -> str:
    """Create a safe filename from the query for the PDF download."""
    safe = re.sub(r'[^\w\s-]', '', query)
    safe = re.sub(r'[\s_]+', '_', safe).strip("_")
    return (safe[:max_len] + "_") if len(safe) > max_len else safe or "research_report"
