/**
 * The Ward — Medical Terminology Module
 */
const Terminology = (() => {
    const MODULE_ID = 'terminology';
    let flashcards = [], cardIndex = 0, cardFlipped = false;
    let practiceQuestions = [], practiceIndex = 0, practiceCorrect = 0;
    let practiceMode = 'mixed';
    let searchTimeout = null;
    let liveBuildTimeout = null;
    let customTermsLoaded = false;
    let customTerms = [];

    function getTermCount() {
        const el = document.getElementById('tab-export');
        return parseInt(el?.dataset.termCount || '217', 10);
    }

    // ── Tabs ──────────────────────────────────────────────────────────────────
    function switchTab(tab) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.querySelectorAll('.term-tab-btn').forEach(b => b.classList.remove('active'));
        const panel = document.getElementById('tab-' + tab);
        const btn = document.querySelector(`[data-tab="${tab}"]`);
        if (panel) panel.classList.remove('hidden');
        if (btn) btn.classList.add('active');

        if (tab === 'flashcards' && !flashcards.length) loadFlashcards(20, true);
        if (tab === 'database' && !document.querySelector('.term-card')) searchTerms();
        if (tab === 'myterms' && !customTermsLoaded) loadCustomTerms();
        history.replaceState(null, '', location.pathname + (tab !== 'builder' ? '#' + tab : ''));
        window.WardSocratic?.setModuleContext({ module: 'terminology', tab, subject: `Medical Terminology · ${tab}` });
    }

    const VALID_TABS = ['builder', 'database', 'flashcards', 'practice', 'myterms', 'export'];
    const DEFAULT_TAB = 'builder';

    // ── Word Builder ──────────────────────────────────────────────────────────
    function getBuilderValues() {
        return {
            prefix: document.getElementById('prefix-select')?.value || '',
            root: document.getElementById('root-select')?.value || '',
            suffix: document.getElementById('suffix-select')?.value || '',
        };
    }

    function updateLivePreview() {
        const { prefix, root, suffix } = getBuilderValues();
        const norm = s => (s || '').replace(/^-+|-+$/g, '');
        let built = norm(prefix) + norm(root) + norm(suffix);
        // combining vowel
        const r = norm(root), s = norm(suffix);
        if (r && s && /[aeiou]$/.test(r) && /^[aeiou]/.test(s)) {
            built = norm(prefix) + r.slice(0, -1) + s;
        }
        const preview = document.getElementById('term-preview');
        const chips = document.getElementById('builder-chips');
        if (preview) preview.textContent = built || '—';
        if (chips) {
            const parts = [];
            if (prefix) parts.push(`<span class="builder-part-chip prefix">${prefix}</span>`);
            if (root) parts.push(`<span class="builder-part-chip root">${root}</span>`);
            if (suffix) parts.push(`<span class="builder-part-chip suffix">${suffix}</span>`);
            chips.innerHTML = parts.join('') || '<span class="text-ward-600 text-xs">Select parts above</span>';
        }
    }

    function scheduleLiveBuild() {
        clearTimeout(liveBuildTimeout);
        updateLivePreview();
        const { root } = getBuilderValues();
        if (!root) return;
        liveBuildTimeout = setTimeout(buildTerm, 600);
    }

    async function buildTerm() {
        const { prefix, root, suffix } = getBuilderValues();
        if (!root) return;
        const res = await fetch('/api/terminology/build', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prefix, root, suffix }),
        });
        const data = await res.json();
        renderBuildResult(data);
        reportProgress(1, 'word_builder');
    }

    function renderBuildResult(data) {
        const el = document.getElementById('build-result');
        if (!el) return;
        const components = data.components.map(c =>
            `<div class="flex gap-2 py-1 text-sm">
                <span class="font-mono text-ward-accent w-24">${c.element}</span>
                <span class="text-ward-600 w-14 text-xs uppercase">${c.type}</span>
                <span class="text-ward-300">${c.meaning}</span>
            </div>`
        ).join('');
        el.innerHTML = `
            <div class="builder-preview-box mb-4">
                <div class="text-xs text-ward-500 uppercase tracking-wide mb-1">Constructed Term</div>
                <div class="builder-preview-term">${data.built_term}</div>
            </div>
            <div class="mb-4">${components}</div>
            <div class="card p-3 mb-3 bg-ward-900/80">
                <div class="text-xs text-ward-500 uppercase mb-1">Definition</div>
                <div class="text-ward-100">${data.likely_meaning}</div>
            </div>
            <div class="clinical-callout mb-3">
                <div class="clinical-callout-label">Why this matters for nursing</div>
                ${data.clinical_note}
            </div>
            <button onclick='showSource(${JSON.stringify(data.source)})' class="btn-verify text-xs">Verify Source</button>
        `;
        document.getElementById('term-preview').textContent = data.built_term;
    }

    // ── Database ──────────────────────────────────────────────────────────────
    function debounceSearch() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(searchTerms, 280);
    }

    async function searchTerms() {
        const q = document.getElementById('term-search')?.value || '';
        const cat = document.getElementById('category-filter')?.value || '';
        const params = new URLSearchParams({ limit: '60' });
        if (q) params.set('q', q);
        if (cat) params.set('category', cat);

        const res = await fetch('/api/terminology/terms?' + params);
        const data = await res.json();
        const container = document.getElementById('search-results');
        const countEl = document.getElementById('search-count');
        if (countEl) countEl.textContent = `${data.total} terms`;

        if (!data.terms.length) {
            container.innerHTML = '<p class="text-ward-500 text-sm py-4">No terms found. Try a different search.</p>';
            return;
        }

        container.innerHTML = data.terms.map(t => `
            <div class="term-card" onclick="Terminology.toggleTermDetail(this)" data-term="${t.term}">
                <div class="flex justify-between items-start gap-2">
                    <div>
                        <span class="term-card-name">${t.term}</span>
                        <span class="term-card-cat ml-2">${t.category || 'general'}</span>
                    </div>
                    <button onclick="event.stopPropagation(); showSource(${JSON.stringify(t.source || data.source)})" class="btn-verify text-xs shrink-0">Verify</button>
                </div>
                <p class="text-sm text-ward-400 mt-1 line-clamp-2">${t.definition}</p>
                <div class="term-detail-panel hidden">
                    ${t.breakdown ? `<p class="text-xs text-ward-500 mb-1"><strong>Breakdown:</strong> ${t.breakdown}</p>` : ''}
                    ${t.clinical_relevance ? `<div class="clinical-callout mt-2"><div class="clinical-callout-label">Why this matters</div>${t.clinical_relevance}</div>` : ''}
                </div>
            </div>
        `).join('');
    }

    function toggleTermDetail(el) {
        const panel = el.querySelector('.term-detail-panel');
        const wasHidden = panel.classList.contains('hidden');
        document.querySelectorAll('.term-card').forEach(c => {
            c.classList.remove('expanded');
            c.querySelector('.term-detail-panel')?.classList.add('hidden');
        });
        if (wasHidden) {
            panel.classList.remove('hidden');
            el.classList.add('expanded');
            const term = el.querySelector('.term-name')?.textContent?.trim();
            const def = el.querySelector('.term-definition')?.textContent?.trim();
            window.WardSocratic?.setModuleContext({
                module: 'terminology',
                tab: 'database',
                subject: term || 'Medical term',
                snippet: def || '',
            });
        }
    }

    // ── Flashcards + SRS ──────────────────────────────────────────────────────
    async function loadFlashcards(count, dueOnly = false) {
        const res = await fetch(`/api/terminology/flashcards?count=${count}&due_only=${dueOnly}`);
        const data = await res.json();
        flashcards = data.cards;
        cardIndex = 0;
        cardFlipped = false;
        updateFlashcardStats(data.stats);
        showCard();
    }

    function updateFlashcardStats(stats) {
        const el = document.getElementById('fc-stats');
        if (!el || !stats) return;
        el.innerHTML = `
            <span class="stat-pill">Due: <strong>${stats.due_today}</strong></span>
            <span class="stat-pill">Mastered: <strong>${stats.mastered}</strong></span>
            <span class="stat-pill">Total: <strong>${stats.total_cards}</strong></span>
        `;
    }

    function showCard() {
        if (!flashcards.length) {
            document.getElementById('flashcard-stage').innerHTML =
                '<p class="text-ward-500 text-center py-8">No cards loaded.</p>';
            return;
        }
        const card = flashcards[cardIndex];
        const inner = document.getElementById('flashcard-inner');
        inner.classList.remove('flipped');
        cardFlipped = false;

        document.getElementById('fc-front').textContent = card.front;
        document.getElementById('fc-back-def').textContent = card.back;
        document.getElementById('fc-back-clinical').textContent = card.clinical || '';
        document.getElementById('fc-breakdown').textContent = card.breakdown || '';
        const verifyBtn = document.getElementById('fc-verify-source');
        if (verifyBtn) {
            if (card.source) {
                verifyBtn.classList.remove('hidden');
                verifyBtn.onclick = (e) => {
                    e.stopPropagation();
                    showSource(card.source);
                };
            } else {
                verifyBtn.classList.add('hidden');
            }
        }
        document.getElementById('flashcard-counter').textContent = `${cardIndex + 1} / ${flashcards.length}`;
        document.getElementById('fc-front-view').classList.remove('hidden');
        document.getElementById('fc-back-view').classList.add('hidden');
        document.querySelectorAll('.srs-btn').forEach(b => b.disabled = true);
    }

    function flipCard() {
        if (!flashcards.length) return;
        cardFlipped = !cardFlipped;
        const inner = document.getElementById('flashcard-inner');
        inner.classList.toggle('flipped', cardFlipped);
        document.getElementById('fc-front-view').classList.toggle('hidden', cardFlipped);
        document.getElementById('fc-back-view').classList.toggle('hidden', !cardFlipped);
        if (cardFlipped) {
            document.querySelectorAll('.srs-btn').forEach(b => b.disabled = false);
        }
    }

    function nextCard() { if (cardIndex < flashcards.length - 1) { cardIndex++; showCard(); } }
    function prevCard() { if (cardIndex > 0) { cardIndex--; showCard(); } }

    async function rateCard(quality) {
        const card = flashcards[cardIndex];
        await fetch('/api/terminology/flashcards/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ card_key: card.key, quality }),
        });
        if (cardIndex >= flashcards.length - 1) {
            await loadFlashcards(20, true);
        } else {
            nextCard();
        }
    }

    // ── Practice ──────────────────────────────────────────────────────────────
    function setPracticeMode(mode) {
        practiceMode = mode;
        document.querySelectorAll('.mode-pill').forEach(p => {
            p.classList.toggle('active', p.dataset.mode === mode);
        });
    }

    async function startPractice(count) {
        const res = await fetch(`/api/terminology/practice?count=${count}&mode=${practiceMode}`);
        const data = await res.json();
        practiceQuestions = data.questions;
        practiceIndex = 0;
        practiceCorrect = 0;
        showPracticeQuestion();
    }

    function showPracticeQuestion() {
        const area = document.getElementById('practice-question-area');
        const scoreEl = document.getElementById('practice-score');

        if (practiceIndex >= practiceQuestions.length) {
            const pct = practiceQuestions.length
                ? Math.round((practiceCorrect / practiceQuestions.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-ward-accent mb-2">${practiceCorrect}/${practiceQuestions.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">${pct === 100 ? 'Outstanding!' : 'Review missed terms in the database.'}</p>
                </div>`;
            scoreEl.textContent = `Final: ${practiceCorrect}/${practiceQuestions.length}`;
            reportProgress(practiceCorrect, 'practice', pct);
            return;
        }

        const q = practiceQuestions[practiceIndex];
        scoreEl.textContent = `${practiceCorrect}/${practiceIndex}`;

        if (q.type === 'type_term') {
            area.innerHTML = `
                <div class="mb-2 text-xs text-ward-warning uppercase tracking-wide">Type the Term</div>
                <p class="text-ward-100 mb-4">${q.question}</p>
                ${q.hint ? `<p class="text-xs text-ward-500 mb-3">Hint: ${q.hint}</p>` : ''}
                <input type="text" id="type-answer" class="type-input" placeholder="Type your answer…" autocomplete="off"
                       onkeydown="if(event.key==='Enter')Terminology.submitTypedAnswer()">
                <button onclick="Terminology.submitTypedAnswer()" class="btn-primary w-full mt-3">Check Answer</button>
                <div id="practice-feedback" class="mt-4 hidden"></div>
            `;
            setTimeout(() => document.getElementById('type-answer')?.focus(), 100);
        } else {
            area.innerHTML = `
                <div class="mb-2 text-xs text-ward-accent uppercase tracking-wide">Multiple Choice</div>
                <p class="text-ward-100 mb-4">${q.question}</p>
                <div class="space-y-2" id="practice-options">
                    ${q.options.map((opt, i) => `
                        <button onclick="Terminology.answerMC(${i}, ${q.correct_index})" class="practice-option">
                            <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${opt}
                        </button>
                    `).join('')}
                </div>
                <div id="practice-feedback" class="mt-4 hidden"></div>
            `;
        }
    }

    function answerMC(selected, correct) {
        const q = practiceQuestions[practiceIndex];
        const isCorrect = selected === correct;
        if (isCorrect) practiceCorrect++;
        document.querySelectorAll('#practice-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (i === correct) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });
        showFeedback(isCorrect, q);
    }

    function submitTypedAnswer() {
        const q = practiceQuestions[practiceIndex];
        const input = document.getElementById('type-answer');
        const answer = (input?.value || '').trim().toLowerCase();
        const acceptable = q.acceptable_answers || [q.correct_answer.toLowerCase()];
        const isCorrect = acceptable.some(a => a.toLowerCase() === answer);
        if (isCorrect) practiceCorrect++;
        input.disabled = true;
        input.classList.add(isCorrect ? 'correct' : 'incorrect');
        showFeedback(isCorrect, q, q.correct_answer);
    }

    function showFeedback(isCorrect, q, correctAnswer) {
        const feedback = document.getElementById('practice-feedback');
        feedback.classList.remove('hidden');
        const src = JSON.stringify(q.source || {});
        feedback.innerHTML = `
            <div class="p-3 rounded-lg text-sm ${isCorrect ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                <p class="font-medium ${isCorrect ? 'text-ward-success' : 'text-ward-danger'}">${isCorrect ? 'Correct!' : `Incorrect — answer: ${correctAnswer || q.correct_answer}`}</p>
                <p class="text-ward-300 mt-1">${q.explanation}</p>
                <button onclick='showSource(${src})' class="btn-verify text-xs mt-2">Verify Source</button>
            </div>
            <button onclick="Terminology.nextPracticeQuestion()" class="btn-primary w-full mt-3">Next Question</button>
        `;
    }

    function nextPracticeQuestion() {
        practiceIndex++;
        showPracticeQuestion();
    }

    // ── Export ────────────────────────────────────────────────────────────────
    async function copyToClipboard(count = 50) {
        const res = await fetch(`/api/terminology/export/clipboard?count=${count}`);
        const data = await res.json();
        const label = count >= getTermCount() ? 'All terms copied to clipboard!' : `${data.count || count} terms copied!`;
        await WardExport.copyToClipboard(data.content, label);
    }

    async function exportPDF(count = 50) {
        const res = await fetch(`/api/terminology/export/study-sheet?count=${count}`);
        const html = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const table = doc.querySelector('table');
        const meta = doc.querySelector('.meta')?.textContent || `${count} terms · Ehrlich & Schroeder, 8th Ed.`;
        WardExport.openPrintableHtml(
            'Medical Terminology Study Sheet',
            table ? table.outerHTML : doc.body.innerHTML,
            meta,
        );
    }

    async function exportMarkdown(count = 50) {
        const res = await fetch(`/api/terminology/export/flashcards?count=${count}`);
        const data = await res.json();
        const suffix = count >= getTermCount() ? 'all' : count;
        WardExport.downloadText(`ward-terminology-flashcards-${suffix}.md`, data.content, 'text/markdown;charset=utf-8');
    }

    // ── Custom Terms ──────────────────────────────────────────────────────────
    async function loadCustomTerms() {
        const res = await fetch('/api/terminology/custom');
        customTerms = await res.json();
        customTermsLoaded = true;
        renderCustomTerms();
    }

    function renderCustomTerms() {
        const list = document.getElementById('custom-terms-list');
        const countEl = document.getElementById('custom-term-count');
        if (!list) return;

        if (countEl) {
            const favCount = customTerms.filter(t => t.is_favorite).length;
            countEl.textContent = favCount
                ? `${customTerms.length} saved · ${favCount} favorited`
                : `${customTerms.length} saved`;
        }

        if (!customTerms.length) {
            list.innerHTML = '<p class="text-ward-500 text-sm py-4">No custom terms yet — add one to get started.</p>';
            return;
        }

        list.innerHTML = customTerms.map(t => {
            const parts = [t.prefix, t.root, t.suffix].filter(Boolean);
            const breakdown = parts.length ? parts.join(' + ') : '';
            return `
                <div class="custom-term-item${t.is_favorite ? ' is-favorite' : ''}" data-id="${t.id}">
                    <div class="flex justify-between items-start gap-2">
                        <div class="min-w-0 flex-1">
                            <span class="custom-term-name">${escapeHtml(t.term)}</span>
                            ${breakdown ? `<span class="custom-term-breakdown">${escapeHtml(breakdown)}</span>` : ''}
                        </div>
                        <button type="button"
                                class="custom-fav-btn${t.is_favorite ? ' active' : ''}"
                                title="${t.is_favorite ? 'Remove from favorites' : 'Add to favorites'}"
                                onclick="Terminology.toggleCustomFavorite(${t.id}, ${!t.is_favorite})">
                            ${t.is_favorite ? '★' : '☆'}
                        </button>
                    </div>
                    <p class="custom-term-def">${escapeHtml(t.definition)}</p>
                    ${t.clinical_note ? `<p class="custom-term-clinical">${escapeHtml(t.clinical_note)}</p>` : ''}
                </div>
            `;
        }).join('');
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    }

    function updateCustomPreview() {
        const prefix = document.getElementById('custom-prefix')?.value.trim() || '';
        const root = document.getElementById('custom-root')?.value.trim() || '';
        const suffix = document.getElementById('custom-suffix')?.value.trim() || '';
        const preview = document.getElementById('custom-breakdown-preview');
        const textEl = document.getElementById('custom-breakdown-text');
        if (!preview || !textEl) return;

        const parts = [prefix, root, suffix].filter(Boolean);
        if (!parts.length) {
            preview.classList.add('hidden');
            textEl.textContent = '';
            return;
        }
        preview.classList.remove('hidden');
        textEl.textContent = parts.join(' + ');
    }

    async function submitCustomTerm(event) {
        event.preventDefault();
        const statusEl = document.getElementById('custom-term-status');
        const payload = {
            term: document.getElementById('custom-term')?.value.trim(),
            definition: document.getElementById('custom-definition')?.value.trim(),
            prefix: document.getElementById('custom-prefix')?.value.trim() || null,
            root: document.getElementById('custom-root')?.value.trim() || null,
            suffix: document.getElementById('custom-suffix')?.value.trim() || null,
            clinical_note: document.getElementById('custom-clinical')?.value.trim() || null,
        };

        if (!payload.term || !payload.definition) return;

        const res = await fetch('/api/terminology/custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            if (statusEl) {
                statusEl.textContent = 'Failed to save term — try again.';
                statusEl.classList.remove('hidden', 'text-ward-success');
                statusEl.classList.add('text-ward-danger');
            }
            return;
        }

        const saved = await res.json();
        customTerms.push(saved);
        customTerms.sort((a, b) => {
            if (a.is_favorite !== b.is_favorite) return b.is_favorite - a.is_favorite;
            return a.term.localeCompare(b.term);
        });
        renderCustomTerms();

        document.getElementById('custom-term-form')?.reset();
        updateCustomPreview();
        if (statusEl) {
            statusEl.textContent = `"${saved.term}" saved to My Terms.`;
            statusEl.classList.remove('hidden', 'text-ward-danger');
            statusEl.classList.add('text-ward-success');
        }
    }

    async function toggleCustomFavorite(termId, isFavorite) {
        const res = await fetch(`/api/terminology/custom/${termId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_favorite: isFavorite }),
        });
        if (!res.ok) return;

        const updated = await res.json();
        customTerms = customTerms.map(t => (t.id === termId ? updated : t));
        customTerms.sort((a, b) => {
            if (a.is_favorite !== b.is_favorite) return b.is_favorite - a.is_favorite;
            return a.term.localeCompare(b.term);
        });
        renderCustomTerms();
    }

    async function exportJSON() {
        const res = await fetch('/api/terminology/export/json');
        const data = await res.json();
        const json = JSON.stringify(data, null, 2);
        WardExport.downloadText(
            'ward-terminology-all-terms.json',
            json,
            'application/json;charset=utf-8',
        );
    }

    // ── Progress ──────────────────────────────────────────────────────────────
    async function reportProgress(items, activityType, score) {
        await fetch('/api/terminology/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items_studied: items, activity_type: activityType, score: score ?? null }),
        });
        refreshModuleProgress();
    }

    async function refreshModuleProgress() {
        const res = await fetch('/api/terminology/stats');
        const data = await res.json();
        const bar = document.getElementById('module-progress-bar');
        const pct = document.getElementById('module-progress-pct');
        if (bar) bar.style.width = data.percentage + '%';
        if (pct) pct.textContent = data.percentage + '%';
    }

    // ── Init ──────────────────────────────────────────────────────────────────
    function init() {
        ['prefix-select', 'root-select', 'suffix-select'].forEach(id => {
            document.getElementById(id)?.addEventListener('change', scheduleLiveBuild);
        });
        updateLivePreview();
        WardTabs.register('/modules/terminology', { validTabs: VALID_TABS, defaultTab: DEFAULT_TAB, switchTab });
        WardTabs.init('/modules/terminology');
    }

    return {
        switchTab, buildTerm, debounceSearch, searchTerms, toggleTermDetail,
        loadFlashcards, flipCard, nextCard, prevCard, rateCard,
        setPracticeMode, startPractice, answerMC, submitTypedAnswer, nextPracticeQuestion,
        copyToClipboard, exportPDF, exportMarkdown, exportJSON,
        loadCustomTerms, submitCustomTerm, updateCustomPreview, toggleCustomFavorite,
        init,
    };
})();

document.addEventListener('DOMContentLoaded', () => Terminology.init());