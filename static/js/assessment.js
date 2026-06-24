/**
 * The Ward — Health Assessment Module (NURS 146)
 */
const Assessment = (() => {
    const MODULE_ID = 'assessment';
    const CHECKLIST_STORAGE_KEY = 'ward_assessment_checklists';

    let sequenceData = [];
    let selectedStepOrder = null;
    let vitalsData = null;
    let contentData = null;
    let redFlagsData = [];
    let selectedSystemId = null;

    let practiceQuestions = [];
    let practiceIndex = 0;
    let practiceCorrect = 0;
    let practiceMode = 'mixed';
    let skillTab = 'skills';

    let checklistData = [];
    let selectedChecklistId = null;
    let checklistChecked = loadChecklistState();

    let soapExercises = [];
    let selectedSoapId = null;

    let docSoapExercises = [];
    let selectedDocSoapId = null;
    let docTab = 'soap-writer';

    let sbarExercises = [];
    let selectedSbarId = null;

    let specialPopData = [];
    let selectedPopId = null;

    let assessNextScenarios = [];
    let assessNextIndex = 0;
    let assessNextCorrect = 0;

    let redFlagDrillQuestions = [];
    let redFlagDrillIndex = 0;
    let redFlagDrillCorrect = 0;

    let flashcards = [];
    let fcIndex = 0;
    let fcFlipped = false;
    let fcSessionReview = 0;

    const VALID_TABS = [
        'head-to-toe', 'systems', 'checklists', 'assess-next',
        'soap', 'special-pop', 'red-flags', 'red-flag-drill', 'practice', 'skills', 'documentation', 'flashcards', 'export',
    ];

    // ── Local storage for checklists ──────────────────────────────────────────
    function loadChecklistState() {
        try {
            return JSON.parse(localStorage.getItem(CHECKLIST_STORAGE_KEY) || '{}');
        } catch {
            return {};
        }
    }

    function saveChecklistState() {
        localStorage.setItem(CHECKLIST_STORAGE_KEY, JSON.stringify(checklistChecked));
    }

    function verifyBtn(source, moduleId) {
        if (!source) return '';
        const mod = moduleId || MODULE_ID;
        return `<button onclick="verifySource('${mod}')" class="btn-verify text-xs mt-3">Verify Source</button>`;
    }

    // ── Tabs ──────────────────────────────────────────────────────────────────
    function switchTab(tab) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.querySelectorAll('.ha-tab-btn').forEach(b => b.classList.remove('active'));
        const panel = document.getElementById('tab-' + tab);
        const btn = document.querySelector(`[data-tab="${tab}"]`);
        if (panel) panel.classList.remove('hidden');
        if (btn) btn.classList.add('active');

        if (tab === 'head-to-toe' && !sequenceData.length) loadHeadToToe();
        if (tab === 'red-flags' && !redFlagsData.length) loadRedFlags();
        if (tab === 'skills' && !contentData) loadSkillsContent();
        if (tab === 'checklists' && !checklistData.length) loadChecklists();
        if (tab === 'soap' && !soapExercises.length) loadSoapList();
        if (tab === 'special-pop' && !specialPopData.length) loadSpecialPopulations();
        if (tab === 'assess-next' && !assessNextScenarios.length) loadAssessNextScenarios();
        if (tab === 'red-flag-drill' && !redFlagDrillQuestions.length) loadRedFlagDrill();
        if (tab === 'documentation') initDocumentationTab();
        if (tab === 'flashcards' && !flashcards.length) loadFlashcards(10);

        history.replaceState(null, '', location.pathname + (tab !== 'head-to-toe' ? '#' + tab : ''));
        window.WardSocratic?.setModuleContext({ module: 'assessment', tab, subject: `Health Assessment · ${tab}`, topic: 'assessment_finding' });
    }

    function initDocumentationTab() {
        if (docTab === 'soap-writer' && !docSoapExercises.length) loadDocSoapList();
        if (docTab === 'sbar' && !sbarExercises.length) loadSbarList();
    }

    function switchDocTab(tab) {
        docTab = tab;
        document.querySelectorAll('[data-doc-tab]').forEach(b => {
            b.classList.toggle('active', b.dataset.docTab === tab);
        });
        const soapPane = document.getElementById('ha-doc-soap-writer');
        const sbarPane = document.getElementById('ha-doc-sbar');
        if (soapPane) soapPane.classList.toggle('hidden', tab !== 'soap-writer');
        if (sbarPane) sbarPane.classList.toggle('hidden', tab !== 'sbar');
        if (tab === 'soap-writer' && !docSoapExercises.length) loadDocSoapList();
        if (tab === 'sbar' && !sbarExercises.length) loadSbarList();
    }

    const DEFAULT_TAB = 'head-to-toe';

    // ── Head-to-Toe ───────────────────────────────────────────────────────────
    async function loadHeadToToe() {
        const res = await fetch('/api/assessment/head-to-toe');
        const data = await res.json();
        sequenceData = data.sequence || [];
        renderSequenceList();
        if (sequenceData.length) selectStep(sequenceData[0].order);

        const contentRes = await fetch('/api/assessment/content');
        const content = await contentRes.json();
        vitalsData = content.vital_signs;
        renderVitalsTable();
    }

    function renderSequenceList() {
        const el = document.getElementById('ha-sequence-list');
        if (!el) return;
        el.innerHTML = sequenceData.map(step => `
            <button type="button" class="ha-sequence-step${selectedStepOrder === step.order ? ' active' : ''}"
                    onclick="Assessment.selectStep(${step.order})">
                <span class="ha-step-num">${step.order}</span>
                <div>
                    <div class="ha-step-title">${step.step}</div>
                    <div class="ha-step-desc">${step.description.substring(0, 80)}…</div>
                </div>
            </button>
        `).join('');
    }

    function selectStep(order) {
        selectedStepOrder = order;
        renderSequenceList();
        const step = sequenceData.find(s => s.order === order);
        const detail = document.getElementById('ha-step-detail');
        if (!detail || !step) return;

        detail.innerHTML = `
            <div class="ha-step-detail-card">
                <h3>Step ${step.order}: ${step.step}</h3>
                <p class="text-sm text-ward-300">${step.description}</p>
                <div class="ha-rationale">
                    <strong class="text-ward-purple">Clinical Reasoning:</strong> ${step.rationale}
                </div>
                ${verifyBtn(step.source)}
            </div>
        `;
        window.WardSocratic?.setModuleContext({
            module: 'assessment',
            tab: 'head-to-toe',
            subject: step.step,
            snippet: step.description || step.rationale || '',
            topic: 'assessment_finding',
        });
        reportProgress(1, 'study');
    }

    function renderVitalsTable() {
        const el = document.getElementById('ha-vitals-table');
        if (!el || !vitalsData?.norms) return;
        el.innerHTML = vitalsData.norms.map(v => `
            <div class="ha-vitals-row">
                <div>
                    <div class="ha-vitals-param">${v.parameter}</div>
                    <div class="ha-vitals-notes">${v.notes}</div>
                </div>
                <div class="ha-vitals-normal">${v.normal}</div>
            </div>
        `).join('');
        if (vitalsData.clinical_note) {
            el.innerHTML += `<p class="text-xs text-ward-accent mt-3 italic">${vitalsData.clinical_note}</p>`;
        }
    }

    // ── Systems ───────────────────────────────────────────────────────────────
    async function selectSystem(systemId) {
        selectedSystemId = systemId;
        document.querySelectorAll('.ha-system-card').forEach(c => {
            c.classList.toggle('selected', c.dataset.system === systemId);
        });

        const res = await fetch(`/api/assessment/systems/${systemId}`);
        const data = await res.json();
        const detail = document.getElementById('ha-system-detail');
        if (!detail) return;

        if (data.error) {
            detail.classList.remove('hidden');
            detail.innerHTML = `<p class="text-ward-danger text-sm">${data.error}</p>`;
            return;
        }

        const sys = data.system;
        detail.classList.remove('hidden');

        const steps = (sys.assessment_steps || []).map(s => `<li>${s}</li>`).join('');
        const normal = (sys.normal_findings || []).map(f => `<li>${f}</li>`).join('');
        const abnormal = (sys.abnormal_findings || []).map(f => `<li>${f}</li>`).join('');
        const red = (sys.red_flags || []).map(f => `<li>${f}</li>`).join('');

        detail.innerHTML = `
            <h2 class="text-lg font-semibold text-ward-100 mb-2">${sys.name}</h2>
            <p class="text-xs text-ward-500 mb-4">Assessment steps and findings comparison</p>

            <div class="mb-4">
                <h4 class="text-xs font-semibold text-ward-purple uppercase mb-2">Assessment Steps</h4>
                <ul class="text-sm text-ward-400 space-y-1 list-disc list-inside">${steps}</ul>
            </div>

            <div class="ha-findings-grid">
                <div class="ha-findings-col normal">
                    <h4>Normal Findings</h4>
                    <ul>${normal}</ul>
                </div>
                <div class="ha-findings-col abnormal">
                    <h4>Abnormal Findings</h4>
                    <ul>${abnormal}</ul>
                </div>
            </div>

            <div class="ha-findings-col red mt-4">
                <h4>Red Flags</h4>
                <ul>${red}</ul>
            </div>

            ${sys.clinical_reasoning ? `
                <div class="ha-clinical-reasoning">
                    <strong>Clinical Reasoning:</strong> ${sys.clinical_reasoning}
                </div>
            ` : ''}
            ${verifyBtn(sys.source)}
        `;
        window.WardSocratic?.setModuleContext({
            module: 'assessment',
            tab: 'systems',
            subject: sys.name,
            snippet: (sys.clinical_reasoning || (sys.red_flags || [])[0] || '').slice(0, 400),
            topic: 'assessment_finding',
        });
        reportProgress(1, 'systems');
    }

    // ── Checklists ────────────────────────────────────────────────────────────
    async function loadChecklists() {
        const el = document.getElementById('ha-checklist-list');
        if (el) el.innerHTML = '<p class="text-ward-500 text-sm">Loading checklists…</p>';

        const res = await fetch('/api/assessment/checklists');
        const data = await res.json();
        checklistData = data.checklists || [];
        renderChecklistList();
        if (checklistData.length) selectChecklist(checklistData[0].id);
    }

    function renderChecklistList() {
        const el = document.getElementById('ha-checklist-list');
        if (!el) return;

        el.innerHTML = checklistData.map(c => {
            const checked = checklistChecked[c.id] || [];
            const pct = c.item_count ? Math.round((checked.length / c.item_count) * 100) : 0;
            return `
                <button type="button" class="ha-checklist-card${selectedChecklistId === c.id ? ' active' : ''}"
                        onclick="Assessment.selectChecklist('${c.id}')">
                    <div class="ha-checklist-title">${c.title}</div>
                    <div class="ha-checklist-meta">${c.item_count} items · ${pct}% complete</div>
                    <div class="ha-checklist-progress">
                        <div class="ha-checklist-progress-fill" style="width:${pct}%"></div>
                    </div>
                </button>
            `;
        }).join('');
    }

    async function selectChecklist(checklistId) {
        selectedChecklistId = checklistId;
        renderChecklistList();

        const res = await fetch(`/api/assessment/checklists/${checklistId}`);
        const data = await res.json();
        const detail = document.getElementById('ha-checklist-detail');
        if (!detail) return;

        if (data.error) {
            detail.innerHTML = `<p class="text-ward-danger text-sm">${data.error}</p>`;
            return;
        }

        const cl = data.checklist;
        const checked = checklistChecked[checklistId] || [];
        const allChecked = checked.length === cl.items.length;

        const items = cl.items.map(item => {
            const isChecked = checked.includes(item.id);
            return `
                <label class="ha-checklist-item${isChecked ? ' checked' : ''}">
                    <input type="checkbox" ${isChecked ? 'checked' : ''}
                           onchange="Assessment.toggleChecklistItem('${checklistId}', '${item.id}')">
                    <div>
                        <div class="ha-checklist-item-text">${item.text}</div>
                        ${item.clinical_note ? `<div class="ha-checklist-item-note">${item.clinical_note}</div>` : ''}
                    </div>
                </label>
            `;
        }).join('');

        detail.innerHTML = `
            <div class="flex flex-wrap justify-between items-start gap-3 mb-4">
                <div>
                    <h2 class="text-lg font-semibold text-ward-100">${cl.title}</h2>
                    <p class="text-xs text-ward-500 mt-1">${cl.description || ''}</p>
                </div>
                <span class="ha-checklist-counter">${checked.length}/${cl.items.length}</span>
            </div>
            <div class="ha-checklist-items">${items}</div>
            ${allChecked ? `
                <div class="ha-checklist-complete mt-4">
                    <span class="text-ward-success font-medium">Checklist complete!</span>
                    <button onclick="Assessment.resetChecklist('${checklistId}')" class="btn-secondary text-xs ml-3">Reset</button>
                </div>
            ` : ''}
            ${verifyBtn(cl.source)}
        `;

        if (allChecked) reportProgress(1, 'checklist');
    }

    function toggleChecklistItem(checklistId, itemId) {
        if (!checklistChecked[checklistId]) checklistChecked[checklistId] = [];
        const arr = checklistChecked[checklistId];
        const idx = arr.indexOf(itemId);
        if (idx >= 0) arr.splice(idx, 1);
        else arr.push(itemId);
        saveChecklistState();
        selectChecklist(checklistId);
        renderChecklistList();
    }

    function resetChecklist(checklistId) {
        checklistChecked[checklistId] = [];
        saveChecklistState();
        selectChecklist(checklistId);
        renderChecklistList();
    }

    // ── Assess Next Scenarios ─────────────────────────────────────────────────
    async function loadAssessNextScenarios() {
        const area = document.getElementById('assess-next-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading scenarios…</p>';

        const res = await fetch('/api/assessment/scenarios/assess-next?count=4');
        const data = await res.json();
        assessNextScenarios = data.scenarios || [];
        assessNextIndex = 0;
        assessNextCorrect = 0;
        showAssessNextScenario();
    }

    function showAssessNextScenario() {
        const area = document.getElementById('assess-next-area');
        const scoreEl = document.getElementById('assess-next-score');
        if (!area) return;

        if (assessNextIndex >= assessNextScenarios.length) {
            const pct = assessNextScenarios.length
                ? Math.round((assessNextCorrect / assessNextScenarios.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-ward-purple mb-2">${assessNextCorrect}/${assessNextScenarios.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">${pct >= 80 ? 'Strong clinical sequencing!' : 'Review head-to-toe priority and red flags for missed concepts.'}</p>
                    <button onclick="Assessment.loadAssessNextScenarios()" class="btn-primary mt-4 text-sm">New Scenarios</button>
                </div>`;
            if (scoreEl) scoreEl.textContent = `Final: ${assessNextCorrect}/${assessNextScenarios.length}`;
            reportProgress(assessNextCorrect, 'scenarios', pct);
            return;
        }

        const s = assessNextScenarios[assessNextIndex];
        if (scoreEl) scoreEl.textContent = `${assessNextCorrect}/${assessNextIndex}`;

        const findings = (s.findings_so_far || []).map(f => `<li>${f}</li>`).join('');

        area.innerHTML = `
            <div class="scenario-card">
                <div class="scenario-title">${s.title}</div>
                <p class="scenario-setup">${s.setup}</p>
                ${findings ? `
                    <div class="ha-findings-so-far">
                        <div class="text-xs font-semibold text-ward-purple uppercase mb-1">Findings So Far</div>
                        <ul class="text-sm text-ward-400">${findings}</ul>
                    </div>
                ` : ''}
                <p class="text-ward-200 font-medium mt-4 mb-3">${s.question}</p>
                <div class="space-y-2" id="assess-next-options">
                    ${s.options.map((opt, i) => `
                        <button type="button" class="practice-option" onclick="Assessment.answerAssessNext(${i})">
                            <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${opt}
                        </button>
                    `).join('')}
                </div>
                <div id="assess-next-feedback" class="mt-4 hidden"></div>
            </div>
            <p class="text-center text-xs text-ward-600 mt-3">Scenario ${assessNextIndex + 1} of ${assessNextScenarios.length}</p>
        `;
    }

    async function answerAssessNext(selected) {
        const s = assessNextScenarios[assessNextIndex];
        const selectedOption = s.options[selected];

        const res = await fetch('/api/assessment/scenarios/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario_id: s.id,
                selected_index: selected,
                selected_option: selectedOption,
            }),
        });
        const result = await res.json();
        const isCorrect = result.correct;
        if (isCorrect) assessNextCorrect++;

        document.querySelectorAll('#assess-next-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (s.options[i] === result.correct_answer) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('assess-next-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${isCorrect ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${isCorrect ? 'text-ward-success' : 'text-ward-danger'}">${result.feedback}</p>
                    <p class="text-ward-300 mt-1">${result.explanation}</p>
                    ${result.clinical_why ? `<p class="text-xs text-ward-accent mt-2">${result.clinical_why}</p>` : ''}
                    ${verifyBtn(result.source)}
                </div>
                <button onclick="Assessment.nextAssessNext()" class="btn-primary w-full mt-3 text-sm">Next Scenario</button>
            `;
        }
        refreshModuleProgress();
    }

    function nextAssessNext() {
        assessNextIndex++;
        showAssessNextScenario();
    }

    // ── SOAP Notes ────────────────────────────────────────────────────────────
    async function loadSoapList() {
        const el = document.getElementById('ha-soap-list');
        if (el) el.innerHTML = '<p class="text-ward-500 text-sm">Loading exercises…</p>';

        const res = await fetch('/api/assessment/soap');
        const data = await res.json();
        soapExercises = data.exercises || [];
        renderSoapList();
        if (soapExercises.length) selectSoapExercise(soapExercises[0].id);
    }

    function renderSoapList() {
        const el = document.getElementById('ha-soap-list');
        if (!el) return;
        el.innerHTML = soapExercises.map(e => `
            <button type="button" class="ha-soap-card${selectedSoapId === e.id ? ' active' : ''}"
                    onclick="Assessment.selectSoapExercise('${e.id}')">
                <div class="ha-soap-title">${e.title}</div>
                <div class="ha-soap-preview">${(e.patient_context || '').substring(0, 60)}…</div>
            </button>
        `).join('');
    }

    async function selectSoapExercise(exerciseId) {
        selectedSoapId = exerciseId;
        renderSoapList();

        const res = await fetch(`/api/assessment/soap/${exerciseId}`);
        const data = await res.json();
        const detail = document.getElementById('ha-soap-detail');
        if (!detail) return;

        if (data.error) {
            detail.innerHTML = `<p class="text-ward-danger text-sm">${data.error}</p>`;
            return;
        }

        const ex = data.exercise;
        const findings = ex.findings || {};
        const findingsHtml = Object.entries(findings).map(([k, v]) => `
            <div class="ha-soap-finding">
                <span class="ha-soap-finding-label">${k}</span>
                <span class="ha-soap-finding-value">${v}</span>
            </div>
        `).join('');

        detail.innerHTML = `
            <h2 class="text-lg font-semibold text-ward-100 mb-2">${ex.title}</h2>
            <p class="text-sm text-ward-400 mb-4">${ex.patient_context}</p>

            <div class="ha-soap-findings mb-5">
                <h4 class="text-xs font-semibold text-ward-purple uppercase mb-2">Clinical Findings</h4>
                ${findingsHtml}
            </div>

            <div class="ha-soap-form">
                <div class="ha-soap-section">
                    <label class="ha-soap-label">S — Subjective</label>
                    <textarea id="soap-s" class="ha-soap-textarea" rows="3" placeholder="Patient report, history, symptoms…"></textarea>
                </div>
                <div class="ha-soap-section">
                    <label class="ha-soap-label">O — Objective</label>
                    <textarea id="soap-o" class="ha-soap-textarea" rows="3" placeholder="Measurable findings, vitals, exam data…"></textarea>
                </div>
                <div class="ha-soap-section">
                    <label class="ha-soap-label">A — Assessment</label>
                    <textarea id="soap-a" class="ha-soap-textarea" rows="2" placeholder="Nursing diagnosis / clinical impression…"></textarea>
                </div>
                <div class="ha-soap-section">
                    <label class="ha-soap-label">P — Plan</label>
                    <textarea id="soap-p" class="ha-soap-textarea" rows="2" placeholder="Nursing interventions, notifications, monitoring…"></textarea>
                </div>
            </div>

            <button onclick="Assessment.revealSoapModel('${exerciseId}')" class="btn-primary w-full mt-4 text-sm">Compare to Model Note</button>
            <div id="ha-soap-model" class="hidden mt-4"></div>
        `;
        reportProgress(1, 'soap');
    }

    async function revealSoapModel(exerciseId) {
        const res = await fetch(`/api/assessment/soap/${exerciseId}`);
        const data = await res.json();
        const modelEl = document.getElementById('ha-soap-model');
        if (!modelEl || data.error) return;

        const ex = data.exercise;
        const model = ex.model_soap || {};
        const tips = (ex.documentation_tips || []).map(t => `<li>${t}</li>`).join('');

        modelEl.classList.remove('hidden');
        modelEl.innerHTML = `
            <div class="ha-soap-model-card">
                <h4 class="text-sm font-semibold text-ward-success mb-3">Model SOAP Note</h4>
                ${['subjective', 'objective', 'assessment', 'plan'].map(key => `
                    <div class="ha-soap-model-section">
                        <div class="ha-soap-model-letter">${key.charAt(0).toUpperCase()}</div>
                        <div class="ha-soap-model-text">${model[key] || ''}</div>
                    </div>
                `).join('')}
                ${tips ? `
                    <div class="ha-soap-tips mt-4">
                        <div class="text-xs font-semibold text-ward-purple uppercase mb-1">Documentation Tips</div>
                        <ul class="text-xs text-ward-400">${tips}</ul>
                    </div>
                ` : ''}
                ${verifyBtn(ex.source)}
            </div>
        `;
        reportProgress(1, 'soap_complete');
    }

    // ── Documentation (SOAP validate + SBAR) ────────────────────────────────
    async function loadDocSoapList() {
        const el = document.getElementById('ha-doc-soap-list');
        if (el) el.innerHTML = '<p class="text-ward-500 text-sm">Loading exercises…</p>';

        const res = await fetch('/api/assessment/soap');
        const data = await res.json();
        docSoapExercises = data.exercises || [];
        renderDocSoapList();
        if (docSoapExercises.length) selectDocSoapExercise(docSoapExercises[0].id);
    }

    function renderDocSoapList() {
        const el = document.getElementById('ha-doc-soap-list');
        if (!el) return;
        el.innerHTML = docSoapExercises.map(e => `
            <button type="button" class="ha-soap-card${selectedDocSoapId === e.id ? ' active' : ''}"
                    onclick="Assessment.selectDocSoapExercise('${e.id}')">
                <div class="ha-soap-title">${e.title}</div>
                <div class="ha-soap-preview">${(e.patient_context || '').substring(0, 60)}…</div>
            </button>
        `).join('');
    }

    async function selectDocSoapExercise(exerciseId) {
        selectedDocSoapId = exerciseId;
        renderDocSoapList();

        const res = await fetch(`/api/assessment/soap/${exerciseId}`);
        const data = await res.json();
        const detail = document.getElementById('ha-doc-soap-detail');
        if (!detail) return;

        if (data.error) {
            detail.innerHTML = `<p class="text-ward-danger text-sm">${data.error}</p>`;
            return;
        }

        const ex = data.exercise;
        const findings = ex.findings || {};
        const findingsHtml = Object.entries(findings).map(([k, v]) => `
            <div class="ha-soap-finding">
                <span class="ha-soap-finding-label">${k}</span>
                <span class="ha-soap-finding-value">${v}</span>
            </div>
        `).join('');

        detail.innerHTML = `
            <h2 class="text-lg font-semibold text-ward-100 mb-2">${ex.title}</h2>
            <p class="text-sm text-ward-400 mb-4">${ex.patient_context}</p>

            <div class="ha-soap-findings mb-5">
                <h4 class="text-xs font-semibold text-ward-purple uppercase mb-2">Clinical Findings</h4>
                ${findingsHtml}
            </div>

            <div class="ha-soap-form">
                <div class="ha-soap-section">
                    <label class="ha-soap-label">S — Subjective</label>
                    <textarea id="doc-soap-s" class="ha-soap-textarea" rows="3" placeholder="Patient report, history, symptoms…"></textarea>
                </div>
                <div class="ha-soap-section">
                    <label class="ha-soap-label">O — Objective</label>
                    <textarea id="doc-soap-o" class="ha-soap-textarea" rows="3" placeholder="Measurable findings, vitals, exam data…"></textarea>
                </div>
                <div class="ha-soap-section">
                    <label class="ha-soap-label">A — Assessment</label>
                    <textarea id="doc-soap-a" class="ha-soap-textarea" rows="2" placeholder="Nursing diagnosis / clinical impression…"></textarea>
                </div>
                <div class="ha-soap-section">
                    <label class="ha-soap-label">P — Plan</label>
                    <textarea id="doc-soap-p" class="ha-soap-textarea" rows="2" placeholder="Nursing interventions, notifications, monitoring…"></textarea>
                </div>
            </div>

            <button onclick="Assessment.submitSoapValidate('${exerciseId}')" class="btn-primary w-full mt-4 text-sm" id="doc-soap-submit-btn">
                Submit for Feedback
            </button>
            <div id="ha-doc-soap-feedback" class="hidden mt-4"></div>
        `;
    }

    function scoreColor(score) {
        if (score >= 80) return 'text-ward-success';
        if (score >= 70) return 'text-ward-warning';
        return 'text-ward-danger';
    }

    function renderSoapFeedback(result) {
        const el = document.getElementById('ha-doc-soap-feedback');
        if (!el) return;
        el.classList.remove('hidden');

        const sections = result.section_scores || {};
        const sectionBars = Object.entries(sections).map(([name, score]) => `
            <div class="ha-doc-score-row">
                <span class="ha-doc-score-label">${name.charAt(0).toUpperCase() + name.slice(1)}</span>
                <div class="ha-doc-score-bar-wrap">
                    <div class="ha-doc-score-bar" style="width: ${score}%"></div>
                </div>
                <span class="ha-doc-score-value ${scoreColor(score)}">${score}%</span>
            </div>
        `).join('');

        const feedback = (result.feedback || []).map(f => `<li class="text-ward-warning">${f}</li>`).join('');
        const strengths = (result.strengths || []).map(s => `<li class="text-ward-success">${s}</li>`).join('');
        const tips = (result.documentation_tips || []).map(t => `<li>${t}</li>`).join('');

        let modelHtml = '';
        if (result.model_soap) {
            modelHtml = `
                <div class="ha-soap-model-card mt-4">
                    <h4 class="text-sm font-semibold text-ward-success mb-3">Model SOAP Note (revealed — score ≥ ${result.pass_threshold}%)</h4>
                    ${['subjective', 'objective', 'assessment', 'plan'].map(key => `
                        <div class="ha-soap-model-section">
                            <div class="ha-soap-model-letter">${key.charAt(0).toUpperCase()}</div>
                            <div class="ha-soap-model-text">${result.model_soap[key] || ''}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        el.innerHTML = `
            <div class="ha-doc-feedback-card ${result.passed ? 'passed' : 'needs-work'}">
                <div class="flex flex-wrap justify-between items-center gap-2 mb-4">
                    <h4 class="text-sm font-semibold text-ward-100">Rubric Feedback</h4>
                    <span class="ha-doc-overall-score ${scoreColor(result.overall_score)}">
                        ${result.overall_score}% ${result.passed ? '✓ Passed' : '— Revise'}
                    </span>
                </div>
                <div class="ha-doc-score-grid mb-4">${sectionBars}</div>
                ${strengths ? `<div class="mb-3"><div class="text-xs font-semibold text-ward-success uppercase mb-1">Strengths</div><ul class="text-xs space-y-1 list-disc list-inside">${strengths}</ul></div>` : ''}
                ${feedback ? `<div class="mb-3"><div class="text-xs font-semibold text-ward-warning uppercase mb-1">Areas to Improve</div><ul class="text-xs space-y-1 list-disc list-inside">${feedback}</ul></div>` : ''}
                ${tips ? `<div class="ha-soap-tips"><div class="text-xs font-semibold text-ward-purple uppercase mb-1">Documentation Tips</div><ul class="text-xs text-ward-400 list-disc list-inside">${tips}</ul></div>` : ''}
                ${modelHtml}
            </div>
        `;
    }

    async function submitSoapValidate(exerciseId) {
        const btn = document.getElementById('doc-soap-submit-btn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Evaluating…';
        }

        const payload = {
            exercise_id: exerciseId,
            subjective: document.getElementById('doc-soap-s')?.value || '',
            objective: document.getElementById('doc-soap-o')?.value || '',
            assessment: document.getElementById('doc-soap-a')?.value || '',
            plan: document.getElementById('doc-soap-p')?.value || '',
        };

        try {
            const res = await fetch('/api/assessment/soap/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            if (data.error || !data.valid) {
                const el = document.getElementById('ha-doc-soap-feedback');
                if (el) {
                    el.classList.remove('hidden');
                    el.innerHTML = `<p class="text-ward-danger text-sm">${data.error || 'Validation failed.'}</p>`;
                }
                return;
            }
            renderSoapFeedback(data);
            if (data.passed) reportProgress(1, 'documentation', data.overall_score);
            refreshModuleProgress();
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Submit for Feedback';
            }
        }
    }

    async function loadSbarList() {
        const el = document.getElementById('ha-sbar-list');
        if (el) el.innerHTML = '<p class="text-ward-500 text-sm">Loading scenarios…</p>';

        const res = await fetch('/api/assessment/sbar');
        const data = await res.json();
        sbarExercises = data.exercises || [];
        renderSbarList();
        if (sbarExercises.length) selectSbarExercise(sbarExercises[0].id);
    }

    function renderSbarList() {
        const el = document.getElementById('ha-sbar-list');
        if (!el) return;
        el.innerHTML = sbarExercises.map(e => `
            <button type="button" class="ha-sbar-card${selectedSbarId === e.id ? ' active' : ''}"
                    onclick="Assessment.selectSbarExercise('${e.id}')">
                <div class="ha-sbar-title">${e.title}</div>
                <div class="ha-sbar-preview">${(e.situation || '').substring(0, 55)}…</div>
            </button>
        `).join('');
    }

    async function selectSbarExercise(exerciseId) {
        selectedSbarId = exerciseId;
        renderSbarList();

        const res = await fetch(`/api/assessment/sbar/${exerciseId}`);
        const data = await res.json();
        const detail = document.getElementById('ha-sbar-detail');
        if (!detail) return;

        if (data.error) {
            detail.innerHTML = `<p class="text-ward-danger text-sm">${data.error}</p>`;
            return;
        }

        const ex = data.exercise;
        const findings = ex.findings || {};
        const findingsHtml = Object.keys(findings).length
            ? Object.entries(findings).map(([k, v]) => `
                <div class="ha-soap-finding">
                    <span class="ha-soap-finding-label">${k}</span>
                    <span class="ha-soap-finding-value">${v}</span>
                </div>
            `).join('')
            : '';

        detail.innerHTML = `
            <h2 class="text-lg font-semibold text-ward-100 mb-4">${ex.title}</h2>

            <div class="ha-sbar-context mb-4">
                <div class="ha-sbar-context-block">
                    <div class="ha-sbar-letter">S</div>
                    <div>
                        <div class="ha-sbar-context-label">Situation</div>
                        <p class="text-sm text-ward-300">${ex.situation}</p>
                    </div>
                </div>
                <div class="ha-sbar-context-block">
                    <div class="ha-sbar-letter">B</div>
                    <div>
                        <div class="ha-sbar-context-label">Background</div>
                        <p class="text-sm text-ward-300">${ex.background}</p>
                    </div>
                </div>
            </div>

            ${findingsHtml ? `
                <div class="ha-soap-findings mb-5">
                    <h4 class="text-xs font-semibold text-ward-purple uppercase mb-2">Current Findings</h4>
                    ${findingsHtml}
                </div>
            ` : ''}

            <div class="ha-soap-form">
                <div class="ha-soap-section">
                    <label class="ha-soap-label">A — Assessment</label>
                    <textarea id="sbar-a" class="ha-soap-textarea" rows="3" placeholder="Your clinical interpretation of the data…"></textarea>
                </div>
                <div class="ha-soap-section">
                    <label class="ha-soap-label">R — Recommendation</label>
                    <textarea id="sbar-r" class="ha-soap-textarea" rows="3" placeholder="Specific requests for the provider…"></textarea>
                </div>
            </div>

            <button onclick="Assessment.revealSbarModel('${exerciseId}')" class="btn-primary w-full mt-4 text-sm">Compare to Model Handoff</button>
            <div id="ha-sbar-model" class="hidden mt-4"></div>
        `;
        reportProgress(1, 'documentation');
    }

    async function revealSbarModel(exerciseId) {
        const res = await fetch(`/api/assessment/sbar/${exerciseId}`);
        const data = await res.json();
        const modelEl = document.getElementById('ha-sbar-model');
        if (!modelEl || data.error) return;

        const ex = data.exercise;
        const tips = (ex.teaching_points || []).map(t => `<li>${t}</li>`).join('');

        modelEl.classList.remove('hidden');
        modelEl.innerHTML = `
            <div class="ha-sbar-model-card">
                <h4 class="text-sm font-semibold text-ward-success mb-3">Model SBAR Handoff</h4>
                <div class="ha-sbar-model-section">
                    <div class="ha-sbar-letter">A</div>
                    <div class="ha-sbar-model-text">${ex.model_assessment}</div>
                </div>
                <div class="ha-sbar-model-section">
                    <div class="ha-sbar-letter">R</div>
                    <div class="ha-sbar-model-text">${ex.model_recommendation}</div>
                </div>
                ${tips ? `
                    <div class="ha-soap-tips mt-4">
                        <div class="text-xs font-semibold text-ward-purple uppercase mb-1">Teaching Points</div>
                        <ul class="text-xs text-ward-400 list-disc list-inside">${tips}</ul>
                    </div>
                ` : ''}
                ${verifyBtn(ex.source)}
            </div>
        `;
        reportProgress(1, 'documentation');
    }

    // ── Special Populations ───────────────────────────────────────────────────
    async function loadSpecialPopulations() {
        const grid = document.getElementById('ha-pop-grid');
        if (grid) grid.innerHTML = '<p class="text-ward-500 text-sm col-span-full">Loading…</p>';

        const res = await fetch('/api/assessment/special-populations');
        const data = await res.json();
        specialPopData = data.populations || [];
        renderPopGrid();
        if (specialPopData.length) selectPopulation(specialPopData[0].id);
    }

    function renderPopGrid() {
        const grid = document.getElementById('ha-pop-grid');
        if (!grid) return;
        grid.innerHTML = specialPopData.map(p => `
            <button type="button" class="ha-pop-card${selectedPopId === p.id ? ' active' : ''}"
                    onclick="Assessment.selectPopulation('${p.id}')">
                <div class="ha-pop-name">${p.name}</div>
                <div class="ha-pop-age">${p.age_range || ''}</div>
            </button>
        `).join('');
    }

    async function selectPopulation(popId) {
        selectedPopId = popId;
        renderPopGrid();

        const res = await fetch(`/api/assessment/special-populations/${popId}`);
        const data = await res.json();
        const detail = document.getElementById('ha-pop-detail');
        if (!detail) return;

        if (data.error) {
            detail.classList.remove('hidden');
            detail.innerHTML = `<p class="text-ward-danger text-sm">${data.error}</p>`;
            return;
        }

        const pop = data.population;
        detail.classList.remove('hidden');

        const considerations = (pop.assessment_considerations || []).map(c => `<li>${c}</li>`).join('');
        const nva = (pop.normal_vs_abnormal || []).map(row => `
            <tr>
                <td class="ha-nva-finding">${row.finding}</td>
                <td class="ha-nva-normal">${row.normal}</td>
                <td class="ha-nva-abnormal">${row.abnormal}</td>
            </tr>
        `).join('');
        const red = (pop.red_flags || []).map(f => `<li>${f}</li>`).join('');

        detail.innerHTML = `
            <h2 class="text-lg font-semibold text-ward-100 mb-1">${pop.name}</h2>
            <p class="text-xs text-ward-500 mb-3">${pop.age_range}</p>
            <p class="text-sm text-ward-400 mb-4">${pop.overview}</p>

            <div class="mb-4">
                <h4 class="text-xs font-semibold text-ward-purple uppercase mb-2">Assessment Considerations</h4>
                <ul class="text-sm text-ward-400 space-y-1 list-disc list-inside">${considerations}</ul>
            </div>

            <div class="ha-nva-table-wrap mb-4">
                <h4 class="text-xs font-semibold text-ward-purple uppercase mb-2">Normal vs. Abnormal</h4>
                <table class="ha-nva-table">
                    <thead>
                        <tr>
                            <th>Finding</th>
                            <th>Normal</th>
                            <th>Abnormal</th>
                        </tr>
                    </thead>
                    <tbody>${nva}</tbody>
                </table>
            </div>

            <div class="ha-findings-col red mb-4">
                <h4>Red Flags</h4>
                <ul>${red}</ul>
            </div>

            ${pop.clinical_reasoning ? `
                <div class="ha-clinical-reasoning">
                    <strong>Clinical Reasoning:</strong> ${pop.clinical_reasoning}
                </div>
            ` : ''}
            ${verifyBtn(pop.source)}
        `;
        reportProgress(1, 'special_pop');
    }

    // ── Red Flags ─────────────────────────────────────────────────────────────
    async function loadRedFlags() {
        const el = document.getElementById('ha-red-flags-list');
        if (el) el.innerHTML = '<p class="text-ward-500 text-sm">Loading red flags…</p>';

        const res = await fetch('/api/assessment/red-flags');
        const data = await res.json();
        redFlagsData = data.red_flags || [];
        renderRedFlags();
    }

    function renderRedFlags() {
        const el = document.getElementById('ha-red-flags-list');
        if (!el) return;

        el.innerHTML = redFlagsData.map(rf => `
            <div class="ha-red-flag-card">
                <div class="ha-red-flag-finding">${rf.finding}</div>
                <div class="ha-red-flag-action"><strong>Action:</strong> ${rf.action}</div>
                <div class="ha-red-flag-meta">
                    <span class="ha-priority-badge">${rf.priority}</span>
                    <span class="ha-system-badge">${rf.system}</span>
                </div>
            </div>
        `).join('');
    }

    // ── Red Flag Triage Drill ─────────────────────────────────────────────────
    async function loadRedFlagDrill() {
        const area = document.getElementById('red-flag-drill-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading drill…</p>';

        const res = await fetch('/api/assessment/red-flag-drill?count=5');
        const data = await res.json();
        redFlagDrillQuestions = data.questions || [];
        redFlagDrillIndex = 0;
        redFlagDrillCorrect = 0;
        showRedFlagDrillQuestion();
    }

    function showRedFlagDrillQuestion() {
        const area = document.getElementById('red-flag-drill-area');
        const scoreEl = document.getElementById('red-flag-drill-score');
        if (!area) return;

        if (redFlagDrillIndex >= redFlagDrillQuestions.length) {
            const pct = redFlagDrillQuestions.length
                ? Math.round((redFlagDrillCorrect / redFlagDrillQuestions.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-ward-purple mb-2">${redFlagDrillCorrect}/${redFlagDrillQuestions.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">${pct >= 80 ? 'Strong triage judgment!' : 'Review the Red Flags reference tab for missed escalation paths.'}</p>
                    <button onclick="Assessment.loadRedFlagDrill()" class="btn-primary mt-4 text-sm">New Drill</button>
                </div>`;
            if (scoreEl) scoreEl.textContent = `Final: ${redFlagDrillCorrect}/${redFlagDrillQuestions.length}`;
            reportProgress(redFlagDrillCorrect, 'red_flags', pct);
            return;
        }

        const q = redFlagDrillQuestions[redFlagDrillIndex];
        if (scoreEl) scoreEl.textContent = `${redFlagDrillCorrect}/${redFlagDrillIndex}`;

        const meta = `
            <div class="ha-red-flag-drill-meta">
                <span class="ha-priority-badge">${q.priority || 'immediate'}</span>
                <span class="ha-system-badge">${q.system || 'general'}</span>
            </div>
        `;

        area.innerHTML = `
            <div class="scenario-card ha-red-flag-drill-card">
                <div class="text-xs font-semibold text-ward-danger uppercase mb-2">Critical Finding</div>
                <div class="ha-red-flag-drill-finding">${q.finding}</div>
                ${meta}
                <p class="text-ward-200 font-medium mt-4 mb-3">What is the correct immediate nursing action?</p>
                <div class="space-y-2" id="red-flag-drill-options">
                    ${q.options.map((opt, i) => `
                        <button type="button" class="practice-option" onclick="Assessment.answerRedFlagDrill(${i})">
                            <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${opt}
                        </button>
                    `).join('')}
                </div>
                <div id="red-flag-drill-feedback" class="mt-4 hidden"></div>
            </div>
            <p class="text-center text-xs text-ward-600 mt-3">Question ${redFlagDrillIndex + 1} of ${redFlagDrillQuestions.length}</p>
        `;
    }

    async function answerRedFlagDrill(selected) {
        const q = redFlagDrillQuestions[redFlagDrillIndex];
        const selectedOption = q.options[selected];

        const res = await fetch('/api/assessment/red-flag-drill/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                flag_id: q.id,
                selected_index: selected,
                selected_option: selectedOption,
            }),
        });
        const result = await res.json();
        const isCorrect = result.correct;
        if (isCorrect) redFlagDrillCorrect++;

        document.querySelectorAll('#red-flag-drill-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (q.options[i] === result.correct_answer) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('red-flag-drill-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${isCorrect ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${isCorrect ? 'text-ward-success' : 'text-ward-danger'}">${result.feedback}</p>
                    <p class="text-ward-300 mt-1">${result.explanation}</p>
                    ${result.clinical_why ? `<p class="text-xs text-ward-accent mt-2">${result.clinical_why}</p>` : ''}
                    ${!isCorrect && result.escalation_path ? `
                        <div class="ha-escalation-path mt-3">
                            <div class="text-xs font-semibold text-ward-danger uppercase mb-1">Escalation Path</div>
                            <p class="text-sm text-ward-300">${result.escalation_path}</p>
                        </div>
                    ` : ''}
                    ${verifyBtn(result.source)}
                </div>
                <button onclick="Assessment.nextRedFlagDrill()" class="btn-primary w-full mt-3 text-sm">Next Question</button>
            `;
        }
        refreshModuleProgress();
    }

    function nextRedFlagDrill() {
        redFlagDrillIndex++;
        showRedFlagDrillQuestion();
    }

    // ── Skills ────────────────────────────────────────────────────────────────
    async function loadSkillsContent() {
        const el = document.getElementById('ha-skills-content');
        if (el) el.innerHTML = '<p class="text-ward-500 text-sm">Loading skills…</p>';

        const res = await fetch('/api/assessment/content');
        contentData = await res.json();
        renderSkillTab();
    }

    function switchSkillTab(tab) {
        skillTab = tab;
        document.querySelectorAll('.ha-learn-subtab').forEach(b => {
            b.classList.toggle('active', b.dataset.skillTab === tab);
        });
        if (!contentData) loadSkillsContent();
        else renderSkillTab();
    }

    function renderSkillTab() {
        const el = document.getElementById('ha-skills-content');
        if (!el || !contentData) return;

        if (skillTab === 'skills') {
            el.innerHTML = (contentData.skills || []).map(s => `
                <div class="ha-skill-card">
                    <div class="ha-skill-title">${s.title}</div>
                    <div class="ha-skill-content">${s.content}</div>
                    ${s.clinical_tip ? `<div class="ha-skill-tip">Tip: ${s.clinical_tip}</div>` : ''}
                    ${verifyBtn(s.source)}
                </div>
            `).join('');
        } else if (skillTab === 'pain') {
            const pain = contentData.pain_assessment || {};
            const components = (pain.components || []).map(c => `
                <div class="ha-pqrst-card">
                    <div class="ha-pqrst-letter">${c.letter}</div>
                    <div class="ha-pqrst-element">${c.element}</div>
                    <p class="text-xs text-ward-400 mt-2">${c.question}</p>
                    ${c.clinical_tip ? `<p class="text-xs text-ward-purple mt-1 italic">${c.clinical_tip}</p>` : ''}
                </div>
            `).join('');
            const scales = (pain.scales || []).map(sc => `
                <li class="text-sm text-ward-400 py-1"><strong class="text-ward-200">${sc.name}</strong> — ${sc.use} (${sc.range})</li>
            `).join('');
            el.innerHTML = `
                <h3 class="text-base font-semibold text-ward-purple mb-3">${pain.title || 'PQRST Pain Assessment'}</h3>
                <div class="ha-pqrst-grid">${components}</div>
                <h4 class="text-sm font-semibold text-ward-200 mb-2">Pain Scales</h4>
                <ul class="mb-4">${scales}</ul>
                ${verifyBtn(pain.source)}
            `;
        } else if (skillTab === 'interview') {
            el.innerHTML = (contentData.interview_techniques || []).map(t => `
                <div class="ha-interview-card">
                    <div class="ha-interview-title">${t.technique}</div>
                    <p class="text-sm text-ward-400 mt-1">${t.description}</p>
                    ${t.example ? `<div class="ha-interview-example">Example: "${t.example}"</div>` : ''}
                    ${t.clinical_relevance ? `<p class="text-xs text-ward-accent mt-2">${t.clinical_relevance}</p>` : ''}
                    ${verifyBtn(t.source)}
                </div>
            `).join('');
        }
        reportProgress(1, 'skills');
    }

    // ── Practice ──────────────────────────────────────────────────────────────
    function setPracticeMode(mode) {
        practiceMode = mode;
        document.querySelectorAll('.ha-mode-pill').forEach(p => {
            p.classList.toggle('active', p.dataset.mode === mode);
        });
    }

    async function startPractice(count) {
        const area = document.getElementById('practice-question-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading questions…</p>';

        const res = await fetch(`/api/assessment/practice?count=${count}&mode=${practiceMode}`);
        const data = await res.json();
        practiceQuestions = data.questions;
        practiceIndex = 0;
        practiceCorrect = 0;
        showPracticeQuestion();
    }

    function showPracticeQuestion() {
        const area = document.getElementById('practice-question-area');
        const scoreEl = document.getElementById('practice-score');
        if (!area) return;

        if (practiceIndex >= practiceQuestions.length) {
            const pct = practiceQuestions.length
                ? Math.round((practiceCorrect / practiceQuestions.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-ward-purple mb-2">${practiceCorrect}/${practiceQuestions.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">${pct >= 80 ? 'Strong assessment knowledge!' : 'Review red flags and system tabs for missed concepts.'}</p>
                </div>`;
            if (scoreEl) scoreEl.textContent = `Final: ${practiceCorrect}/${practiceQuestions.length}`;
            reportProgress(practiceCorrect, 'practice', pct);
            return;
        }

        const q = practiceQuestions[practiceIndex];
        if (scoreEl) scoreEl.textContent = `${practiceCorrect}/${practiceIndex}`;

        const cat = q.nclex_category ? `<span class="text-xs text-ward-600 ml-2">${q.nclex_category}</span>` : '';
        const sys = q.system ? `<span class="text-xs text-ward-purple ml-1">· ${q.system}</span>` : '';

        area.innerHTML = `
            <div class="mb-2 text-xs text-ward-purple uppercase tracking-wide">NCLEX-Style${cat}${sys}</div>
            <p class="text-ward-100 mb-4">${q.question}</p>
            <div class="space-y-2" id="practice-options">
                ${q.options.map((opt, i) => `
                    <button type="button" class="practice-option" onclick="Assessment.answerPractice(${i})">
                        <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${opt}
                    </button>
                `).join('')}
            </div>
            <div id="practice-feedback" class="mt-4 hidden"></div>
        `;
    }

    async function answerPractice(selected) {
        const q = practiceQuestions[practiceIndex];
        const selectedOption = q.options[selected];

        const res = await fetch('/api/assessment/practice/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: q.id,
                selected_index: selected,
                selected_option: selectedOption,
            }),
        });
        const result = await res.json();
        const isCorrect = result.correct;
        if (isCorrect) practiceCorrect++;

        document.querySelectorAll('#practice-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (q.options[i] === result.correct_answer) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('practice-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${isCorrect ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${isCorrect ? 'text-ward-success' : 'text-ward-danger'}">${result.feedback}</p>
                    <p class="text-ward-300 mt-1">${result.explanation}</p>
                    ${result.clinical_why ? `<p class="text-xs text-ward-accent mt-2">${result.clinical_why}</p>` : ''}
                    ${verifyBtn(result.source)}
                </div>
                <button onclick="Assessment.nextPracticeQuestion()" class="btn-primary w-full mt-3 text-sm">Next Question</button>
            `;
        }
        refreshModuleProgress();
    }

    function nextPracticeQuestion() {
        practiceIndex++;
        showPracticeQuestion();
    }

    // ── Progress ──────────────────────────────────────────────────────────────
    async function reportProgress(items, activityType, score) {
        await fetch('/api/assessment/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items_studied: items, activity_type: activityType, score: score ?? null }),
        });
        refreshModuleProgress();
    }

    async function refreshModuleProgress() {
        const res = await fetch('/api/assessment/stats');
        const data = await res.json();
        const bar = document.getElementById('module-progress-bar');
        const pct = document.getElementById('module-progress-pct');
        if (bar) bar.style.width = data.percentage + '%';
        if (pct) pct.textContent = data.percentage + '%';
    }

    // ── Flashcards ────────────────────────────────────────────────────────────
    async function loadFlashcards(count = 10, dueOnly = false) {
        const params = new URLSearchParams({ count: String(count) });
        if (dueOnly) params.set('due_only', 'true');
        const res = await fetch(`/api/assessment/flashcards?${params}`);
        const data = await res.json();
        flashcards = data.cards || [];
        fcIndex = 0;
        fcFlipped = false;
        hideFcDeckComplete();
        updateFcStatsDisplay(data.stats);
        showFlashcard();
        reportProgress(Math.min(flashcards.length, 1), 'flashcards');
    }

    function updateFcStatsDisplay(stats) {
        if (!stats) return;
        const due = document.getElementById('ha-fc-due');
        const mastered = document.getElementById('ha-fc-mastered');
        if (due) due.textContent = stats.due_today ?? 0;
        if (mastered) mastered.textContent = stats.mastered ?? 0;
    }

    function renderFcDots() {
        const dots = document.getElementById('ha-fc-dots');
        if (!dots) return;
        dots.innerHTML = flashcards.map((c, i) => {
            const cls = ['ha-fc-dot', i === fcIndex ? 'active' : ''].filter(Boolean).join(' ');
            return `<button type="button" class="${cls}" title="Card ${i + 1}" aria-label="Go to card ${i + 1}" onclick="Assessment.goToFlashcard(${i})"></button>`;
        }).join('');
    }

    function goToFlashcard(index) {
        if (index < 0 || index >= flashcards.length) return;
        fcIndex = index;
        showFlashcard();
    }

    function setFcRatingButtons(enabled) {
        document.getElementById('ha-fc-btn-review')?.toggleAttribute('disabled', !enabled);
        document.getElementById('ha-fc-btn-know')?.toggleAttribute('disabled', !enabled);
    }

    function showFlashcard() {
        if (!flashcards.length) {
            const stage = document.getElementById('ha-flashcard-stage');
            if (stage) stage.innerHTML = '<p class="text-ward-500 text-center py-8">No cards loaded.</p>';
            return;
        }
        const card = flashcards[fcIndex];
        const inner = document.getElementById('ha-flashcard-inner');
        if (inner) inner.classList.remove('flipped');
        fcFlipped = false;

        document.getElementById('ha-fc-front').textContent = card.front;
        const sysEl = document.getElementById('ha-fc-system');
        if (sysEl) {
            sysEl.textContent = card.system_name || card.system || '';
            sysEl.classList.toggle('red-flag', card.type === 'red_flag');
        }
        document.getElementById('ha-fc-back-normal').textContent = card.normal || '—';
        document.getElementById('ha-fc-back-abnormal').textContent = card.abnormal || '—';
        document.getElementById('ha-fc-back-action').textContent = card.abnormal_action || '—';
        document.getElementById('ha-fc-back-clinical').textContent = card.clinical_why || '';
        document.getElementById('ha-fc-front-view')?.classList.remove('hidden');
        document.getElementById('ha-fc-back-view')?.classList.add('hidden');
        document.getElementById('ha-fc-verify-btn')?.classList.add('hidden');
        document.getElementById('ha-flashcard-counter').textContent = `${fcIndex + 1} / ${flashcards.length}`;
        setFcRatingButtons(false);
        renderFcDots();
    }

    function flipFlashcard() {
        if (!flashcards.length) return;
        fcFlipped = !fcFlipped;
        document.getElementById('ha-flashcard-inner')?.classList.toggle('flipped', fcFlipped);
        document.getElementById('ha-fc-front-view')?.classList.toggle('hidden', fcFlipped);
        document.getElementById('ha-fc-back-view')?.classList.toggle('hidden', !fcFlipped);
        if (fcFlipped) {
            setFcRatingButtons(true);
            document.getElementById('ha-fc-verify-btn')?.classList.remove('hidden');
        }
    }

    async function rateFlashcard(rating) {
        const card = flashcards[fcIndex];
        if (!card) return;
        const quality = rating === 'know' ? 2 : 0;
        await fetch('/api/assessment/flashcards/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ card_id: card.id, quality }),
        });
        if (rating === 'review') {
            fcSessionReview++;
            const rev = document.getElementById('ha-fc-review');
            if (rev) rev.textContent = fcSessionReview;
        }
        refreshModuleProgress();
        if (fcIndex < flashcards.length - 1) {
            fcIndex++;
            showFlashcard();
        } else {
            setFcRatingButtons(false);
            showFcDeckComplete();
        }
    }

    function showFcDeckComplete() {
        const el = document.getElementById('ha-fc-complete');
        const stage = document.getElementById('ha-flashcard-stage');
        if (!el) return;
        el.classList.remove('hidden');
        if (stage) stage.classList.add('hidden');
        el.innerHTML = `
            <div class="text-center py-4">
                <p class="text-ward-success font-semibold mb-2">Deck complete!</p>
                <p class="text-sm text-ward-400 mb-4">Rated ${flashcards.length} cards this session.</p>
                <div class="flex flex-wrap justify-center gap-2">
                    <button type="button" class="btn-primary text-sm" onclick="Assessment.loadFlashcards(10, true)">Study Due Cards</button>
                    <button type="button" class="btn-secondary text-sm" onclick="Assessment.exportFlashcardDeck()">Export Deck</button>
                </div>
            </div>`;
    }

    function hideFcDeckComplete() {
        document.getElementById('ha-fc-complete')?.classList.add('hidden');
        document.getElementById('ha-flashcard-stage')?.classList.remove('hidden');
    }

    async function exportFlashcardDeck() {
        const res = await fetch('/api/assessment/export/flashcards');
        const data = await res.json();
        if (data.content && typeof WardExport !== 'undefined') {
            WardExport.downloadText('ward-assessment-flashcards.md', data.content, 'text/markdown;charset=utf-8');
            if (typeof showToast === 'function') showToast('Deck exported as Markdown.');
        }
    }

    async function openPrintableExport(url, title) {
        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error('fetch failed');
            const html = await res.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const body = doc.body.innerHTML;
            const meta = doc.querySelector('.meta')?.textContent || 'NURS 146 Health Assessment';
            WardExport.openPrintableHtml(title, body, meta);
            fetch('/api/assessment/progress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items_studied: 1, activity_type: 'export' }),
            }).catch(() => {});
        } catch {
            if (typeof showToast === 'function') showToast('Export failed. Is the server running?', 'error');
        }
    }

    function exportHeadToToeSheet() {
        openPrintableExport('/api/assessment/export/head-to-toe', 'Head-to-Toe Sequence Sheet');
    }

    function exportRedFlagsSheet() {
        openPrintableExport('/api/assessment/export/red-flags', 'Red Flag Quick Reference');
    }

    function exportChecklistsPack() {
        openPrintableExport('/api/assessment/export/checklist', 'Assessment Checklists Pack');
    }

    function copyHeadToToeClipboard() {
        WardExport.copyExportText(
            '/api/assessment/export/head-to-toe',
            'Head-to-toe sequence copied to clipboard',
        );
    }

    function copyRedFlagsClipboard() {
        WardExport.copyExportText(
            '/api/assessment/export/red-flags',
            'Red flags reference copied to clipboard',
        );
    }

    function prevFlashcard() {
        if (fcIndex > 0) { fcIndex--; showFlashcard(); }
    }

    function nextFlashcard() {
        if (fcIndex < flashcards.length - 1) { fcIndex++; showFlashcard(); }
    }

    // ── Init ──────────────────────────────────────────────────────────────────
    function init() {
        WardTabs.register('/modules/assessment', { validTabs: VALID_TABS, defaultTab: DEFAULT_TAB, switchTab });
        WardTabs.init('/modules/assessment');
        loadHeadToToe();
        document.addEventListener('keydown', (e) => {
            const fcTab = document.getElementById('tab-flashcards');
            if (!fcTab || fcTab.classList.contains('hidden')) return;
            if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
            if (e.code === 'Space') { e.preventDefault(); flipFlashcard(); }
            if (e.code === 'ArrowRight') nextFlashcard();
            if (e.code === 'ArrowLeft') prevFlashcard();
        });
    }

    return {
        switchTab,
        selectStep,
        selectSystem,
        switchSkillTab,
        setPracticeMode,
        startPractice,
        answerPractice,
        nextPracticeQuestion,
        loadChecklists,
        selectChecklist,
        toggleChecklistItem,
        resetChecklist,
        loadAssessNextScenarios,
        answerAssessNext,
        nextAssessNext,
        loadRedFlagDrill,
        answerRedFlagDrill,
        nextRedFlagDrill,
        loadSoapList,
        selectSoapExercise,
        revealSoapModel,
        switchDocTab,
        loadDocSoapList,
        selectDocSoapExercise,
        submitSoapValidate,
        loadSbarList,
        selectSbarExercise,
        revealSbarModel,
        loadFlashcards,
        flipFlashcard,
        rateFlashcard,
        goToFlashcard,
        prevFlashcard,
        nextFlashcard,
        exportFlashcardDeck,
        exportHeadToToeSheet,
        exportRedFlagsSheet,
        exportChecklistsPack,
        copyHeadToToeClipboard,
        copyRedFlagsClipboard,
        loadSpecialPopulations,
        selectPopulation,
        init,
    };
})();

document.addEventListener('DOMContentLoaded', () => Assessment.init());