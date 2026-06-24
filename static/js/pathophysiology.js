/**
 * The Ward — Pathophysiology Module
 */
const Pathophysiology = (() => {
    const MODULE_ID = 'pathophysiology';
    const VALID_TABS = ['core-concepts', 'disease-processes', 'compare-contrast', 'what-breaks-down', 'flashcards', 'practice'];
    const DEFAULT_TAB = 'core-concepts';
    const esc = (s) => (WardExport?.escapeHtml || escapeHtml)(String(s ?? ''));

    let conceptsData = null;
    let diseasesData = null;
    let compareData = null;

    let breakdownScenarios = [];
    let breakdownIndex = 0;
    let breakdownCorrect = 0;

    let flashcards = [];
    let cardIndex = 0;
    let cardFlipped = false;

    let practiceQuestions = [];
    let practiceIndex = 0;
    let practiceCorrect = 0;

    const TAB_LABELS = {
        'core-concepts': 'Core Concepts',
        'disease-processes': 'Disease Processes',
        'compare-contrast': 'Compare & Contrast',
        'what-breaks-down': 'What Breaks Down',
        flashcards: 'Flashcards',
        practice: 'NCLEX Practice',
    };

    function switchTab(tab) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.querySelectorAll('.patho-tab-btn').forEach(b => b.classList.remove('active'));
        const panel = document.getElementById('tab-' + tab);
        const btn = document.querySelector(`[data-tab="${tab}"]`);
        if (panel) panel.classList.remove('hidden');
        if (btn) btn.classList.add('active');

        if (tab === 'core-concepts' && !conceptsData) loadConcepts();
        if (tab === 'disease-processes' && !diseasesData) loadDiseases();
        if (tab === 'compare-contrast' && !compareData) loadCompare();
        if (tab === 'what-breaks-down' && !breakdownScenarios.length) loadBreakdownScenarios();
        if (tab === 'flashcards' && !flashcards.length) loadFlashcards(10);
        if (tab === 'practice' && !practiceQuestions.length) {
            const area = document.getElementById('patho-practice-area');
            if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Choose a session size below.</p>';
        }

        history.replaceState(null, '', location.pathname + (tab !== DEFAULT_TAB ? '#' + tab : ''));
        window.WardSocratic?.setModuleContext({
            module: MODULE_ID,
            tab,
            subject: `Pathophysiology · ${TAB_LABELS[tab] || tab}`,
            topic: 'pathophysiology',
        });
    }

    async function reportProgress(items, activityType, score) {
        await fetch('/api/pathophysiology/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items_studied: items, activity_type: activityType, score: score ?? null }),
        });
        refreshModuleProgress();
    }

    async function refreshModuleProgress() {
        const res = await fetch('/api/pathophysiology/stats');
        const data = await res.json();
        const bar = document.getElementById('module-progress-bar');
        const pct = document.getElementById('module-progress-pct');
        if (bar) bar.style.width = data.percentage + '%';
        if (pct) pct.textContent = data.percentage + '%';
    }

    // ── Core Concepts ─────────────────────────────────────────────────────────
    async function loadConcepts() {
        const el = document.getElementById('patho-concepts-container');
        try {
            const res = await fetch('/api/pathophysiology/concepts');
            const data = await res.json();
            conceptsData = data;
            renderConcepts(el);
        } catch {
            if (el) el.innerHTML = '<p class="text-ward-danger text-sm">Failed to load concepts.</p>';
        }
    }

    function renderConcepts(el) {
        if (!el || !conceptsData) return;
        const concepts = conceptsData.concepts || [];
        el.innerHTML = `
            <p class="text-xs text-ward-500 mb-3">${concepts.length} foundational concepts — expand each to study the cascade</p>
            <div class="patho-concept-list">
                ${concepts.map(c => `
                    <details class="patho-concept-card" data-id="${esc(c.id)}">
                        <summary class="patho-concept-summary">
                            <span class="patho-concept-name">${esc(c.title)}</span>
                            <span class="patho-concept-toggle">Expand</span>
                        </summary>
                        <div class="patho-concept-body">
                            <p class="text-xs text-ward-400 italic">${esc(c.summary || '')}</p>
                            <p class="patho-concept-desc">${esc(c.content || '')}</p>
                            ${c.clinical_relevance ? `<div class="patho-clinical-box"><strong>Clinical:</strong> ${esc(c.clinical_relevance)}</div>` : ''}
                            ${c.nursing_focus ? `<div class="patho-nursing-box"><strong>RN Focus:</strong> ${esc(c.nursing_focus)}</div>` : ''}
                            ${c.source_ref ? `<button type="button" class="btn-verify text-xs mt-2" onclick='showSource(${JSON.stringify(c.source_ref)})'>Verify Source</button>` : ''}
                            <button type="button" class="text-xs text-rose-400 hover:underline mt-2 block"
                                    onclick="Pathophysiology.askSocratic('${esc(c.title)}', '${esc((c.content || '').slice(0, 200))}')">
                                Ask Socratic tutor →
                            </button>
                        </div>
                    </details>
                `).join('')}
            </div>`;

        el.querySelectorAll('.patho-concept-card').forEach(card => {
            card.addEventListener('toggle', () => {
                if (!card.open) return;
                const concept = concepts.find(c => c.id === card.dataset.id);
                if (concept) {
                    window.WardSocratic?.setModuleContext({
                        module: MODULE_ID,
                        tab: 'core-concepts',
                        subject: concept.title,
                        snippet: (concept.content || '').slice(0, 400),
                        topic: 'pathophysiology',
                    });
                    reportProgress(1, 'concepts');
                }
            });
        });
    }

    // ── Disease Processes ─────────────────────────────────────────────────────
    async function loadDiseases() {
        const el = document.getElementById('patho-diseases-container');
        try {
            const res = await fetch('/api/pathophysiology/diseases');
            const data = await res.json();
            diseasesData = data;
            renderDiseases(el);
        } catch {
            if (el) el.innerHTML = '<p class="text-ward-danger text-sm">Failed to load disease processes.</p>';
        }
    }

    function renderDiseases(el) {
        if (!el || !diseasesData) return;
        const diseases = diseasesData.diseases || [];
        el.innerHTML = `
            <div class="patho-disease-grid">
                ${diseases.map(d => `
                    <div class="patho-disease-card">
                        <div class="patho-disease-name">${esc(d.name)}</div>
                        <span class="patho-disease-cat">${esc(d.category || '')}</span>
                        <div class="patho-disease-section">
                            <div class="patho-disease-label">Etiology</div>
                            <p class="patho-disease-text">${esc(d.etiology || '')}</p>
                        </div>
                        <div class="patho-disease-section">
                            <div class="patho-disease-label">Patho Cascade</div>
                            <ul class="patho-cascade-list">
                                ${(d.patho_cascade || []).map(step => `<li>${esc(step)}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="patho-disease-section">
                            <div class="patho-disease-label">Clinical Manifestations</div>
                            <p class="patho-disease-text">${(d.clinical_manifestations || []).map(m => esc(m)).join(' · ')}</p>
                        </div>
                        <div class="patho-disease-section">
                            <div class="patho-disease-label">Nursing Priorities</div>
                            <ul class="patho-cascade-list">
                                ${(d.nursing_priorities || []).map(p => `<li>${esc(p)}</li>`).join('')}
                            </ul>
                        </div>
                        ${d.source_ref ? `<button type="button" class="btn-verify text-xs mt-2" onclick='showSource(${JSON.stringify(d.source_ref)})'>Verify Source</button>` : ''}
                    </div>
                `).join('')}
            </div>`;
        reportProgress(1, 'diseases');
    }

    // ── Compare & Contrast ────────────────────────────────────────────────────
    async function loadCompare() {
        const el = document.getElementById('patho-compare-container');
        try {
            const res = await fetch('/api/pathophysiology/compare');
            const data = await res.json();
            compareData = data;
            renderCompare(el);
        } catch {
            if (el) el.innerHTML = '<p class="text-ward-danger text-sm">Failed to load compare/contrast content.</p>';
        }
    }

    function renderCompare(el) {
        if (!el || !compareData) return;
        const pairs = compareData.pairs || [];
        el.innerHTML = `
            <div class="patho-compare-grid">
                ${pairs.map(p => `
                    <div class="patho-compare-card">
                        <div class="patho-compare-title">${esc(p.title)}</div>
                        <div class="patho-compare-columns">
                            <div class="patho-compare-col patho-compare-col-a">
                                <div class="patho-compare-col-name">${esc(p.condition_a?.name || 'A')}</div>
                                <ul class="patho-compare-features">
                                    ${(p.condition_a?.key_features || []).map(f => `<li>${esc(f)}</li>`).join('')}
                                </ul>
                            </div>
                            <div class="patho-compare-col patho-compare-col-b">
                                <div class="patho-compare-col-name">${esc(p.condition_b?.name || 'B')}</div>
                                <ul class="patho-compare-features">
                                    ${(p.condition_b?.key_features || []).map(f => `<li>${esc(f)}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        ${p.clinical_pearls ? `<div class="patho-pearl"><strong>Pearl:</strong> ${esc(p.clinical_pearls)}</div>` : ''}
                        ${p.nclex_tip ? `<div class="patho-pearl mt-2"><strong>NCLEX:</strong> ${esc(p.nclex_tip)}</div>` : ''}
                        ${p.source_ref ? `<button type="button" class="btn-verify text-xs mt-2" onclick='showSource(${JSON.stringify(p.source_ref)})'>Verify Source</button>` : ''}
                    </div>
                `).join('')}
            </div>`;
        reportProgress(1, 'compare');
    }

    // ── What Breaks Down Scenarios ────────────────────────────────────────────
    async function loadBreakdownScenarios() {
        const area = document.getElementById('patho-scenario-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading scenarios…</p>';
        const res = await fetch('/api/pathophysiology/scenarios/breakdown?count=5');
        const data = await res.json();
        breakdownScenarios = data.scenarios || [];
        breakdownIndex = 0;
        breakdownCorrect = 0;
        showBreakdownScenario();
    }

    function showBreakdownScenario() {
        const area = document.getElementById('patho-scenario-area');
        const scoreEl = document.getElementById('patho-scenario-score');
        if (!area) return;

        if (breakdownIndex >= breakdownScenarios.length) {
            const pct = breakdownScenarios.length
                ? Math.round((breakdownCorrect / breakdownScenarios.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-ward-success mb-2">${breakdownCorrect}/${breakdownScenarios.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">Review disease processes and core concepts for missed mechanisms.</p>
                    <button onclick="Pathophysiology.loadBreakdownScenarios()" class="btn-primary mt-4 text-sm">New Scenarios</button>
                </div>`;
            if (scoreEl) scoreEl.textContent = `Final: ${breakdownCorrect}/${breakdownScenarios.length}`;
            reportProgress(breakdownCorrect, 'scenarios', pct);
            return;
        }

        const s = breakdownScenarios[breakdownIndex];
        if (scoreEl) scoreEl.textContent = `${breakdownCorrect}/${breakdownIndex}`;

        const cascadeHtml = (s.cascade || []).map(c => `<li>${esc(c)}</li>`).join('');
        const signsHtml = (s.clinical_signs || []).map(c => `<li>${esc(c)}</li>`).join('');

        area.innerHTML = `
            <div class="patho-breakdown-card">
                <div class="patho-breakdown-title">${esc(s.title)}</div>
                <div class="patho-breakdown-section"><span class="patho-breakdown-label">Trigger:</span> ${esc(s.trigger || '')}</div>
                <div class="patho-breakdown-section"><span class="patho-breakdown-label">Normal:</span> ${esc(s.normal_function || '')}</div>
                <div class="patho-breakdown-section"><span class="patho-breakdown-label">Breakdown:</span> ${esc(s.breakdown || '')}</div>
                ${cascadeHtml ? `<div class="patho-breakdown-section"><span class="patho-breakdown-label">Cascade:</span><ul class="patho-cascade-list">${cascadeHtml}</ul></div>` : ''}
                ${signsHtml ? `<div class="patho-breakdown-section"><span class="patho-breakdown-label">Clinical Signs:</span><ul class="patho-cascade-list">${signsHtml}</ul></div>` : ''}
                <div class="patho-breakdown-section"><span class="patho-breakdown-label">RN Response:</span> ${esc(s.nursing_response || '')}</div>
                <hr class="border-ward-700 my-4">
                <p class="text-sm font-medium text-ward-200 mb-3">${esc(s.question)}</p>
                <div class="space-y-2" id="patho-scenario-options">
                    ${(s.options || []).map((opt, i) => `
                        <button type="button" class="practice-option" onclick="Pathophysiology.answerBreakdown(${i})">
                            <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${esc(opt)}
                        </button>
                    `).join('')}
                </div>
                <div id="patho-scenario-feedback" class="mt-4 hidden"></div>
            </div>
            <p class="text-center text-xs text-ward-600 mt-3">Scenario ${breakdownIndex + 1} of ${breakdownScenarios.length}</p>`;
    }

    async function answerBreakdown(selected) {
        const s = breakdownScenarios[breakdownIndex];
        const res = await fetch('/api/pathophysiology/scenarios/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario_id: s.id,
                selected_index: selected,
                selected_option: s.options[selected],
            }),
        });
        const result = await res.json();
        if (result.correct) breakdownCorrect++;

        document.querySelectorAll('#patho-scenario-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (i === result.correct_index) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('patho-scenario-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${result.correct ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${result.correct ? 'text-ward-success' : 'text-ward-danger'}">${esc(result.feedback)}</p>
                    <p class="text-ward-300 mt-1">${esc(result.explanation)}</p>
                    ${result.clinical_why ? `<p class="text-xs text-ward-accent mt-2">${esc(result.clinical_why)}</p>` : ''}
                    <button onclick="Pathophysiology.nextBreakdown()" class="btn-primary text-xs mt-3">Next →</button>
                </div>`;
        }
    }

    function nextBreakdown() {
        breakdownIndex++;
        showBreakdownScenario();
    }

    // ── Flashcards ────────────────────────────────────────────────────────────
    async function loadFlashcards(count, shuffle = false) {
        const url = count
            ? `/api/pathophysiology/flashcards?count=${count}`
            : '/api/pathophysiology/flashcards';
        const res = await fetch(url);
        const data = await res.json();
        flashcards = data.cards || [];
        if (shuffle && flashcards.length > 1) {
            flashcards = flashcards.sort(() => Math.random() - 0.5);
        }
        cardIndex = 0;
        cardFlipped = false;
        showCard();
        reportProgress(flashcards.length, 'flashcards');
    }

    function renderFcDots() {
        const dots = document.getElementById('patho-fc-dots');
        if (!dots) return;
        dots.innerHTML = flashcards.map((c, i) => {
            const cls = ['patho-fc-dot', i === cardIndex ? 'active' : ''].filter(Boolean).join(' ');
            return `<button type="button" class="${cls}" aria-label="Go to card ${i + 1}" onclick="Pathophysiology.goToCard(${i})"></button>`;
        }).join('');
    }

    function goToCard(index) {
        if (index < 0 || index >= flashcards.length) return;
        cardIndex = index;
        showCard();
    }

    function showCard() {
        if (!flashcards.length) {
            const stage = document.getElementById('patho-flashcard-stage');
            if (stage) stage.innerHTML = '<p class="text-ward-500 text-center py-8">No cards loaded.</p>';
            return;
        }
        const card = flashcards[cardIndex];
        cardFlipped = false;
        document.getElementById('pfc-front').textContent = card.front || '';
        const catEl = document.getElementById('pfc-category');
        if (catEl) catEl.textContent = card.category || '';
        document.getElementById('pfc-back').textContent = card.back || '';
        document.getElementById('pfc-clinical').textContent = card.clinical_why || '';
        document.getElementById('pfc-front-view')?.classList.remove('hidden');
        document.getElementById('pfc-back-view')?.classList.add('hidden');
        document.getElementById('patho-flashcard-counter').textContent = `${cardIndex + 1} / ${flashcards.length}`;
        renderFcDots();
    }

    function flipCard() {
        if (!flashcards.length) return;
        cardFlipped = !cardFlipped;
        document.getElementById('pfc-front-view')?.classList.toggle('hidden', cardFlipped);
        document.getElementById('pfc-back-view')?.classList.toggle('hidden', !cardFlipped);
        if (cardFlipped) reportProgress(1, 'flashcards');
    }

    function nextCard() {
        if (cardIndex < flashcards.length - 1) { cardIndex++; showCard(); }
    }

    function prevCard() {
        if (cardIndex > 0) { cardIndex--; showCard(); }
    }

    function handleFlashcardKeys(e) {
        const panel = document.getElementById('tab-flashcards');
        if (!panel || panel.classList.contains('hidden') || !flashcards.length) return;
        if (e.target.matches('input, textarea, select')) return;
        if (e.key === ' ' || e.key === 'Spacebar') { e.preventDefault(); flipCard(); }
        else if (e.key === 'ArrowRight') { e.preventDefault(); nextCard(); }
        else if (e.key === 'ArrowLeft') { e.preventDefault(); prevCard(); }
    }

    document.addEventListener('keydown', handleFlashcardKeys);

    // ── Practice ──────────────────────────────────────────────────────────────
    async function startPractice(count) {
        const area = document.getElementById('patho-practice-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading questions…</p>';
        const res = await fetch(`/api/pathophysiology/practice?count=${count}`);
        const data = await res.json();
        practiceQuestions = data.questions || [];
        practiceIndex = 0;
        practiceCorrect = 0;
        showPracticeQuestion();
    }

    function showPracticeQuestion() {
        const area = document.getElementById('patho-practice-area');
        const scoreEl = document.getElementById('patho-practice-score');
        if (!area) return;

        if (practiceIndex >= practiceQuestions.length) {
            const pct = practiceQuestions.length
                ? Math.round((practiceCorrect / practiceQuestions.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-ward-success mb-2">${practiceCorrect}/${practiceQuestions.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <button onclick="Pathophysiology.startPractice(10)" class="btn-primary mt-4 text-sm">Try Again (10)</button>
                </div>`;
            if (scoreEl) scoreEl.textContent = `Final: ${practiceCorrect}/${practiceQuestions.length}`;
            reportProgress(practiceCorrect, 'practice', pct);
            return;
        }

        const q = practiceQuestions[practiceIndex];
        if (scoreEl) scoreEl.textContent = `${practiceCorrect}/${practiceIndex}`;

        area.innerHTML = `
            <div class="scenario-card">
                <p class="text-sm text-ward-200 mb-4">${esc(q.question)}</p>
                <div class="space-y-2" id="patho-practice-options">
                    ${(q.options || []).map((opt, i) => `
                        <button type="button" class="practice-option" onclick="Pathophysiology.answerPractice(${i})">
                            <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${esc(opt)}
                        </button>
                    `).join('')}
                </div>
                <div id="patho-practice-feedback" class="mt-4 hidden"></div>
            </div>
            <p class="text-center text-xs text-ward-600 mt-3">Question ${practiceIndex + 1} of ${practiceQuestions.length}</p>`;
    }

    function answerPractice(selected) {
        const q = practiceQuestions[practiceIndex];
        const isCorrect = selected === q.correct_index;
        if (isCorrect) practiceCorrect++;

        document.querySelectorAll('#patho-practice-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (i === q.correct_index) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('patho-practice-feedback');
        if (feedback) {
            const src = q.source_ref ? `<button onclick='showSource(${JSON.stringify(q.source_ref)})' class="btn-verify text-xs mt-2">Verify Source</button>` : '';
            feedback.classList.remove('hidden');
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${isCorrect ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${isCorrect ? 'text-ward-success' : 'text-ward-danger'}">${isCorrect ? 'Correct!' : 'Incorrect.'}</p>
                    <p class="text-ward-300 mt-1">${esc(q.rationale || '')}</p>
                    ${q.nclex_category ? `<p class="text-xs text-ward-500 mt-2">${esc(q.nclex_category)}</p>` : ''}
                    ${src}
                </div>
                <button onclick="Pathophysiology.nextPractice()" class="btn-primary w-full mt-3 text-sm">Next Question</button>`;
        }
    }

    function nextPractice() {
        practiceIndex++;
        showPracticeQuestion();
    }

    async function exportFlashcardDeck() {
        try {
            const res = await fetch('/api/pathophysiology/export/flashcards');
            if (!res.ok) throw new Error('export failed');
            const data = await res.json();
            if (typeof WardExport !== 'undefined') {
                WardExport.downloadText('ward-pathophysiology-flashcards.md', data.content, 'text/markdown;charset=utf-8');
            }
            if (typeof showToast === 'function') showToast('Flashcard deck exported.');
        } catch {
            if (typeof showToast === 'function') showToast('Export failed.', 'error');
        }
    }

    function askSocratic(subject, snippet) {
        window.WardSocratic?.setModuleContext({
            module: MODULE_ID,
            tab: 'core-concepts',
            subject,
            snippet,
            topic: 'pathophysiology',
        });
        openSocraticMode(MODULE_ID, 'pathophysiology');
    }

    function init() {
        WardTabs.register('/modules/pathophysiology', { validTabs: VALID_TABS, defaultTab: DEFAULT_TAB, switchTab });
        WardTabs.init('/modules/pathophysiology');
        loadConcepts();
    }

    return {
        switchTab,
        init,
        loadConcepts,
        loadDiseases,
        loadCompare,
        loadBreakdownScenarios,
        answerBreakdown,
        nextBreakdown,
        loadFlashcards,
        goToCard,
        flipCard,
        nextCard,
        prevCard,
        startPractice,
        answerPractice,
        nextPractice,
        askSocratic,
        exportFlashcardDeck,
    };
})();