/**
 * The Ward — NURS 147 Mental Health Nursing Module
 */
const MentalHealth = (() => {
    const MODULE_ID = 'mental_health';
    const TABS = ['therapeutic-communication', 'safety-risk'];

    let commData = null;
    let safetyData = null;
    let drillQuestions = [];
    let drillIndex = 0;
    let drillCorrect = 0;

    function switchTab(tab) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.querySelectorAll('.mh-tab-btn').forEach(b => b.classList.remove('active'));
        const panel = document.getElementById('tab-' + tab);
        const btn = document.querySelector(`[data-tab="${tab}"]`);
        if (panel) panel.classList.remove('hidden');
        if (btn) btn.classList.add('active');

        if (tab === 'therapeutic-communication' && !commData) loadCommunication();
        if (tab === 'safety-risk') {
            if (!safetyData) loadSafetyRisk();
            if (!drillQuestions.length) loadSafetyDrill();
        }

        history.replaceState(null, '', location.pathname + (tab !== 'therapeutic-communication' ? '#' + tab : ''));

        const labels = {
            'therapeutic-communication': 'Therapeutic Communication',
            'safety-risk': 'Safety & Risk Assessment',
        };
        window.WardSocratic?.setModuleContext({
            module: 'mental_health',
            tab,
            subject: labels[tab] || 'Mental Health Nursing',
            snippet: '',
            topic: 'psychosocial',
        });
    }

    const DEFAULT_TAB = 'therapeutic-communication';

    async function reportProgress(items, activityType, score) {
        await fetch('/api/mental-health/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items_studied: items, activity_type: activityType, score }),
        });
        refreshProgressBar();
    }

    async function refreshProgressBar() {
        const res = await fetch('/api/mental-health/stats');
        const data = await res.json();
        const bar = document.getElementById('module-progress-bar');
        const pct = document.getElementById('module-progress-pct');
        if (bar) bar.style.width = data.percentage + '%';
        if (pct) pct.textContent = data.percentage + '%';
    }

    async function loadCommunication() {
        const el = document.getElementById('mh-comm-container');
        try {
            const res = await fetch('/api/mental-health/communication');
            commData = await res.json();
            renderCommunication(el);
        } catch {
            if (el) el.innerHTML = '<p class="text-ward-danger text-sm">Failed to load communication content.</p>';
        }
    }

    function renderCommunication(el) {
        if (!el || !commData) return;
        const techniques = commData.techniques || [];
        const barriers = commData.barriers || [];

        const techCards = techniques.map(t => `
            <details class="mh-comm-card" data-id="${esc(t.id)}">
                <summary class="mh-comm-summary">
                    <span class="mh-comm-name">${esc(t.technique)}</span>
                    <span class="mh-comm-toggle">Expand</span>
                </summary>
                <div class="mh-comm-body">
                    <p class="mh-comm-desc">${esc(t.description)}</p>
                    ${t.example ? `<div class="mh-callout mh-callout-example"><strong>Example:</strong> ${esc(t.example)}</div>` : ''}
                    ${t.nursing_action ? `<div class="mh-callout mh-callout-action"><strong>RN Action:</strong> ${esc(t.nursing_action)}</div>` : ''}
                    ${t.avoid ? `<div class="mh-callout mh-callout-avoid"><strong>Avoid:</strong> ${esc(t.avoid)}</div>` : ''}
                    ${t.clinical_why ? `<p class="mh-clinical-why"><em>${esc(t.clinical_why)}</em></p>` : ''}
                    <button type="button" class="text-xs text-ward-purple hover:underline mt-2"
                            onclick="MentalHealth.askSocratic('${esc(t.technique)}', '${esc((t.description || '').slice(0, 200))}')">
                        Ask Socratic tutor →
                    </button>
                </div>
            </details>
        `).join('');

        const barrierCards = barriers.map(b => `
            <div class="mh-barrier-card">
                <div class="mh-barrier-name">${esc(b.barrier)}</div>
                <p class="mh-barrier-desc">${esc(b.description)}</p>
                ${b.example ? `<p class="mh-barrier-example"><strong class="text-ward-danger">Don't:</strong> ${esc(b.example)}</p>` : ''}
                ${b.instead ? `<p class="mh-barrier-instead"><strong class="text-ward-success">Instead:</strong> ${esc(b.instead)}</p>` : ''}
            </div>
        `).join('');

        el.innerHTML = `
            <section class="mh-section">
                <h3 class="mh-section-title">Core Techniques</h3>
                <p class="mh-section-desc">${techniques.length} evidence-based communication skills for behavioral health settings</p>
                <div class="mh-comm-list">${techCards}</div>
            </section>
            <section class="mh-section mt-6">
                <h3 class="mh-section-title">Barriers to Avoid</h3>
                <p class="mh-section-desc">Non-therapeutic responses that block disclosure and escalate distress</p>
                <div class="mh-barrier-grid">${barrierCards}</div>
            </section>
        `;

        el.querySelectorAll('.mh-comm-card').forEach(card => {
            card.addEventListener('toggle', () => {
                if (!card.open) return;
                const tech = techniques.find(t => t.id === card.dataset.id);
                if (tech) {
                    window.WardSocratic?.setModuleContext({
                        module: 'mental_health',
                        tab: 'therapeutic-communication',
                        subject: tech.technique,
                        snippet: (tech.description || '').slice(0, 400),
                        topic: 'psychosocial',
                    });
                    reportProgress(1, 'communication');
                }
            });
        });
    }

    async function loadSafetyRisk() {
        const el = document.getElementById('mh-safety-container');
        try {
            const res = await fetch('/api/mental-health/safety-risk');
            safetyData = await res.json();
            renderSafetyRisk(el);
        } catch {
            if (el) el.innerHTML = '<p class="text-ward-danger text-sm">Failed to load safety content.</p>';
        }
    }

    function renderSafetyRisk(el) {
        if (!el || !safetyData) return;
        const flags = safetyData.flags || [];
        const tools = safetyData.screening_tools || [];

        const flagCards = flags.map(f => `
            <div class="mh-flag-card mh-cat-${esc(f.category || 'suicide')}">
                <div class="mh-flag-priority">${esc(f.priority || 'immediate')}</div>
                <div class="mh-flag-finding">${esc(f.finding)}</div>
                <div class="mh-flag-action"><strong>Action:</strong> ${esc(f.action)}</div>
                <span class="mh-flag-cat">${esc(f.category || '')}</span>
            </div>
        `).join('');

        const toolCards = tools.map(t => `
            <details class="mh-tool-card">
                <summary class="mh-tool-summary">
                    <span class="mh-tool-name">${esc(t.name)}</span>
                </summary>
                <div class="mh-tool-body">
                    <p>${esc(t.purpose)}</p>
                    <div class="mh-callout mh-callout-action mt-2"><strong>RN Action:</strong> ${esc(t.nursing_action)}</div>
                    <ul class="mh-tool-points">
                        ${(t.key_points || []).map(p => `<li>${esc(p)}</li>`).join('')}
                    </ul>
                    ${t.clinical_why ? `<p class="mh-clinical-why mt-2"><em>${esc(t.clinical_why)}</em></p>` : ''}
                </div>
            </details>
        `).join('');

        el.innerHTML = `
            <section class="mh-section">
                <h3 class="mh-section-title">Psychosocial Red Flags</h3>
                <p class="mh-section-desc">Immediate nursing actions for behavioral health emergencies</p>
                <div class="mh-flag-grid">${flagCards}</div>
            </section>
            <section class="mh-section mt-6">
                <h3 class="mh-section-title">Screening Tools</h3>
                <p class="mh-section-desc">Validated instruments for suicide risk and withdrawal assessment</p>
                <div class="mh-tool-list">${toolCards}</div>
            </section>
        `;
    }

    async function loadSafetyDrill() {
        const area = document.getElementById('mh-drill-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading drill…</p>';
        const res = await fetch('/api/mental-health/safety-drill?count=5');
        const data = await res.json();
        drillQuestions = data.questions || [];
        drillIndex = 0;
        drillCorrect = 0;
        showDrillQuestion();
    }

    function showDrillQuestion() {
        const area = document.getElementById('mh-drill-area');
        const scoreEl = document.getElementById('mh-drill-score');
        const totalEl = document.getElementById('mh-drill-total');
        if (!area) return;

        if (totalEl) totalEl.textContent = drillQuestions.length;

        if (drillIndex >= drillQuestions.length) {
            const pct = drillQuestions.length
                ? Math.round((drillCorrect / drillQuestions.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-ward-purple mb-2">${drillCorrect}/${drillQuestions.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">${pct >= 80 ? 'Strong safety judgment!' : 'Review the red flags above for missed escalation paths.'}</p>
                    <button onclick="MentalHealth.loadSafetyDrill()" class="btn-primary mt-4 text-sm">New Drill</button>
                </div>`;
            if (scoreEl) scoreEl.textContent = drillCorrect;
            reportProgress(drillCorrect, 'safety_drill', pct);
            return;
        }

        const q = drillQuestions[drillIndex];
        if (scoreEl) scoreEl.textContent = drillCorrect;

        area.innerHTML = `
            <div class="scenario-card mh-drill-card">
                <div class="text-xs font-semibold text-ward-danger uppercase mb-2">Clinical Scenario</div>
                <div class="mh-drill-finding">${esc(q.finding)}</div>
                ${q.category ? `<span class="mh-flag-cat inline-block mt-2">${esc(q.category)}</span>` : ''}
                <p class="text-ward-200 font-medium mt-4 mb-3">What is the correct priority nursing action?</p>
                <div class="space-y-2" id="mh-drill-options">
                    ${q.options.map((opt, i) => `
                        <button type="button" class="practice-option" onclick="MentalHealth.answerDrill(${i})">
                            <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${esc(opt)}
                        </button>
                    `).join('')}
                </div>
                <div id="mh-drill-feedback" class="mt-4 hidden"></div>
            </div>
            <p class="text-center text-xs text-ward-600 mt-3">Question ${drillIndex + 1} of ${drillQuestions.length}</p>
        `;
    }

    async function answerDrill(selected) {
        const q = drillQuestions[drillIndex];
        const res = await fetch('/api/mental-health/safety-drill/check', {
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

        document.querySelectorAll('#mh-drill-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (i === result.correct_index) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('mh-drill-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${result.correct ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${result.correct ? 'text-ward-success' : 'text-ward-danger'}">${esc(result.feedback)}</p>
                    <p class="text-ward-300 mt-1">${esc(result.explanation)}</p>
                    ${result.clinical_why ? `<p class="text-xs text-ward-accent mt-2">${esc(result.clinical_why)}</p>` : ''}
                    <button onclick="MentalHealth.nextDrill()" class="btn-primary text-xs mt-3">Next →</button>
                </div>`;
        }
    }

    function nextDrill() {
        drillIndex++;
        showDrillQuestion();
    }

    function askSocratic(subject, snippet) {
        window.WardSocratic?.setModuleContext({
            module: 'mental_health',
            tab: 'therapeutic-communication',
            subject,
            snippet,
            topic: 'psychosocial',
        });
        openSocraticMode('mental_health', 'psychosocial');
    }

    function init() {
        WardTabs.register('/modules/mental-health', { validTabs: TABS, defaultTab: DEFAULT_TAB, switchTab });
        WardTabs.init('/modules/mental-health');
    }

    return {
        switchTab, init, loadCommunication, loadSafetyRisk, loadSafetyDrill,
        answerDrill, nextDrill, askSocratic,
    };
})();