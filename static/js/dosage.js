/**
 * The Ward — NURS 145 Dosage Calculations Module
 */
const Dosage = (() => {
    const MODULE_ID = 'dosage';
    let showWork = true;
    let showFirstPrinciples = true;
    let firstPrinciplesCache = {};
    let lastResult = null;
    let lastInputs = null;
    let practiceProblems = [];
    let practiceIndex = 0;
    let practiceCorrect = 0;
    let practiceAnswered = 0;
    let contentData = null;
    let pharmCategoryFilter = 'all';
    const favoritesCache = {};

    const calcForms = {
        tablet_capsule: [
            { id: 'ordered_dose', label: 'Ordered Dose', type: 'number', step: '0.01', placeholder: 'e.g. 0.125' },
            { id: 'available_dose', label: 'Available Dose per Tablet/Capsule', type: 'number', step: '0.01', placeholder: 'e.g. 0.25' },
        ],
        liquid: [
            { id: 'ordered_dose', label: 'Ordered Dose', type: 'number', step: '0.1', placeholder: 'e.g. 4' },
            { id: 'available_dose', label: 'Available Dose (in volume)', type: 'number', step: '0.1', placeholder: 'e.g. 10' },
            { id: 'available_volume', label: 'Available Volume (mL)', type: 'number', step: '0.1', placeholder: 'e.g. 1' },
        ],
        iv_drip_gtt: [
            { id: 'volume_to_infuse_ml', label: 'Volume to Infuse (mL)', type: 'number', step: '1', placeholder: 'e.g. 1000' },
            { id: 'time_minutes', label: 'Time (minutes)', type: 'number', step: '1', placeholder: 'e.g. 480 for 8 hr' },
            { id: 'drop_factor', label: 'Drop Factor (gtt/mL)', type: 'number', step: '1', placeholder: '10, 15, 20, or 60' },
        ],
        iv_drip_ml_hr: [
            { id: 'volume_to_infuse_ml', label: 'Volume to Infuse (mL)', type: 'number', step: '1', placeholder: 'e.g. 500' },
            { id: 'time_minutes', label: 'Time (minutes)', type: 'number', step: '1', placeholder: 'e.g. 240 for 4 hr' },
        ],
        weight_based: [
            { id: 'patient_weight_kg', label: 'Patient Weight (kg)', type: 'number', step: '0.1', placeholder: 'e.g. 80' },
            { id: 'dose_per_kg', label: 'Dose per kg', type: 'number', step: '0.1', placeholder: 'e.g. 2 mg/kg' },
            { id: 'doses_per_day', label: 'Doses per Day (optional)', type: 'number', step: '1', placeholder: 'Leave blank if single dose' },
        ],
        pediatric: [
            { id: 'patient_weight_kg', label: 'Child Weight (kg)', type: 'number', step: '0.1', placeholder: 'Weigh patient!' },
            { id: 'dose_per_kg', label: 'Dose per kg per day', type: 'number', step: '0.1', placeholder: 'e.g. 25 mg/kg/day' },
            { id: 'doses_per_day', label: 'Doses per Day', type: 'number', step: '1', placeholder: 'e.g. 2 for BID' },
        ],
        geriatric: [
            { id: 'ordered_dose', label: 'Standard Adult Dose', type: 'number', step: '0.1', placeholder: 'e.g. 10' },
            { id: 'geriatric_factor', label: 'Adjustment Factor', type: 'select', options: [
                { value: '0.75', label: '75% — usual geriatric start' },
                { value: '0.5', label: '50% — high sensitivity / frail' },
            ]},
        ],
    };

    function switchTab(tab) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.querySelectorAll('.dose-tab-btn').forEach(b => b.classList.remove('active'));
        const panel = document.getElementById('tab-' + tab);
        const btn = document.querySelector(`[data-tab="${tab}"]`);
        if (panel) panel.classList.remove('hidden');
        if (btn) btn.classList.add('active');

        if (tab === 'practice' && !practiceProblems.length) loadPractice();
        if (tab === 'traps' && !document.querySelector('.dose-trap-card')) loadContent();
        if (tab === 'pharm' && !document.querySelector('.dose-pharm-explorer')) loadContent();
        if (tab === 'favorites') loadFavorites();
        if (tab === 'export') ensureExportData();

        history.replaceState(null, '', location.pathname + (tab !== 'calculator' ? '#' + tab : ''));
        const tabLabels = {
            calculator: 'Calculator', practice: 'Practice', traps: 'Error Traps',
            pharm: 'Pharmacology', favorites: 'Saved Calculations', export: 'Export',
        };
        window.WardSocratic?.setModuleContext({
            module: 'dosage',
            tab,
            subject: `NURS 145 Dosage · ${tabLabels[tab] || tab}`,
            topic: tab === 'pharm' ? 'drug_mechanism' : 'calculation',
        });
    }

    const VALID_TABS = ['calculator', 'practice', 'traps', 'pharm', 'favorites', 'export'];
    const DEFAULT_TAB = 'calculator';

    async function ensureExportData() {
        if (!practiceProblems.length) await loadPractice();
        if (!contentData) await loadContent();
    }

    async function loadFirstPrinciples(calcType) {
        if (firstPrinciplesCache[calcType]) {
            renderFirstPrinciples(firstPrinciplesCache[calcType]);
            return;
        }
        try {
            const res = await fetch(`/api/dosage/first-principles/${calcType}`);
            const data = await res.json();
            firstPrinciplesCache[calcType] = data.principles || {};
            renderFirstPrinciples(firstPrinciplesCache[calcType]);
        } catch { /* silent */ }
    }

    function renderFirstPrinciples(fp) {
        const panel = document.getElementById('first-principles-panel');
        if (!panel) return;
        if (!showFirstPrinciples || !fp || !fp.core_idea) {
            panel.innerHTML = '';
            panel.classList.add('hidden');
            return;
        }
        panel.classList.remove('hidden');
        const setup = (fp.setup || []).map(s => `<li>${renderDosageMathLine(s)}</li>`).join('');
        panel.innerHTML = `
            <div class="dose-fp-header">
                <span class="dose-fp-icon">∑</span>
                <span class="text-xs font-semibold text-ward-warning uppercase tracking-wide">First Principles</span>
            </div>
            <p class="dose-fp-core">${esc(fp.core_idea)}</p>
            ${fp.question ? `<p class="dose-fp-question"><em>${esc(fp.question)}</em></p>` : ''}
            ${setup ? `<ol class="dose-fp-setup">${setup}</ol>` : ''}
            ${fp.unit_logic ? `<p class="dose-fp-unit"><strong>Units:</strong> ${renderDosageMathLine(fp.unit_logic)}</p>` : ''}
            ${fp.safety_check ? `<p class="dose-fp-safety"><strong>Safety:</strong> ${esc(fp.safety_check)}</p>` : ''}
            ${fp.clinical_why ? `<p class="dose-fp-why"><strong>Clinical why:</strong> ${esc(fp.clinical_why)}</p>` : ''}
            <button type="button" onclick="openSocraticMode('dosage', 'calculation')" class="text-xs text-ward-purple hover:underline mt-2">Ask Socratic tutor about this →</button>
        `;
        renderMath(panel);
    }

    function toggleFirstPrinciples() {
        showFirstPrinciples = document.getElementById('first-principles-toggle')?.checked ?? true;
        const type = document.getElementById('calc-type')?.value || 'tablet_capsule';
        if (firstPrinciplesCache[type]) renderFirstPrinciples(firstPrinciplesCache[type]);
        else loadFirstPrinciples(type);
    }

    function updateCalcForm() {
        const type = document.getElementById('calc-type')?.value || 'tablet_capsule';
        const fields = calcForms[type] || [];
        updateFormulaHint();
        loadFirstPrinciples(type);

        const container = document.getElementById('calc-inputs');
        if (!container) return;

        container.innerHTML = fields.map(f => {
            if (f.type === 'select') {
                const opts = (f.options || []).map(o =>
                    `<option value="${o.value}">${o.label}</option>`
                ).join('');
                return `<div><label class="label">${f.label}</label>
                    <select id="${f.id}" class="input-field">${opts}</select></div>`;
            }
            return `<div><label class="label">${f.label}</label>
                <input type="${f.type}" id="${f.id}" step="${f.step || 1}" class="input-field" placeholder="${f.placeholder || ''}"></div>`;
        }).join('');
    }

    function toggleShowWork() {
        showWork = document.getElementById('show-work-toggle')?.checked ?? true;
    }

    function collectInputs() {
        const type = document.getElementById('calc-type')?.value;
        const fields = calcForms[type] || [];
        const body = { calc_type: type, show_work: showWork };
        fields.forEach(f => {
            const el = document.getElementById(f.id);
            if (!el) return;
            if (f.type === 'select') {
                body[f.id] = parseFloat(el.value);
            } else {
                const val = parseFloat(el.value);
                if (!isNaN(val)) body[f.id] = val;
            }
        });
        return body;
    }

    async function calculate() {
        const body = collectInputs();
        lastInputs = body;
        const res = await fetch('/api/dosage/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        lastResult = data;
        renderResult(data);
        document.getElementById('save-fav-btn')?.removeAttribute('disabled');
        await reportProgress(1, 'calculator');
        refreshProgressBar();
    }

    function renderResult(data) {
        const el = document.getElementById('calc-result');
        if (!el) return;

        const workHtml = (data.work_steps && data.work_steps.length && showWork)
            ? `<div class="mt-3 mb-3">
                <div class="text-xs text-ward-warning uppercase font-semibold mb-2">Detailed Work — Clinical Reasoning</div>
                ${data.work_steps.map(w => `
                    <div class="dose-work-card">
                        <div class="dose-work-step-num">Step ${w.step}</div>
                        <div class="dose-work-title">${esc(w.title)}</div>
                        <div class="dose-work-formula">${mathSpan(w.formula)}</div>
                        <div class="dose-work-reasoning">${esc(w.reasoning)}</div>
                        ${w.result ? `<div class="dose-work-result">→ ${esc(w.result)}</div>` : ''}
                    </div>
                `).join('')}
               </div>`
            : '';

        const stepsHtml = (!showWork || !data.work_steps?.length)
            ? `<div class="space-y-1 mb-3">${(data.steps || []).map(s =>
                `<div class="dose-step">${esc(s)}</div>`
            ).join('')}</div>`
            : '';

        const warningsHtml = (data.safety_warnings || []).length
            ? `<div class="dose-callout dose-callout-danger">
                <div class="dose-callout-label">Safety Warnings</div>
                <ul class="dose-warning-list">${data.safety_warnings.map(w => `<li>${esc(w)}</li>`).join('')}</ul>
               </div>`
            : '';

        const nursingHtml = (data.nursing_considerations || []).length
            ? `<div class="dose-callout dose-callout-nursing">
                <div class="dose-callout-label">Nursing Considerations</div>
                <ul class="dose-warning-list" style="color:#6ee7b7">${data.nursing_considerations.map(n =>
                    `<li style="color:#86efac">${esc(n)}</li>`
                ).join('')}</ul>
               </div>`
            : '';

        el.innerHTML = `
            <div class="dose-answer">${data.answer} ${esc(data.unit)}</div>
            ${workHtml}
            ${stepsHtml}
            ${renderDerivation(data)}
            <div class="dose-callout dose-callout-clinical">
                <div class="dose-callout-label">Clinical Note</div>
                ${esc(data.clinical_note)}
            </div>
            ${data.pharmacology_note ? `<div class="dose-callout dose-callout-pharm">
                <div class="dose-callout-label">Pharmacology</div>
                ${esc(data.pharmacology_note)}
            </div>` : ''}
            ${warningsHtml}
            ${nursingHtml}
            <button onclick='showSource(${JSON.stringify(data.source)})' class="btn-verify text-xs mt-3">Verify Source</button>
            <button type="button" onclick="openSocraticMode('dosage','calculation')" class="text-xs text-ward-purple hover:underline mt-2 block">Ask Socratic tutor about this →</button>
        `;
        const typeLabel = document.querySelector(`#calc-type option[value="${lastInputs?.calc_type}"]`)?.textContent
            || lastInputs?.calc_type || 'Dosage calculation';
        window.WardSocratic?.setModuleContext({
            module: 'dosage',
            tab: 'calculator',
            subject: typeLabel,
            snippet: `${data.answer} ${data.unit} — ${data.clinical_note || ''}`.slice(0, 400),
            topic: 'calculation',
        });
        renderMath(el);
    }

    async function saveFavorite() {
        if (!lastResult || !lastInputs) return;
        const label = lastResult.calc_label || `${lastInputs.calc_type} calculation`;
        await fetch('/api/dosage/favorites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                calc_type: lastInputs.calc_type,
                label,
                inputs_json: JSON.stringify(lastInputs),
                result_json: JSON.stringify(lastResult),
            }),
        });
        const btn = document.getElementById('save-fav-btn');
        if (btn) {
            btn.textContent = '★ Saved';
            setTimeout(() => { btn.textContent = '★ Save'; }, 2000);
        }
        refreshProgressBar();
    }

    async function loadPractice() {
        const res = await fetch('/api/dosage/practice');
        const data = await res.json();
        practiceProblems = data.problems || [];
        practiceIndex = 0;
        practiceCorrect = 0;
        practiceAnswered = 0;
        document.getElementById('practice-total').textContent = practiceProblems.length;
        document.getElementById('practice-score').textContent = '0';
        renderPracticeQuestion();
    }

    function renderPracticeQuestion() {
        const container = document.getElementById('practice-container');
        if (!container || !practiceProblems.length) {
            if (container) container.innerHTML = '<p class="text-ward-500">No practice problems available.</p>';
            return;
        }

        if (practiceIndex >= practiceProblems.length) {
            const pct = practiceProblems.length
                ? Math.round((practiceCorrect / practiceProblems.length) * 100) : 0;
            container.innerHTML = `
                <div class="dose-practice-card text-center">
                    <div class="text-2xl font-bold text-ward-warning mb-2">Set Complete!</div>
                    <p class="text-ward-300">${practiceCorrect} of ${practiceProblems.length} correct (${pct}%)</p>
                    <button onclick="Dosage.loadPractice()" class="btn-primary mt-4">Try Again</button>
                </div>`;
            return;
        }

        const p = practiceProblems[practiceIndex];
        container.innerHTML = `
            <div class="dose-practice-card">
                <div class="flex justify-between text-xs text-ward-500 mb-2">
                    <span>Problem ${practiceIndex + 1} of ${practiceProblems.length}</span>
                    <span class="font-mono text-ward-warning">${esc(p.calc_type || '')}</span>
                </div>
                <div class="dose-practice-q">${esc(p.question)}</div>
                <div id="practice-options">
                    ${p.options.map((opt, i) =>
                        `<button class="dose-option" onclick="Dosage.answerPractice('${p.id}', ${i}, this)">${esc(opt)}</button>`
                    ).join('')}
                </div>
                <div id="practice-feedback"></div>
            </div>`;
    }

    async function answerPractice(problemId, selectedIndex, btn) {
        document.querySelectorAll('.dose-option').forEach(b => b.disabled = true);
        const res = await fetch('/api/dosage/practice/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ problem_id: problemId, selected_index: selectedIndex }),
        });
        const data = await res.json();
        practiceAnswered++;

        if (data.correct) {
            practiceCorrect++;
            btn.classList.add('correct');
        } else {
            btn.classList.add('incorrect');
            document.querySelectorAll('.dose-option')[data.correct_index]?.classList.add('correct');
        }

        document.getElementById('practice-score').textContent = practiceCorrect;

        const workHtml = (data.work_steps || []).map(w => `
            <div class="dose-work-card" style="margin-top:0.5rem">
                <div class="dose-work-step-num">Step ${w.step}</div>
                <div class="dose-work-formula">${mathSpan(w.formula)}</div>
                <div class="dose-work-reasoning">${esc(w.reasoning)}</div>
                ${w.result ? `<div class="dose-work-result">→ ${esc(w.result)}</div>` : ''}
            </div>
        `).join('');

        document.getElementById('practice-feedback').innerHTML = `
            <div class="dose-feedback ${data.correct ? 'correct-fb' : 'incorrect-fb'}">
                <strong>${data.correct ? '✓ Correct!' : '✗ Not quite.'}</strong>
                <p class="mt-1">${esc(data.explanation)}</p>
                <p class="mt-1 font-mono text-ward-warning">Answer: ${esc(data.answer)}</p>
                ${data.trap ? `<p class="mt-2 text-ward-danger text-xs"><strong>Error trap:</strong> ${esc(data.trap)}</p>` : ''}
                ${data.nursing_note ? `<p class="mt-1 text-ward-success text-xs"><strong>Nursing:</strong> ${esc(data.nursing_note)}</p>` : ''}
                ${workHtml}
                <button onclick="Dosage.nextPractice()" class="btn-primary text-xs mt-3">Next Problem →</button>
            </div>`;

        const feedbackEl = document.getElementById('practice-feedback');
        if (feedbackEl) renderMath(feedbackEl);

        refreshProgressBar();
    }

    function nextPractice() {
        practiceIndex++;
        renderPracticeQuestion();
    }

    async function loadContent() {
        if (contentData) {
            renderTraps(contentData.error_traps);
            renderPharm(contentData);
            return;
        }
        const res = await fetch('/api/dosage/content');
        contentData = await res.json();
        renderTraps(contentData.error_traps || []);
        renderPharm(contentData);
    }

    function renderTraps(traps) {
        const el = document.getElementById('traps-container');
        if (!el) return;
        el.innerHTML = traps.map(t => `
            <div class="dose-trap-card">
                <div class="dose-trap-title">${esc(t.title)}</div>
                <div class="dose-trap-trap"><strong class="text-ward-danger">Trap:</strong> ${esc(t.trap)}</div>
                <div class="dose-trap-avoid"><strong>Avoid:</strong> ${esc(t.avoid)}</div>
                <div class="dose-trap-example">Example: ${esc(t.example)}</div>
            </div>
        `).join('');
    }

    function renderPharmList(items, label, cls) {
        if (!items?.length) return '';
        return `
            <ul class="dose-pharm-list ${cls || ''}">
                ${items.map(item => `<li>${esc(item)}</li>`).join('')}
            </ul>
        `;
    }

    function renderPharmSafety(safetyItems) {
        if (!safetyItems?.length) return '';
        return `
            <section class="dose-pharm-section">
                <h3 class="dose-pharm-section-title">Safety Concepts</h3>
                <p class="dose-pharm-section-desc">Connect dose calculations to therapeutic range and high-alert protocols</p>
                <div class="dose-pharm-safety-grid">
                    ${safetyItems.map(p => `
                        <div class="dose-pharm-card dose-pharm-safety-card">
                            <div class="dose-pharm-title">${esc(p.title)}</div>
                            <div class="dose-pharm-concept">${esc(p.concept)}</div>
                            <div class="dose-pharm-action"><strong>RN Action:</strong> ${esc(p.nursing_action)}</div>
                            <div class="dose-pharm-examples">
                                ${(p.examples || []).map(e => `<span class="dose-pharm-tag">${esc(e)}</span>`).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </section>
        `;
    }

    function renderDrugClassCard(dc) {
        const prototypes = (dc.prototype_drugs || []).map(d => `<span class="dose-pharm-tag">${esc(d)}</span>`).join('');
        const color = dc.category || 'purple';
        const highAlert = dc.high_alert
            ? '<span class="dose-drug-alert">High Alert</span>'
            : '';
        return `
            <details class="dose-drug-class-card" data-category="${esc(dc.category)}" data-id="${esc(dc.id)}">
                <summary class="dose-drug-class-summary dose-cat-${esc(color)}">
                    <div class="dose-drug-class-head">
                        <span class="dose-drug-class-name">${esc(dc.name)}</span>
                        <span class="dose-drug-class-cat">${esc(dc.category_label || dc.category)}</span>
                    </div>
                    <div class="dose-drug-class-meta">
                        ${highAlert}
                        <span class="dose-drug-class-toggle">Expand</span>
                    </div>
                </summary>
                <div class="dose-drug-class-body">
                    ${prototypes ? `<div class="dose-drug-prototypes">${prototypes}</div>` : ''}
                    <div class="dose-drug-block">
                        <h4>Mechanism of Action</h4>
                        <p>${esc(dc.mechanism)}</p>
                    </div>
                    ${dc.indications ? `
                        <div class="dose-drug-block">
                            <h4>Indications</h4>
                            <p>${esc(dc.indications)}</p>
                        </div>
                    ` : ''}
                    <div class="dose-drug-block dose-drug-block-nursing">
                        <h4>Nursing Implications</h4>
                        ${renderPharmList(dc.nursing_implications)}
                    </div>
                    <div class="dose-drug-grid">
                        <div class="dose-drug-block">
                            <h4>Monitoring</h4>
                            ${renderPharmList(dc.monitoring, '', 'dose-pharm-list-compact')}
                        </div>
                        <div class="dose-drug-block dose-drug-block-warn">
                            <h4>Common Side Effects</h4>
                            ${renderPharmList(dc.common_side_effects, '', 'dose-pharm-list-compact')}
                        </div>
                    </div>
                    <div class="dose-drug-grid">
                        <div class="dose-drug-block dose-drug-block-danger">
                            <h4>Contraindications</h4>
                            ${renderPharmList(dc.contraindications, '', 'dose-pharm-list-compact')}
                        </div>
                        <div class="dose-drug-block dose-drug-block-interact">
                            <h4>Key Interactions</h4>
                            ${renderPharmList(dc.interactions, '', 'dose-pharm-list-compact')}
                        </div>
                    </div>
                    ${dc.nclex_focus ? `
                        <div class="dose-drug-nclex">
                            <strong>NCLEX Focus:</strong> ${esc(dc.nclex_focus)}
                        </div>
                    ` : ''}
                    ${dc.clinical_why ? `
                        <div class="dose-drug-clinical-why">
                            <strong>Clinical Why:</strong> ${esc(dc.clinical_why)}
                        </div>
                    ` : ''}
                    <div class="dose-drug-actions">
                        <button type="button" class="text-xs text-ward-purple hover:underline"
                                onclick="Dosage.askPharmSocratic('${esc(dc.id)}')">Ask Socratic tutor →</button>
                    </div>
                </div>
            </details>
        `;
    }

    function renderPharm(data) {
        const el = document.getElementById('pharm-container');
        if (!el) return;

        const safety = data.pharmacology_safety || [];
        const classes = data.drug_classes || [];
        const categories = data.pharm_categories || [];
        const filtered = pharmCategoryFilter === 'all'
            ? classes
            : classes.filter(dc => dc.category === pharmCategoryFilter);

        const categoryPills = [
            { id: 'all', label: 'All Classes' },
            ...categories.map(c => ({ id: c.id, label: c.label })),
        ];

        el.innerHTML = `
            <div class="dose-pharm-explorer">
                ${renderPharmSafety(safety)}
                <section class="dose-pharm-section">
                    <div class="dose-pharm-section-header">
                        <div>
                            <h3 class="dose-pharm-section-title">Drug Class Explorer</h3>
                            <p class="dose-pharm-section-desc">${classes.length} ADN-relevant classes across ${categories.length} categories</p>
                        </div>
                        <span class="stat-pill">${filtered.length} shown</span>
                    </div>
                    <div class="dose-pharm-filter" role="tablist">
                        ${categoryPills.map(c => `
                            <button type="button"
                                    class="dose-pharm-filter-btn${pharmCategoryFilter === c.id ? ' active' : ''}"
                                    data-cat="${esc(c.id)}"
                                    onclick="Dosage.filterPharmCategory('${esc(c.id)}')">
                                ${esc(c.label)}
                            </button>
                        `).join('')}
                    </div>
                    <div class="dose-drug-class-list">
                        ${filtered.length
                            ? filtered.map(renderDrugClassCard).join('')
                            : '<p class="text-ward-500 text-sm">No drug classes in this category.</p>'}
                    </div>
                </section>
            </div>
        `;

        el.querySelectorAll('.dose-drug-class-card').forEach(card => {
            card.addEventListener('toggle', () => {
                if (!card.open) return;
                const dc = (data.drug_classes || []).find(d => d.id === card.dataset.id);
                if (!dc) return;
                window.WardSocratic?.setModuleContext({
                    module: 'dosage',
                    tab: 'pharm',
                    subject: `${dc.name} (${dc.category_label || dc.category})`,
                    snippet: (dc.mechanism || dc.clinical_why || '').slice(0, 400),
                    topic: 'drug_mechanism',
                });
                reportProgress(1, 'pharm');
            });
        });
    }

    function filterPharmCategory(catId) {
        pharmCategoryFilter = catId;
        if (contentData) renderPharm(contentData);
    }

    function askPharmSocratic(classId) {
        const dc = (contentData?.drug_classes || []).find(d => d.id === classId);
        if (dc) {
            window.WardSocratic?.setModuleContext({
                module: 'dosage',
                tab: 'pharm',
                subject: `${dc.name} — pharmacology`,
                snippet: (dc.mechanism || dc.nclex_focus || '').slice(0, 400),
                topic: 'drug_mechanism',
            });
        }
        openSocraticMode('dosage', 'drug_mechanism');
    }

    async function loadFavorites() {
        const res = await fetch('/api/dosage/favorites');
        const items = await res.json();
        const el = document.getElementById('favorites-container');
        if (!el) return;

        if (!items.length) {
            el.innerHTML = '<p class="text-ward-500 text-sm">No saved calculations yet. Use ★ Save after calculating.</p>';
            return;
        }

        items.forEach(f => { favoritesCache[f.id] = f.inputs_json; });

        el.innerHTML = items.map(f => {
            let result = {};
            try { result = JSON.parse(f.result_json); } catch (_) {}
            return `
                <div class="dose-fav-card">
                    <div>
                        <div class="dose-fav-label">${esc(f.label)}</div>
                        <div class="dose-fav-meta">${esc(f.calc_type)} · ${new Date(f.created_at).toLocaleDateString()}</div>
                        <div class="dose-fav-answer mt-1">${result.answer ?? '—'} ${esc(result.unit || '')}</div>
                    </div>
                    <div class="flex gap-2 shrink-0">
                        <button onclick="Dosage.loadFavorite(${f.id})" class="btn-secondary text-xs">Load</button>
                        <button onclick="Dosage.deleteFavorite(${f.id})" class="text-xs text-ward-danger hover:underline">Delete</button>
                    </div>
                </div>`;
        }).join('');
    }

    function loadFavorite(id) {
        const inputsJson = favoritesCache[id];
        if (!inputsJson) return;
        let inputs;
        try { inputs = JSON.parse(inputsJson); } catch (_) { return; }
        switchTab('calculator');
        const typeSelect = document.getElementById('calc-type');
        if (typeSelect) typeSelect.value = inputs.calc_type || 'tablet_capsule';
        updateCalcForm();
        Object.entries(inputs).forEach(([key, val]) => {
            const el = document.getElementById(key);
            if (el && key !== 'calc_type' && key !== 'show_work') el.value = val;
        });
        if (inputs.show_work !== undefined) {
            const toggle = document.getElementById('show-work-toggle');
            if (toggle) { toggle.checked = inputs.show_work; showWork = inputs.show_work; }
        }
        calculate();
    }

    async function deleteFavorite(id) {
        await fetch(`/api/dosage/favorites/${id}`, { method: 'DELETE' });
        loadFavorites();
    }

    async function reportProgress(items, activityType, score) {
        await fetch('/api/dosage/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items_studied: items, activity_type: activityType, score }),
        });
    }

    async function refreshProgressBar() {
        const res = await fetch('/api/dosage/stats');
        const data = await res.json();
        const pct = document.getElementById('module-progress-pct');
        const bar = document.getElementById('module-progress-bar');
        if (pct) pct.textContent = data.percentage + '%';
        if (bar) bar.style.width = data.percentage + '%';
    }

    function esc(s) {
        if (!s) return '';
        const d = document.createElement('div');
        d.textContent = String(s);
        return d.innerHTML;
    }

    function escAttr(s) {
        if (WardKaTeX?.escapeAttr) return WardKaTeX.escapeAttr(s);
        return esc(s).replace(/"/g, '&quot;');
    }

    /** Wrap LaTeX for KaTeX rendering via data-latex attribute. */
    function mathSpan(latex, display = false) {
        if (!latex) return '';
        const cls = display ? 'math-latex math-display' : 'math-latex';
        return `<span class="${cls}" data-latex="${escAttr(latex)}"></span>`;
    }

    /** Convert dimensional-analysis shorthand to LaTeX for KaTeX. */
    function convertDosageExprToLatex(expr) {
        if (!expr) return '';
        let s = String(expr).trim();
        s = s.replace(/\(([^()]+)\s*÷\s*([^()]+)\)\s*×\s*([A-Za-z0-9]+)/g,
            '\\left(\\frac{$1}{$2}\\right) \\times $3');
        s = s.replace(/([A-Za-z0-9]+)\s*÷\s*([A-Za-z0-9]+)/g, '\\frac{$1}{$2}');
        s = s.replace(/×/g, ' \\times ');
        s = s.replace(/÷/g, ' \\div ');
        s = s.replace(/(\d+)\s*gtt\/mL/g, '$1\\,\\mathrm{gtt/mL}');
        s = s.replace(/mL\/hr/g, '\\mathrm{mL/hr}');
        s = s.replace(/mg\/kg/g, '\\mathrm{mg/kg}');
        return s.trim();
    }

    /** Render a setup/unit line — mathify expressions after '=' when present. */
    function renderDosageMathLine(line) {
        const text = String(line || '').trim();
        if (!text) return '';
        const eqIdx = text.indexOf('=');
        if (eqIdx === -1) {
            return /÷|×|\//.test(text) ? mathSpan(convertDosageExprToLatex(text)) : esc(text);
        }
        const label = text.slice(0, eqIdx).trim();
        const expr = text.slice(eqIdx + 1).trim();
        const exprHtml = /÷|×|\(|\//.test(expr)
            ? mathSpan(convertDosageExprToLatex(expr))
            : esc(expr);
        return `<strong>${esc(label)}</strong> = ${exprHtml}`;
    }

    function renderDerivation(data) {
        const latexPart = data.derivation_latex || '';
        const resultPart = data.derivation_result || '';
        if (!latexPart && !data.derivation) return '';

        if (latexPart) {
            const resultHtml = resultPart
                ? `<span class="dose-derivation-result"> = ${esc(resultPart)}</span>`
                : '';
            return `<div class="dose-derivation">
                <span class="dose-derivation-label">SymPy Derivation</span>
                <div class="dose-derivation-math">${mathSpan(latexPart, true)}${resultHtml}</div>
            </div>`;
        }

        return `<div class="dose-derivation">
            <span class="dose-derivation-label">SymPy Derivation</span>
            ${mathSpan(data.derivation, true)}
        </div>`;
    }

    function renderMath(el) {
        const target = el || document;
        if (typeof WardKaTeX !== 'undefined' && WardKaTeX.renderMathInElementWhenReady) {
            WardKaTeX.renderMathInElementWhenReady(target);
        } else if (typeof WardKaTeX !== 'undefined' && WardKaTeX.renderMathInElement) {
            WardKaTeX.renderMathInElement(target);
        }
    }

    // ── Export ────────────────────────────────────────────────────────────────
    async function exportPracticeSheet() {
        await ensureExportData();
        if (!practiceProblems.length) {
            showToast('No practice problems loaded.', 'error');
            return;
        }

        const rows = practiceProblems.map((p, i) => `
            <tr>
                <td>${i + 1}</td>
                <td><span class="muted">${esc(p.calc_type || '')}</span></td>
                <td>${esc(p.question)}</td>
                <td class="muted">Work space below ↓</td>
            </tr>
            <tr>
                <td colspan="4" style="height:3rem;border-bottom:2px dashed var(--ward-border)"></td>
            </tr>
        `).join('');

        WardExport.openPrintableHtml(
            'NURS 145 Practice Problems',
            `<table>
                <thead><tr><th>#</th><th>Type</th><th>Problem</th><th>Notes</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
            <p class="muted">Source: Ogden &amp; Fluharty, 11th Ed. · Verify answers in The Ward practice tab.</p>`,
            `${practiceProblems.length} problems · dimensional analysis`,
        );
    }

    async function exportTrapsCheatSheet() {
        await ensureExportData();
        const traps = contentData?.error_traps || [];
        if (!traps.length) {
            showToast('Error traps not loaded.', 'error');
            return;
        }

        const rows = traps.map((t, i) => `
            <tr>
                <td>${i + 1}</td>
                <td><strong>${esc(t.title)}</strong></td>
                <td class="trap">${esc(t.trap)}</td>
                <td class="avoid">${esc(t.avoid)}</td>
                <td class="muted">${esc(t.example)}</td>
            </tr>
        `).join('');

        WardExport.openPrintableHtml(
            'Dosage Error Traps Cheat Sheet',
            `<table>
                <thead><tr><th>#</th><th>Trap</th><th>What Goes Wrong</th><th>How to Avoid</th><th>Example</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`,
            `${traps.length} common exam &amp; bedside traps`,
        );
    }

    function exportLastCalculation() {
        if (!lastResult || !lastInputs) {
            showToast('Calculate a dose first, then export.', 'error');
            return;
        }

        const typeLabel = document.querySelector(`#calc-type option[value="${lastInputs.calc_type}"]`)?.textContent
            || lastInputs.calc_type;

        const inputsHtml = Object.entries(lastInputs)
            .filter(([k]) => !['calc_type', 'show_work'].includes(k))
            .map(([k, v]) => `<li><strong>${esc(k.replace(/_/g, ' '))}:</strong> ${esc(v)}</li>`)
            .join('');

        const workHtml = (lastResult.work_steps || []).length
            ? lastResult.work_steps.map(w => `
                <div class="step">
                    <div class="step-num">Step ${w.step} — ${esc(w.title || '')}</div>
                    <div>${w.formula ? mathSpan(convertDosageExprToLatex(w.formula)) : ''}</div>
                    <div class="muted">${esc(w.reasoning)}</div>
                    ${w.result ? `<div style="color:var(--ward-accent);margin-top:0.25rem">→ ${esc(w.result)}</div>` : ''}
                </div>
            `).join('')
            : (lastResult.steps || []).map(s => `<div class="step">${renderDosageMathLine(s)}</div>`).join('');

        const derivationHtml = (lastResult.derivation_latex || lastResult.derivation)
            ? `<h2>SymPy Derivation</h2>${renderDerivation(lastResult)}`
            : '';

        const warningsHtml = (lastResult.safety_warnings || []).length
            ? `<div class="callout"><div class="callout-label">Safety Warnings</div><ul>${lastResult.safety_warnings.map(w => `<li>${esc(w)}</li>`).join('')}</ul></div>`
            : '';

        WardExport.openPrintableHtml(
            'Dosage Calculation — Work Sheet',
            `<p><strong>Calculation type:</strong> ${esc(typeLabel)}</p>
             <div class="callout"><div class="callout-label">Inputs</div><ul>${inputsHtml}</ul></div>
             <div class="answer">Answer: ${esc(lastResult.answer)} ${esc(lastResult.unit || '')}</div>
             ${derivationHtml}
             <h2>Work Steps</h2>
             ${workHtml}
             <div class="callout"><div class="callout-label">Clinical Note</div>${esc(lastResult.clinical_note)}</div>
             ${warningsHtml}`,
            'Exported from NURS 145 Dosage Calculator',
            { renderMath: true },
        );
    }

    function init() {
        updateCalcForm();
        WardTabs.register('/modules/dosage', { validTabs: VALID_TABS, defaultTab: DEFAULT_TAB, switchTab });
        WardTabs.init('/modules/dosage');
        updateFormulaHint();
    }

    function updateFormulaHint() {
        const sel = document.getElementById('calc-type');
        const hint = document.getElementById('calc-formula-hint');
        if (!hint || !sel) return;
        const opt = sel.options[sel.selectedIndex];
        const formula = opt?.dataset?.formula || '';
        hint.innerHTML = formula ? mathSpan(convertDosageExprToLatex(formula)) : '';
        renderMath(hint);
    }

    return {
        switchTab, updateCalcForm, toggleShowWork, toggleFirstPrinciples, calculate, saveFavorite,
        loadPractice, answerPractice, nextPractice, loadFavorites,
        loadFavorite, deleteFavorite, filterPharmCategory, askPharmSocratic,
        exportPracticeSheet, exportTrapsCheatSheet, exportLastCalculation, init,
    };
})();