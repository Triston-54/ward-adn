/**
 * The Ward — Global export utilities
 * Shared download, print, and clipboard helpers for all modules.
 */
const WardExport = (() => {
    function toast(message, type = 'success') {
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            console.log(`[WardExport] ${message}`);
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        const d = document.createElement('div');
        d.textContent = String(str);
        return d.innerHTML;
    }

    function getPrintStyles() {
        return `
            :root {
                --ward-bg: #ffffff;
                --ward-text: #0f172a;
                --ward-muted: #475569;
                --ward-border: #cbd5e1;
                --ward-accent: #0284c7;
                --ward-header-bg: #0f172a;
                --ward-header-text: #f8fafc;
                --ward-row-alt: #f8fafc;
            }
            @media (prefers-color-scheme: dark) {
                :root {
                    --ward-bg: #0f172a;
                    --ward-text: #e2e8f0;
                    --ward-muted: #94a3b8;
                    --ward-border: #334155;
                    --ward-accent: #38bdf8;
                    --ward-header-bg: #1e293b;
                    --ward-header-text: #f1f5f9;
                    --ward-row-alt: #1e293b;
                }
            }
            * { box-sizing: border-box; }
            body {
                font-family: Inter, system-ui, sans-serif;
                margin: 1.5cm;
                color: var(--ward-text);
                background: var(--ward-bg);
                line-height: 1.5;
                font-size: 12px;
            }
            h1 {
                color: var(--ward-text);
                border-bottom: 2px solid var(--ward-accent);
                padding-bottom: 0.5rem;
                margin: 0 0 0.5rem;
                font-size: 1.35rem;
            }
            h2 {
                color: var(--ward-text);
                font-size: 1rem;
                margin: 1.25rem 0 0.5rem;
                border-left: 3px solid var(--ward-accent);
                padding-left: 0.5rem;
            }
            .ward-print-meta {
                color: var(--ward-muted);
                font-size: 10px;
                margin-bottom: 1.25rem;
            }
            .ward-print-footer {
                margin-top: 1.5rem;
                padding-top: 0.75rem;
                border-top: 1px solid var(--ward-border);
                color: var(--ward-muted);
                font-size: 9px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
                margin: 0.75rem 0;
            }
            th {
                background: var(--ward-header-bg);
                color: var(--ward-header-text);
                padding: 0.5rem 0.625rem;
                text-align: left;
                font-weight: 600;
            }
            td {
                padding: 0.4rem 0.625rem;
                border-bottom: 1px solid var(--ward-border);
                vertical-align: top;
            }
            tr:nth-child(even) td { background: var(--ward-row-alt); }
            .clinical, .muted { color: var(--ward-muted); font-size: 10px; }
            .trap { color: #b91c1c; }
            .avoid { color: #047857; }
            .answer {
                font-size: 1.25rem;
                font-weight: 700;
                color: var(--ward-accent);
                margin: 0.5rem 0;
            }
            .step {
                padding: 0.5rem 0.75rem;
                margin: 0.35rem 0;
                border-left: 3px solid var(--ward-accent);
                background: var(--ward-row-alt);
                border-radius: 0 0.25rem 0.25rem 0;
            }
            .step-num {
                font-size: 9px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--ward-muted);
            }
            .callout {
                padding: 0.625rem 0.75rem;
                margin: 0.75rem 0;
                border: 1px solid var(--ward-border);
                border-radius: 0.375rem;
                background: var(--ward-row-alt);
            }
            .callout-label {
                font-size: 9px;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: var(--ward-muted);
                margin-bottom: 0.25rem;
            }
            ul { margin: 0.25rem 0; padding-left: 1.25rem; }
            li { margin: 0.2rem 0; }
            .math-latex, .katex { font-size: 1.05em; }
            .math-latex-display, .math-display .katex-display { margin: 0.75rem 0; overflow-x: auto; }
            .math-fallback { font-family: 'JetBrains Mono', monospace; font-size: 10px; }
            @media print {
                :root {
                    --ward-bg: #ffffff;
                    --ward-text: #111111;
                    --ward-muted: #444444;
                    --ward-border: #cccccc;
                    --ward-accent: #0369a1;
                    --ward-header-bg: #0f172a;
                    --ward-header-text: #ffffff;
                    --ward-row-alt: #f8fafc;
                }
                body { margin: 1cm; }
                .no-print { display: none !important; }
                a { color: inherit; text-decoration: none; }
            }
        `;
    }

    const KATEX_CDN_CSS = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css';
    const KATEX_CDN_JS = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js';

    function getKatexHead() {
        return `<link rel="stylesheet" href="${KATEX_CDN_CSS}" crossorigin="anonymous">`;
    }

    function getKatexBootScript() {
        return `<script src="${KATEX_CDN_JS}" crossorigin="anonymous"><\/script>
<script>
(function() {
    function render() {
        if (typeof katex === 'undefined') return;
        document.querySelectorAll('.math-latex, [data-latex]').forEach(function(node) {
            var latex = (node.dataset.latex || node.textContent || '').trim();
            if (!latex || node.classList.contains('math-rendered')) return;
            try {
                var display = node.classList.contains('math-display') || node.dataset.display === 'true';
                node.innerHTML = katex.renderToString(latex, { displayMode: display, throwOnError: false });
                node.classList.add('math-rendered');
            } catch (_) {}
        });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render);
    else render();
})();
<\/script>`;
    }

    /**
     * Trigger a file download with the given text content.
     */
    function downloadText(filename, content, mime = 'text/plain;charset=utf-8') {
        const blob = new Blob([content], { type: mime });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        toast(`Downloaded ${filename}`);
    }

    /**
     * Open a new window with Ward print styles and trigger print dialog.
     */
    function openPrintableHtml(title, bodyHtml, meta = '', options = {}) {
        const win = window.open('', '_blank');
        if (!win) {
            toast('Pop-up blocked — allow pop-ups to print study sheets.', 'error');
            return null;
        }

        const safeTitle = escapeHtml(title);
        const metaLine = meta
            ? `<p class="ward-print-meta">${escapeHtml(meta)}</p>`
            : '';
        const renderMath = Boolean(options.renderMath);
        const katexHead = renderMath ? getKatexHead() : '';
        const katexBoot = renderMath ? getKatexBootScript() : '';

        win.document.write(`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>The Ward — ${safeTitle}</title>
    ${katexHead}
    <style>${getPrintStyles()}</style>
</head>
<body>
    <h1>The Ward — ${safeTitle}</h1>
    ${metaLine}
    ${bodyHtml}
    <p class="ward-print-footer">Generated by The Ward · New River CTC ADN · Local-first nursing study suite</p>
    <p class="ward-print-footer no-print" style="margin-top:0.5rem">Use <strong>Print → Save as PDF</strong> to keep a copy.</p>
    ${katexBoot}
</body>
</html>`);
        win.document.close();

        const triggerPrint = () => {
            win.focus();
            setTimeout(() => win.print(), renderMath ? 450 : 250);
        };
        win.onload = triggerPrint;
        if (renderMath) setTimeout(triggerPrint, 600);

        toast('Study sheet opened — use Print → Save as PDF');
        return win;
    }

    async function htmlToPlainText(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error('Export fetch failed');
        const html = await res.text();
        const doc = new DOMParser().parseFromString(html, 'text/html');
        return (doc.body?.innerText || '').replace(/\n{3,}/g, '\n\n').trim();
    }

    async function copyExportText(url, successMessage) {
        try {
            const text = await htmlToPlainText(url);
            return await copyToClipboard(text, successMessage);
        } catch {
            toast('Copy failed — is the server running?', 'error');
            return false;
        }
    }

    /**
     * Copy text to clipboard with toast feedback.
     */
    async function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
        try {
            await navigator.clipboard.writeText(text);
            toast(successMessage);
            return true;
        } catch {
            try {
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.style.position = 'fixed';
                ta.style.left = '-9999px';
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                ta.remove();
                toast(successMessage);
                return true;
            } catch {
                toast('Clipboard copy failed — check browser permissions.', 'error');
                return false;
            }
        }
    }

    return {
        downloadText,
        openPrintableHtml,
        copyToClipboard,
        copyExportText,
        htmlToPlainText,
        escapeHtml,
    };
})();