/**
 * The Ward — KaTeX math rendering utility (CDN-backed, no build step).
 */
const WardKaTeX = (() => {
    'use strict';

    const pending = [];
    let ready = false;

    function escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = String(str);
        return d.innerHTML;
    }

    function escapeAttr(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function isReady() {
        return typeof katex !== 'undefined' && typeof katex.renderToString === 'function';
    }

    function markReady() {
        if (!isReady()) return false;
        ready = true;
        const queue = pending.splice(0);
        queue.forEach((fn) => { try { fn(); } catch (_) { /* ignore */ } });
        return true;
    }

    /**
     * Run callback once KaTeX CDN script is available.
     */
    function whenReady(callback) {
        if (ready && isReady()) {
            callback();
            return;
        }
        pending.push(callback);
        if (isReady()) markReady();
        else {
            const poll = setInterval(() => {
                if (markReady()) clearInterval(poll);
            }, 40);
            setTimeout(() => clearInterval(poll), 8000);
        }
    }

    /**
     * Render a LaTeX string to HTML for inline insertion.
     */
    function renderLatexString(latex, options = {}) {
        const src = (latex ?? '').trim();
        if (!src) return '';

        const displayMode = Boolean(options.displayMode);

        if (!isReady()) {
            return `<code class="math-fallback">${escapeHtml(src)}</code>`;
        }

        try {
            return katex.renderToString(src, {
                displayMode,
                throwOnError: false,
                strict: 'warn',
                trust: false,
                output: 'html',
            });
        } catch (_) {
            return `<code class="math-fallback">${escapeHtml(src)}</code>`;
        }
    }

    function shouldDisplay(node) {
        return (
            node.classList.contains('math-display') ||
            node.dataset.display === 'true' ||
            Boolean(node.closest('.dose-derivation'))
        );
    }

    function getLatex(node) {
        if (node.dataset.latex) return node.dataset.latex.trim();
        return (node.textContent || '').trim();
    }

    /**
     * Find and render math inside a container.
     */
    function renderMathInElement(el, options = {}) {
        if (!el) return;

        const selector = options.selector || '.math-latex, [data-latex]';
        const nodes = el.querySelectorAll(selector);

        nodes.forEach((node) => {
            const latex = getLatex(node);
            if (!latex) return;

            const displayMode = shouldDisplay(node);
            node.innerHTML = renderLatexString(latex, { displayMode });
            node.classList.add('math-rendered');
            if (displayMode) node.classList.add('math-display');
        });
    }

    function renderMathInElementWhenReady(el, options = {}) {
        whenReady(() => renderMathInElement(el, options));
    }

    // Bootstrap on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => markReady());
    } else {
        markReady();
    }

    return {
        renderLatexString,
        renderMathInElement,
        renderMathInElementWhenReady,
        whenReady,
        escapeAttr,
        isReady,
    };
})();