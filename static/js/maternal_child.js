/**
 * The Ward — NURS 148 Maternal-Child Nursing Module
 */
const MaternalChild = (() => {
    const MODULE_ID = 'maternal_child';
    const TABS = [
        'antepartum', 'intrapartum', 'postpartum-newborn', 'pediatrics',
        'safety', 'complications-drill', 'flashcards', 'practice',
    ];

    let antepartumData = null;
    let intrapartumData = null;
    let postpartumData = null;
    let pediatricsData = null;
    let safetyData = null;

    let drillQuestions = [];
    let drillIndex = 0;
    let drillCorrect = 0;

    let flashcards = [];
    let cardIndex = 0;
    let cardFlipped = false;
    const FC_RATINGS_KEY = 'ward_mc_flashcard_ratings';
    let fcRatings = loadFcRatings();

    let practiceQuestions = [];
    let practiceIndex = 0;
    let practiceCorrect = 0;

    function esc(s) {
        if (s == null) return '';
        const d = document.createElement('div');
        d.textContent = String(s);
        return d.innerHTML;
    }

    function switchTab(tab) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.querySelectorAll('.mc-tab-btn').forEach(b => b.classList.remove('active'));
        const panel = document.getElementById('tab-' + tab);
        const btn = document.querySelector(`[data-tab="${tab}"]`);
        if (panel) panel.classList.remove('hidden');
        if (btn) btn.classList.add('active');

        if (tab === 'antepartum' && !antepartumData) loadAntepartum();
        if (tab === 'intrapartum' && !intrapartumData) loadIntrapartum();
        if (tab === 'postpartum-newborn' && !postpartumData) loadPostpartum();
        if (tab === 'pediatrics' && !pediatricsData) loadPediatrics();
        if (tab === 'safety' && !safetyData) loadSafety();
        if (tab === 'complications-drill' && !drillQuestions.length) loadComplicationsDrill();
        if (tab === 'flashcards' && !flashcards.length) loadFlashcards(15);
        if (tab === 'practice' && !practiceQuestions.length) { /* wait for user */ }

        history.replaceState(null, '', location.pathname + (tab !== 'antepartum' ? '#' + tab : ''));

        const labels = {
            antepartum: 'Antepartum & Fetal Development',
            intrapartum: 'Labor & Delivery',
            'postpartum-newborn': 'Postpartum & Newborn',
            pediatrics: 'Pediatric Essentials',
            safety: 'Safety Red Flags',
            'complications-drill': 'Complications Drill',
            flashcards: 'Flashcards',
            practice: 'NCLEX Practice',
        };
        window.WardSocratic?.setModuleContext({
            module: MODULE_ID,
            tab,
            subject: labels[tab] || 'Maternal-Child Nursing',
            snippet: '',
            topic: 'assessment_finding',
        });
    }

    const DEFAULT_TAB = 'antepartum';

    async function reportProgress(items, activityType, score) {
        await fetch('/api/maternal-child/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items_studied: items, activity_type: activityType, score }),
        });
        refreshModuleProgress();
    }

    async function refreshModuleProgress() {
        try {
            const res = await fetch('/api/maternal-child/stats');
            const data = await res.json();
            const bar = document.getElementById('module-progress-bar');
            const pct = document.getElementById('module-progress-pct');
            if (bar) bar.style.width = `${data.percentage}%`;
            if (pct) pct.textContent = `${data.percentage}%`;
        } catch { /* non-fatal */ }
    }

    async function exportFlashcardDeck() {
        try {
            const res = await fetch('/api/maternal-child/export/flashcards');
            if (!res.ok) throw new Error('export failed');
            const data = await res.json();
            if (typeof WardExport !== 'undefined') {
                WardExport.downloadText('ward-maternal-child-flashcards.md', data.content, 'text/markdown;charset=utf-8');
            }
            if (typeof showToast === 'function') showToast('Flashcard deck exported.');
        } catch {
            if (typeof showToast === 'function') showToast('Export failed.', 'error');
        }
    }

    function refCardSummary(t) {
        return t.summary || t.content || '';
    }

    function refCardNursingAction(t) {
        if (t.nursing_action) return t.nursing_action;
        if (Array.isArray(t.nursing_actions) && t.nursing_actions.length) {
            return t.nursing_actions.join(' · ');
        }
        return '';
    }

    function renderRefCards(topics, el, tabName) {
        if (!el || !topics?.length) return;
        const cards = topics.map(t => {
            const summary = refCardSummary(t);
            const nursingAction = refCardNursingAction(t);
            const keyPoints = t.key_points || t.nursing_actions || [];
            return `
            <details class="mc-ref-card" data-id="${esc(t.id)}">
                <summary class="mc-ref-summary">
                    <span class="mc-ref-name">${esc(t.title)}</span>
                    <span class="mc-ref-cat">${esc(t.category || '')}</span>
                </summary>
                <div class="mc-ref-body">
                    ${summary ? `<p class="mc-ref-desc">${esc(summary)}</p>` : ''}
                    ${keyPoints.length ? `
                        <ul class="mc-ref-points">
                            ${keyPoints.map(p => `<li>${esc(p)}</li>`).join('')}
                        </ul>` : ''}
                    ${nursingAction ? `<div class="mc-callout-action"><strong>RN Action:</strong> ${esc(nursingAction)}</div>` : ''}
                    ${t.clinical_why ? `<p class="mc-clinical-why"><em>${esc(t.clinical_why)}</em></p>` : ''}
                    <button type="button" class="text-xs text-pink-400 hover:underline mt-2"
                            onclick="MaternalChild.askSocratic('${esc(t.title)}', '${esc(summary.slice(0, 200))}', '${tabName}')">
                        Ask Socratic tutor →
                    </button>
                </div>
            </details>`;
        }).join('');

        el.innerHTML = `
            <section class="mc-section">
                <p class="mc-section-desc">${topics.length} evidence-based reference topics</p>
                <div class="space-y-2">${cards}</div>
            </section>
        `;

        el.querySelectorAll('.mc-ref-card').forEach(card => {
            card.addEventListener('toggle', () => {
                if (!card.open) return;
                const topic = topics.find(t => t.id === card.dataset.id);
                if (topic) {
                    window.WardSocratic?.setModuleContext({
                        module: MODULE_ID,
                        tab: tabName,
                        subject: topic.title,
                        snippet: (topic.summary || '').slice(0, 400),
                        topic: 'assessment_finding',
                    });
                    reportProgress(1, tabName);
                }
            });
        });
    }

    async function loadAntepartum() {
        const el = document.getElementById('mc-antepartum-container');
        try {
            const res = await fetch('/api/maternal-child/antepartum');
            antepartumData = await res.json();
            renderRefCards(antepartumData.topics, el, 'antepartum');
        } catch {
            if (el) el.innerHTML = '<p class="text-ward-danger text-sm">Failed to load antepartum content.</p>';
        }
    }

    async function loadIntrapartum() {
        const el = document.getElementById('mc-intrapartum-container');
        try {
            const res = await fetch('/api/maternal-child/intrapartum');
            intrapartumData = await res.json();
            renderRefCards(intrapartumData.topics, el, 'intrapartum');
        } catch {
            if (el) el.innerHTML = '<p class="text-ward-danger text-sm">Failed to load intrapartum content.</p>';
        }
    }

    async function loadPostpartum() {
        const el = document.getElementById('mc-postpartum-container');
        try {
            const res = await fetch('/api/maternal-child/postpartum-newborn');
            postpartumData = await res.json();
            renderRefCards(postpartumData.topics, el, 'postpartum-newborn');
        } catch {
            if (el) el.innerHTML = '<p class="text-ward-danger text-sm">Failed to load postpartum content.</p>';
        }
    }

    async function loadPediatrics() {
        const el = document.getElementById('mc-pediatrics-container');
        try {
            const res = await fetch('/api/maternal-child/pediatrics');
            pediatricsData = await res.json();
            renderRefCards(pediatricsData.topics, el, 'pediatrics');
        } catch {
            if (el) el.innerHTML = '<p class="text-ward-danger text-sm">Failed to load pediatric content.</p>';
        }
    }

    async function loadSafety() {
        const el = document.getElementById('mc-safety-container');
        try {
            const res = await fetch('/api/maternal-child/safety');
            safetyData = await res.json();
            renderSafety(el);
        } catch {
            if (el) el.innerHTML = '<p class="text-ward-danger text-sm">Failed to load safety content.</p>';
        }
    }

    function renderSafety(el) {
        if (!el || !safetyData) return;
        const flags = safetyData.flags || [];
        const flagCards = flags.map(f => `
            <div class="mc-flag-card mc-cat-${esc(f.category || 'maternal')}">
                <div class="mc-flag-priority">${esc(f.priority || 'immediate')}</div>
                <div class="mc-flag-finding">${esc(f.finding)}</div>
                <div class="mc-flag-action"><strong>Action:</strong> ${esc(f.action)}</div>
                ${f.escalation ? `<div class="mc-flag-escalation"><strong>Escalation:</strong> ${esc(f.escalation)}</div>` : ''}
            </div>
        `).join('');

        el.innerHTML = `
            <section class="mc-section">
                <h3 class="mc-section-title">Maternal-Child Red Flags</h3>
                <p class="mc-section-desc">${flags.length} emergencies with priority actions and escalation paths</p>
                <div class="mc-flag-grid">${flagCards}</div>
            </section>
        `;
        reportProgress(1, 'safety');
    }

    async function loadComplicationsDrill() {
        const area = document.getElementById('mc-drill-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading drill…</p>';
        const res = await fetch('/api/maternal-child/complications-drill?count=5');
        const data = await res.json();
        drillQuestions = data.questions || [];
        drillIndex = 0;
        drillCorrect = 0;
        showDrillQuestion();
    }

    function showDrillQuestion() {
        const area = document.getElementById('mc-drill-area');
        const scoreEl = document.getElementById('mc-drill-score');
        const totalEl = document.getElementById('mc-drill-total');
        if (!area) return;

        if (totalEl) totalEl.textContent = drillQuestions.length;

        if (drillIndex >= drillQuestions.length) {
            const pct = drillQuestions.length
                ? Math.round((drillCorrect / drillQuestions.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-pink-400 mb-2">${drillCorrect}/${drillQuestions.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">${pct >= 80 ? 'Strong complication judgment!' : 'Review the safety red flags for missed escalation paths.'}</p>
                    <button onclick="MaternalChild.loadComplicationsDrill()" class="btn-primary mt-4 text-sm">New Drill</button>
                </div>`;
            if (scoreEl) scoreEl.textContent = drillCorrect;
            reportProgress(drillCorrect, 'complications_drill', pct);
            return;
        }

        const q = drillQuestions[drillIndex];
        if (scoreEl) scoreEl.textContent = drillCorrect;

        area.innerHTML = `
            <div class="scenario-card mc-drill-card">
                <div class="text-xs font-semibold text-ward-danger uppercase mb-2">Clinical Scenario</div>
                <div class="mc-drill-finding">${esc(q.finding)}</div>
                ${q.category ? `<span class="mc-ref-cat inline-block mt-2">${esc(q.category)}</span>` : ''}
                <p class="text-ward-200 font-medium mt-4 mb-3">What is the correct priority nursing action?</p>
                <div class="space-y-2" id="mc-drill-options">
                    ${q.options.map((opt, i) => `
                        <button type="button" class="practice-option" onclick="MaternalChild.answerDrill(${i})">
                            <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${esc(opt)}
                        </button>
                    `).join('')}
                </div>
                <div id="mc-drill-feedback" class="mt-4 hidden"></div>
            </div>
            <p class="text-center text-xs text-ward-600 mt-3">Question ${drillIndex + 1} of ${drillQuestions.length}</p>
        `;
    }

    async function answerDrill(selected) {
        const q = drillQuestions[drillIndex];
        const res = await fetch('/api/maternal-child/complications-drill/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: q.id,
                selected_index: selected,
                selected_option: q.options[selected],
            }),
        });
        const result = await res.json();
        if (result.correct) drillCorrect++;

        document.querySelectorAll('#mc-drill-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (i === result.correct_index) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('mc-drill-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${result.correct ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${result.correct ? 'text-ward-success' : 'text-ward-danger'}">${esc(result.feedback)}</p>
                    <p class="text-ward-300 mt-1">${esc(result.explanation)}</p>
                    ${result.clinical_why ? `<p class="text-xs text-ward-accent mt-2">${esc(result.clinical_why)}</p>` : ''}
                    <button onclick="MaternalChild.nextDrill()" class="btn-primary text-xs mt-3">Next →</button>
                </div>`;
        }
    }

    function nextDrill() {
        drillIndex++;
        showDrillQuestion();
    }

    function loadFcRatings() {
        try { return JSON.parse(localStorage.getItem(FC_RATINGS_KEY) || '{}'); }
        catch { return {}; }
    }

    function saveFcRatings() {
        localStorage.setItem(FC_RATINGS_KEY, JSON.stringify(fcRatings));
    }

    function updateFcStats() {
        const known = Object.values(fcRatings).filter(v => v === 'know').length;
        const review = Object.values(fcRatings).filter(v => v === 'review').length;
        const knownEl = document.getElementById('mc-fc-known');
        const reviewEl = document.getElementById('mc-fc-review');
        if (knownEl) knownEl.textContent = known;
        if (reviewEl) reviewEl.textContent = review;
    }

    async function loadFlashcards(count, shuffle = false) {
        const url = count
            ? `/api/maternal-child/flashcards?count=${count}`
            : '/api/maternal-child/flashcards';
        const res = await fetch(url);
        const data = await res.json();
        flashcards = data.cards || [];
        if (shuffle && flashcards.length > 1) {
            flashcards = flashcards.sort(() => Math.random() - 0.5);
        }
        cardIndex = 0;
        cardFlipped = false;
        showCard();
        updateFcStats();
        reportProgress(flashcards.length, 'flashcards');

        const verifyBtn = document.getElementById('mc-fc-verify-btn');
        if (verifyBtn) verifyBtn.classList.remove('hidden');
    }

    function renderFcDots() {
        const dots = document.getElementById('mc-fc-dots');
        if (!dots) return;
        dots.innerHTML = flashcards.map((c, i) => {
            const rating = fcRatings[c.id];
            let cls = 'mc-fc-dot';
            if (i === cardIndex) cls += ' active';
            if (rating === 'know') cls += ' known';
            if (rating === 'review') cls += ' review';
            return `<span class="${cls}"></span>`;
        }).join('');
    }

    function showCard() {
        const area = document.getElementById('mc-flashcard-area');
        if (!area || !flashcards.length) {
            if (area) area.innerHTML = '<p class="text-ward-500 text-sm text-center">No flashcards loaded.</p>';
            return;
        }

        const card = flashcards[cardIndex];
        cardFlipped = false;
        area.innerHTML = `
            <div class="mc-flashcard" id="mc-fc-card" onclick="MaternalChild.flipCard()">
                <div class="mc-flashcard-inner">
                    <div class="mc-flashcard-front">
                        <span class="text-xs text-pink-400 uppercase mb-2">${esc(card.category || 'OB/Peds')}</span>
                        <p class="text-ward-100 font-medium text-lg">${esc(card.front)}</p>
                        <p class="text-xs text-ward-600 mt-4">Tap to flip</p>
                    </div>
                    <div class="mc-flashcard-back">
                        <p class="text-ward-200">${esc(card.back)}</p>
                    </div>
                </div>
            </div>
            <p class="text-center text-xs text-ward-600 mt-3">Card ${cardIndex + 1} of ${flashcards.length}</p>
        `;
        renderFcDots();
    }

    function flipCard() {
        const card = document.getElementById('mc-fc-card');
        if (card) {
            cardFlipped = !cardFlipped;
            card.classList.toggle('flipped', cardFlipped);
        }
    }

    function nextCard() {
        if (cardIndex < flashcards.length - 1) {
            cardIndex++;
            showCard();
        }
    }

    function prevCard() {
        if (cardIndex > 0) {
            cardIndex--;
            showCard();
        }
    }

    function rateCard(rating) {
        const card = flashcards[cardIndex];
        if (!card) return;
        fcRatings[card.id] = rating;
        saveFcRatings();
        updateFcStats();
        renderFcDots();
        reportProgress(1, 'flashcard_review');
        nextCard();
    }

    async function startPractice(count) {
        const area = document.getElementById('mc-practice-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading questions…</p>';

        const res = await fetch(`/api/maternal-child/practice?count=${count}`);
        const data = await res.json();
        practiceQuestions = data.questions;
        practiceIndex = 0;
        practiceCorrect = 0;
        showPracticeQuestion();
    }

    function showPracticeQuestion() {
        const area = document.getElementById('mc-practice-area');
        const scoreEl = document.getElementById('mc-practice-score');
        if (!area) return;

        if (practiceIndex >= practiceQuestions.length) {
            const pct = practiceQuestions.length
                ? Math.round((practiceCorrect / practiceQuestions.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-pink-400 mb-2">${practiceCorrect}/${practiceQuestions.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">${pct >= 80 ? 'Strong maternal-child knowledge!' : 'Review reference tabs and retry.'}</p>
                </div>`;
            if (scoreEl) scoreEl.textContent = `Final: ${practiceCorrect}/${practiceQuestions.length}`;
            reportProgress(practiceCorrect, 'practice', pct);
            return;
        }

        const q = practiceQuestions[practiceIndex];
        if (scoreEl) scoreEl.textContent = `${practiceCorrect}/${practiceIndex}`;

        const cat = q.nclex_category ? `<span class="text-xs text-ward-600 ml-2">${esc(q.nclex_category)}</span>` : '';

        area.innerHTML = `
            <div class="mb-2 text-xs text-pink-400 uppercase tracking-wide">NCLEX-Style${cat}</div>
            <p class="text-ward-100 mb-4">${esc(q.question)}</p>
            <div class="space-y-2" id="mc-practice-options">
                ${q.options.map((opt, i) => `
                    <button type="button" class="practice-option" onclick="MaternalChild.answerPractice(${i}, ${q.correct_index})">
                        <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${esc(opt)}
                    </button>
                `).join('')}
            </div>
            <div id="mc-practice-feedback" class="mt-4 hidden"></div>
        `;
    }

    function answerPractice(selected, correct) {
        const q = practiceQuestions[practiceIndex];
        const isCorrect = selected === correct;
        if (isCorrect) practiceCorrect++;

        document.querySelectorAll('#mc-practice-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (i === correct) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('mc-practice-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${isCorrect ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${isCorrect ? 'text-ward-success' : 'text-ward-danger'}">${isCorrect ? 'Correct!' : 'Incorrect.'}</p>
                    <p class="text-ward-300 mt-1">${esc(q.explanation)}</p>
                    <button onclick="verifySource('maternal_child')" class="btn-verify text-xs mt-2">Verify Source</button>
                </div>
                <button onclick="MaternalChild.nextPracticeQuestion()" class="btn-primary w-full mt-3 text-sm">Next Question</button>
            `;
        }
    }

    function nextPracticeQuestion() {
        practiceIndex++;
        showPracticeQuestion();
    }

    function askSocratic(subject, snippet, tab) {
        window.WardSocratic?.setModuleContext({
            module: MODULE_ID,
            tab: tab || 'antepartum',
            subject,
            snippet,
            topic: 'assessment_finding',
        });
        openSocraticMode(MODULE_ID, 'assessment_finding');
    }

    function init() {
        WardTabs.register('/modules/maternal-child', { validTabs: TABS, defaultTab: DEFAULT_TAB, switchTab });
        WardTabs.init('/modules/maternal-child');
    }

    return {
        switchTab, init,
        loadAntepartum, loadIntrapartum, loadPostpartum, loadPediatrics, loadSafety,
        loadComplicationsDrill, answerDrill, nextDrill,
        loadFlashcards, flipCard, nextCard, prevCard, rateCard,
        startPractice, answerPractice, nextPracticeQuestion,
        askSocratic,
        exportFlashcardDeck,
        refreshModuleProgress,
    };
})();