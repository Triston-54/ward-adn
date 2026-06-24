/**
 * The Ward — Microbiology Module
 */
const Microbiology = (() => {
    const MODULE_ID = 'microbiology';

    const LINK_NAMES = {
        agent: 'Infectious Agent',
        reservoir: 'Reservoir',
        exit: 'Portal of Exit',
        transmission: 'Mode of Transmission',
        entry: 'Portal of Entry',
        host: 'Susceptible Host',
    };

    let chainData = { links: [], interventions: {} };
    let selectedLinkId = null;
    let brokenLinks = new Set();

    let breakChainScenarios = [];
    let breakChainIndex = 0;
    let breakChainCorrect = 0;

    let whatIfScenarios = [];
    let whatIfIndex = 0;
    let whatIfCorrect = 0;

    let practiceQuestions = [];
    let practiceIndex = 0;
    let practiceCorrect = 0;
    let practiceMode = 'mixed';

    let learnData = null;
    let learnSubtab = 'concepts';
    let breakPoints = [];

    let flashcards = [];
    let cardIndex = 0;
    let cardFlipped = false;
    const FC_RATINGS_KEY = 'ward_micro_flashcard_ratings';
    let fcRatings = loadFcRatings();

    // ── Tabs ──────────────────────────────────────────────────────────────────
    function switchTab(tab) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.querySelectorAll('.micro-tab-btn').forEach(b => b.classList.remove('active'));
        const panel = document.getElementById('tab-' + tab);
        const btn = document.querySelector(`[data-tab="${tab}"]`);
        if (panel) panel.classList.remove('hidden');
        if (btn) btn.classList.add('active');

        if (tab === 'chain' && !chainData.links.length) loadChainBuilder();
        if (tab === 'learn' && !learnData) loadLearnContent();
        if (tab === 'break-chain' && !breakChainScenarios.length) loadBreakChainScenarios();
        if (tab === 'what-if' && !whatIfScenarios.length) loadWhatIfScenarios();
        if (tab === 'flashcards' && !flashcards.length) loadFlashcards(8);
        if (tab === 'export') ensureLearnData();

        history.replaceState(null, '', location.pathname + (tab !== 'chain' ? '#' + tab : ''));
        window.WardSocratic?.setModuleContext({ module: 'microbiology', tab, subject: `Microbiology · ${tab}`, topic: 'pathophysiology' });
    }

    const VALID_TABS = ['chain', 'learn', 'break-chain', 'what-if', 'flashcards', 'practice', 'export'];
    const DEFAULT_TAB = 'chain';

    async function ensureLearnData() {
        if (!learnData) await loadLearnContent();
    }

    // ── Chain Builder ─────────────────────────────────────────────────────────
    function getChainInterventionsEl() {
        const area = document.getElementById('chain-builder-area');
        let el = document.getElementById('chain-interventions');
        if (!el && area) {
            el = document.createElement('div');
            el.id = 'chain-interventions';
            area.appendChild(el);
        }
        return el;
    }

    function setChainLoadingState() {
        const flow = document.getElementById('chain-flow');
        const interventions = getChainInterventionsEl();
        if (flow) flow.innerHTML = '<p class="text-ward-500 text-sm">Loading infection chain…</p>';
        if (interventions) interventions.innerHTML = '<p class="text-ward-500 text-sm">Loading intervention options…</p>';
    }

    function showChainLoadError(message) {
        const flow = document.getElementById('chain-flow');
        const interventions = getChainInterventionsEl();
        const text = message || 'Failed to load infection chain. Refresh to try again.';
        if (flow) flow.innerHTML = `<p class="text-ward-danger text-sm">${text}</p>`;
        if (interventions) interventions.innerHTML = '';
    }

    async function loadInfectionChainData() {
        if (window.WardData?.Microbiology?.infectionChain) {
            try {
                const data = await WardData.Microbiology.infectionChain();
                if (data?.links?.length) return data;
            } catch (err) {
                console.warn('[Microbiology] WardData infection chain failed, trying fetch:', err);
            }
        }

        const res = await fetch('/api/microbiology/infection-chain');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data?.error) throw new Error(data.error);
        return data;
    }

    async function loadChainBuilder() {
        setChainLoadingState();

        try {
            const data = await loadInfectionChainData();
            chainData = {
                links: data.links || [],
                interventions: data.interventions || {},
            };
            renderChainFlow();
            if (chainData.links.length) {
                selectChainLink(chainData.links[0].id);
            } else {
                showChainLoadError('No infection chain data available.');
            }
        } catch (err) {
            console.error('[Microbiology] Failed to load infection chain:', err);
            showChainLoadError();
        }
    }

    function renderChainFlow() {
        const flow = document.getElementById('chain-flow');
        if (!flow) return;

        flow.innerHTML = chainData.links.map((link, i) => {
            const arrow = i < chainData.links.length - 1
                ? '<span class="chain-arrow hidden sm:inline">→</span>'
                : '';
            const broken = brokenLinks.has(link.id) ? ' broken' : '';
            const active = selectedLinkId === link.id ? ' active' : '';
            return `
                <button type="button" class="chain-link-btn${active}${broken}"
                        onclick="Microbiology.selectChainLink('${link.id}')"
                        data-link="${link.id}">
                    ${link.name}
                </button>${arrow}`;
        }).join('');
    }

    function selectChainLink(linkId) {
        selectedLinkId = linkId;
        renderChainFlow();
        renderLinkDetail();
        renderInterventions();
        document.getElementById('chain-feedback')?.classList.add('hidden');
        const link = chainData.links.find(l => l.id === linkId);
        if (link) {
            window.WardSocratic?.setModuleContext({
                module: 'microbiology',
                tab: 'chain',
                subject: `Chain of Infection · ${link.name}`,
                snippet: link.description || '',
                topic: 'pathophysiology',
            });
        }
    }

    function renderLinkDetail() {
        const el = document.getElementById('chain-link-detail');
        if (!el) return;
        const link = chainData.links.find(l => l.id === selectedLinkId);
        if (!link) {
            el.innerHTML = '';
            return;
        }
        const src = link.source ? `<button onclick='showSource(${JSON.stringify(link.source)})' class="btn-verify text-xs mt-2">Verify Source</button>` : '';
        el.innerHTML = `
            <h3>${link.name}</h3>
            <p>${link.description}</p>
            <p class="text-xs text-ward-success mt-2"><strong>Break it:</strong> ${link.intervention}</p>
            ${src}
        `;
    }

    function renderInterventions() {
        const el = getChainInterventionsEl();
        if (!el) return;
        const options = chainData.interventions[selectedLinkId] || [];
        if (!options.length) {
            el.innerHTML = '<p class="text-ward-500 text-sm">Select a chain link above.</p>';
            return;
        }
        el.innerHTML = `
            <p class="text-xs text-ward-500 mb-3">Which intervention best breaks the <strong class="text-ward-300">${getLinkName(selectedLinkId)}</strong> link?</p>
            <div class="intervention-grid">
                ${options.map(opt => `
                    <button type="button" class="intervention-btn" data-id="${opt.id}"
                            onclick="Microbiology.submitChainBreak('${opt.id}')">
                        ${opt.label}
                    </button>
                `).join('')}
            </div>
        `;
    }

    function getLinkName(linkId) {
        return chainData.links.find(l => l.id === linkId)?.name || LINK_NAMES[linkId] || linkId;
    }

    async function evaluateChainBreak(linkId, interventionId) {
        if (window.WardData?.Microbiology?.evaluateChainBreak) {
            try {
                return await WardData.Microbiology.evaluateChainBreak(linkId, interventionId);
            } catch (err) {
                console.warn('[Microbiology] WardData chain-break failed, trying fetch:', err);
            }
        }

        const res = await fetch('/api/microbiology/chain-break', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ link_id: linkId, intervention_id: interventionId }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data?.error) throw new Error(data.error);
        return data;
    }

    async function submitChainBreak(interventionId) {
        if (!selectedLinkId) return;

        let data;
        try {
            data = await evaluateChainBreak(selectedLinkId, interventionId);
        } catch (err) {
            console.error('[Microbiology] Chain break evaluation failed:', err);
            const feedback = document.getElementById('chain-feedback');
            if (feedback) {
                feedback.classList.remove('hidden');
                feedback.innerHTML = '<p class="text-ward-danger text-sm">Could not check that answer. Refresh and try again.</p>';
            }
            return;
        }

        document.querySelectorAll('#chain-interventions .intervention-btn').forEach(btn => {
            btn.disabled = true;
            if (btn.dataset.id === interventionId) {
                btn.classList.add(data.correct ? 'correct' : 'incorrect');
            }
        });

        const feedback = document.getElementById('chain-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${data.correct ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${data.correct ? 'text-ward-success' : 'text-ward-danger'}">
                        ${data.correct ? '✓ Chain link broken!' : '✗ Not the best match'}
                    </p>
                    <p class="text-ward-300 mt-1">${data.feedback}</p>
                    ${data.clinical_why ? `<p class="text-xs text-ward-accent mt-2">${data.clinical_why}</p>` : ''}
                </div>
                <button onclick="Microbiology.nextChainChallenge()" class="btn-primary w-full mt-3 text-sm">Try Another Link</button>
            `;
        }

        if (data.correct) {
            brokenLinks.add(selectedLinkId);
            renderChainFlow();
            reportProgress(1, 'chain_builder');

            if (brokenLinks.size >= chainData.links.length) {
                showChainCompletion();
                return;
            }
        }
    }

    function showChainCompletion() {
        const feedback = document.getElementById('chain-feedback');
        const completion = document.getElementById('chain-completion');
        if (feedback) feedback.classList.add('hidden');

        if (completion) {
            completion.classList.remove('hidden');
            completion.innerHTML = `
                <div class="chain-completion-card">
                    <div class="chain-completion-icon">🛡️</div>
                    <h3 class="text-lg font-bold text-ward-success mb-1">Chain Broken!</h3>
                    <p class="text-sm text-ward-300 mb-1">You correctly addressed all 6 links in the chain of infection.</p>
                    <p class="text-xs text-ward-500 mb-4">Hand hygiene, PPE, isolation, vaccination, and environmental cleaning — every link matters in clinical practice.</p>
                    <div class="flex flex-wrap gap-2">
                        <button onclick="Microbiology.resetChainBuilder()" class="btn-primary text-sm flex-1">Practice Again</button>
                        <button onclick="Microbiology.switchTab('learn')" class="btn-secondary text-sm flex-1">Review Learn Tab</button>
                    </div>
                </div>`;
        }

        reportProgress(chainData.links.length, 'chain_complete', 100);
    }

    function hideChainCompletion() {
        document.getElementById('chain-completion')?.classList.add('hidden');
    }

    function nextChainChallenge() {
        hideChainCompletion();
        const unbroken = chainData.links.filter(l => !brokenLinks.has(l.id));
        if (!unbroken.length) return;
        const next = unbroken[Math.floor(Math.random() * unbroken.length)];
        document.getElementById('chain-feedback')?.classList.add('hidden');
        selectChainLink(next.id);
    }

    function resetChainBuilder() {
        brokenLinks.clear();
        hideChainCompletion();
        document.getElementById('chain-feedback')?.classList.add('hidden');
        if (chainData.links.length) selectChainLink(chainData.links[0].id);
        else loadChainBuilder();
    }

    // ── Learn / Reference ─────────────────────────────────────────────────────
    async function loadLearnContent() {
        const area = document.getElementById('learn-content');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm py-4">Loading reference content…</p>';

        const [conceptsRes, classRes, pathRes, gramRes, clinicalRes, breakRes] = await Promise.all([
            fetch('/api/microbiology/concepts'),
            fetch('/api/microbiology/classification'),
            fetch('/api/microbiology/pathogens'),
            fetch('/api/microbiology/gram-stain'),
            fetch('/api/microbiology/clinical'),
            fetch('/api/microbiology/break-points'),
        ]);

        learnData = {
            concepts: (await conceptsRes.json()).concepts,
            classification: (await classRes.json()).types,
            pathogens: (await pathRes.json()).pathogens,
            gramStain: await gramRes.json(),
            clinical: await clinicalRes.json(),
        };
        breakPoints = (await breakRes.json()).break_points || [];
        renderBreakPoints();
        renderLearnSubtab();
    }

    function renderBreakPoints() {
        const callout = document.getElementById('break-points-callout');
        const list = document.getElementById('break-points-list');
        if (!callout || !list || !breakPoints.length) return;
        callout.classList.remove('hidden');
        list.innerHTML = breakPoints.map(bp => `<li>${bp}</li>`).join('');
    }

    function switchLearnSubtab(subtab) {
        learnSubtab = subtab;
        document.querySelectorAll('.learn-subtab').forEach(b => {
            b.classList.toggle('active', b.dataset.learn === subtab);
        });
        renderLearnSubtab();
    }

    function renderLearnSubtab() {
        const area = document.getElementById('learn-content');
        if (!area || !learnData) return;

        switch (learnSubtab) {
            case 'concepts': area.innerHTML = renderConcepts(); break;
            case 'pathogens': area.innerHTML = renderPathogens(); break;
            case 'classification': area.innerHTML = renderClassification(); break;
            case 'gram': area.innerHTML = renderGramStain(); break;
            case 'clinical': area.innerHTML = renderClinical(); break;
        }
    }

    function renderConcepts() {
        return `<div class="grid sm:grid-cols-2 gap-4">
            ${learnData.concepts.map(c => {
                const src = c.source ? `<button onclick='showSource(${JSON.stringify(c.source)})' class="btn-verify text-xs mt-2">Verify</button>` : '';
                return `
                    <div class="micro-ref-card p-5">
                        <h3 class="font-semibold text-ward-success mb-2">${c.title}</h3>
                        <p class="text-sm text-ward-300">${c.content}</p>
                        ${c.clinical_relevance ? `<p class="text-xs text-ward-warning mt-3"><strong>Clinical:</strong> ${c.clinical_relevance}</p>` : ''}
                        ${src}
                    </div>`;
            }).join('')}
        </div>`;
    }

    function renderPathogens() {
        return `<div class="space-y-2 max-h-[65vh] overflow-y-auto">
            ${learnData.pathogens.map((p, i) => `
                <div class="micro-ref-card" onclick="Microbiology.toggleRefCard(${i}, 'pathogen')">
                    <div class="flex justify-between items-start gap-2">
                        <div>
                            <span class="font-mono font-semibold text-ward-success">${p.name}</span>
                            <span class="pathogen-badge ml-2">${p.type}</span>
                        </div>
                        <span class="pathogen-precaution">${p.precautions}</span>
                    </div>
                    <div id="pathogen-detail-${i}" class="hidden mt-3 pt-3 border-t border-ward-800 text-sm">
                        <p class="text-ward-400">${p.full_name}</p>
                        <p class="text-ward-500 mt-2"><strong>Transmission:</strong> ${p.transmission}</p>
                        <p class="text-ward-300 mt-1"><strong>Nursing action:</strong> ${p.nursing_action}</p>
                        <p class="text-xs text-ward-accent mt-2">${p.clinical_why}</p>
                        ${p.source ? `<button onclick='event.stopPropagation();showSource(${JSON.stringify(p.source)})' class="btn-verify text-xs mt-2">Verify</button>` : ''}
                    </div>
                </div>
            `).join('')}
        </div>`;
    }

    function formatClassificationExamples(examples) {
        if (Array.isArray(examples)) return examples.join(', ');
        return examples || '—';
    }

    function renderClassification() {
        return `<div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            ${learnData.classification.map(t => {
                const structure = t.structure || t.cell_type || '';
                const treatment = t.treatment || t.notes || '';
                const examples = formatClassificationExamples(t.examples);
                const clinicalWhy = t.clinical_why || '';
                return `
                <div class="classification-card">
                    <div class="classification-icon">${t.icon || '🦠'}</div>
                    <div class="classification-type">${t.type}</div>
                    ${structure ? `<p class="text-xs text-ward-500 mt-2">${structure}</p>` : ''}
                    ${treatment ? `<p class="text-xs text-ward-400 mt-2"><strong>Treatment:</strong> ${treatment}</p>` : ''}
                    <p class="text-xs text-ward-500 mt-1"><strong>Examples:</strong> ${examples}</p>
                    ${clinicalWhy ? `<p class="text-xs text-ward-accent mt-2">${clinicalWhy}</p>` : ''}
                </div>`;
            }).join('')}
        </div>`;
    }

    function formatListField(value) {
        if (Array.isArray(value)) return value.join(', ');
        return value || '';
    }

    function normalizeBreakChainOptions(scenario) {
        const opts = scenario.options || [];
        return opts.map((opt, i) => {
            if (typeof opt === 'string') {
                return {
                    text: opt,
                    correct: i === (scenario.correct_index ?? -1),
                    explanation: scenario.explanation || '',
                };
            }
            return {
                text: opt.text || opt.label || String(opt),
                correct: !!opt.correct || i === (scenario.correct_index ?? -1),
                explanation: opt.explanation || scenario.explanation || '',
            };
        });
    }

    function renderGramStain() {
        const gs = learnData.gramStain;
        const pos = gs.interpretation?.gram_positive || {};
        const neg = gs.interpretation?.gram_negative || {};
        const note = gs.interpretation?.clinical_note || gs.clinical_note || '';
        return `
            <div class="grid lg:grid-cols-2 gap-5">
                <div class="card p-5">
                    <h3 class="text-sm font-semibold text-ward-100 mb-3">Procedure</h3>
                    <ol class="gram-stain-steps">
                        ${(gs.procedure || []).map(step => `<li>${step}</li>`).join('')}
                    </ol>
                </div>
                <div class="gram-compare">
                    <div class="card p-4 gram-positive">
                        <h4 class="text-sm font-semibold text-purple-300 mb-2">Gram-Positive</h4>
                        <p class="text-xs text-ward-400"><strong>Appearance:</strong> ${pos.appearance || ''}</p>
                        <p class="text-xs text-ward-400 mt-1"><strong>Cell wall:</strong> ${pos.cell_wall || ''}</p>
                        <p class="text-xs text-ward-500 mt-2"><strong>Examples:</strong> ${formatListField(pos.examples)}</p>
                        ${pos.antibiotics ? `<p class="text-xs text-ward-accent mt-2"><strong>Empiric therapy:</strong> ${pos.antibiotics}</p>` : ''}
                    </div>
                    <div class="card p-4 gram-negative">
                        <h4 class="text-sm font-semibold text-pink-300 mb-2">Gram-Negative</h4>
                        <p class="text-xs text-ward-400"><strong>Appearance:</strong> ${neg.appearance || ''}</p>
                        <p class="text-xs text-ward-400 mt-1"><strong>Cell wall:</strong> ${neg.cell_wall || ''}</p>
                        <p class="text-xs text-ward-500 mt-2"><strong>Examples:</strong> ${formatListField(neg.examples)}</p>
                        ${neg.antibiotics ? `<p class="text-xs text-ward-accent mt-2"><strong>Empiric therapy:</strong> ${neg.antibiotics}</p>` : ''}
                    </div>
                </div>
            </div>
            ${note ? `<p class="text-xs text-ward-accent mt-3 italic">${note}</p>` : ''}`;
    }

    function renderClinical() {
        const c = learnData.clinical;
        const hh = c.hand_hygiene || {};
        const ppe = c.ppe || c.ppe_guide || {};
        const when = hh.when || hh.who_five_moments || [];
        const soapWater = hh.soap_and_water || hh.soap_and_water_required || [];
        const alcoholGel = hh.alcohol_gel
            || (hh.alcohol_rub ? [hh.alcohol_rub] : []);
        const hhWhy = hh.clinical_why || hh.nursing_priority || '';
        const ppeWhy = ppe.clinical_why || ppe.sequence || '';
        return `
            <div class="grid lg:grid-cols-2 gap-5">
                <div class="card p-5">
                    <h3 class="text-sm font-semibold text-ward-100 mb-3">Hand Hygiene — WHO 5 Moments</h3>
                    <ul class="text-sm text-ward-300 space-y-1 list-disc list-inside">
                        ${when.map(w => `<li>${w}</li>`).join('')}
                    </ul>
                    <div class="mt-4 grid sm:grid-cols-2 gap-3">
                        <div class="p-3 bg-ward-900 rounded-lg">
                            <div class="text-xs font-semibold text-ward-success mb-1">Soap &amp; Water</div>
                            <ul class="text-xs text-ward-500 space-y-0.5">
                                ${soapWater.map(s => `<li>• ${s}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="p-3 bg-ward-900 rounded-lg">
                            <div class="text-xs font-semibold text-ward-accent mb-1">Alcohol Gel</div>
                            <ul class="text-xs text-ward-500 space-y-0.5">
                                ${alcoholGel.map(s => `<li>• ${s}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                    ${hhWhy ? `<p class="text-xs text-ward-accent mt-3">${hhWhy}</p>` : ''}
                </div>
                <div class="card p-5">
                    <h3 class="text-sm font-semibold text-ward-100 mb-3">PPE Guide</h3>
                    <dl class="ppe-list">
                        <dt>Gloves</dt><dd>${ppe.gloves || ''}</dd>
                        <dt>Gown</dt><dd>${ppe.gown || ''}</dd>
                        <dt>Surgical Mask</dt><dd>${ppe.mask_surgical || ppe.mask || ''}</dd>
                        <dt>N95 Respirator</dt><dd>${ppe.n95 || ''}</dd>
                        <dt>Eye Protection</dt><dd>${ppe.eye_protection || ''}</dd>
                    </dl>
                    ${ppeWhy ? `<p class="text-xs text-ward-accent mt-3">${ppeWhy}</p>` : ''}
                </div>
            </div>
            <div class="mt-5">
                <h3 class="text-sm font-semibold text-ward-100 mb-3">Healthcare-Associated Infections (HAIs)</h3>
                <div class="hai-grid">
                    ${(c.hai_types || []).map(h => `
                        <div class="hai-card">
                            <div class="hai-abbrev">${h.abbrev || h.id || h.name}</div>
                            <div class="text-xs text-ward-400 mt-1">${h.name}</div>
                            ${h.definition ? `<p class="text-xs text-ward-500 mt-1">${h.definition}</p>` : ''}
                            <p class="text-xs text-ward-500 mt-2"><strong>Bundle:</strong> ${formatListField(h.bundle)}</p>
                            ${h.clinical_why ? `<p class="text-xs text-ward-accent mt-1">${h.clinical_why}</p>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>`;
    }

    function toggleRefCard(index, type) {
        const el = document.getElementById(`${type}-detail-${index}`);
        if (el) el.classList.toggle('hidden');
    }

    // ── Break-Chain Scenarios ─────────────────────────────────────────────────
    async function loadBreakChainScenarios() {
        const area = document.getElementById('break-chain-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading scenarios…</p>';

        const res = await fetch('/api/microbiology/scenarios/break-chain?count=4');
        const data = await res.json();
        breakChainScenarios = data.scenarios;
        breakChainIndex = 0;
        breakChainCorrect = 0;
        showBreakChainScenario();
    }

    function showBreakChainScenario() {
        const area = document.getElementById('break-chain-area');
        const scoreEl = document.getElementById('break-chain-score');
        if (!area) return;

        if (breakChainIndex >= breakChainScenarios.length) {
            const pct = breakChainScenarios.length
                ? Math.round((breakChainCorrect / breakChainScenarios.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-ward-success mb-2">${breakChainCorrect}/${breakChainScenarios.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">Review the chain builder and learn tabs for missed concepts.</p>
                    <button onclick="Microbiology.loadBreakChainScenarios()" class="btn-primary mt-4 text-sm">New Scenarios</button>
                </div>`;
            if (scoreEl) scoreEl.textContent = `Final: ${breakChainCorrect}/${breakChainScenarios.length}`;
            reportProgress(breakChainCorrect, 'scenarios', pct);
            return;
        }

        const s = breakChainScenarios[breakChainIndex];
        const bcOptions = normalizeBreakChainOptions(s);
        if (scoreEl) scoreEl.textContent = `${breakChainCorrect}/${breakChainIndex}`;

        const linkLabel = getLinkName(s.target_link) || s.target_link;
        area.innerHTML = `
            <div class="scenario-card">
                <div class="scenario-title">${s.title}</div>
                <span class="scenario-target">Target link: ${linkLabel}</span>
                <p class="scenario-setup">${s.scenario}</p>
                <div class="space-y-2" id="bc-options">
                    ${bcOptions.map((opt, i) => `
                        <button type="button" class="practice-option" onclick="Microbiology.answerBreakChain(${i})">
                            <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${opt.text}
                        </button>
                    `).join('')}
                </div>
                <div id="bc-feedback" class="mt-4 hidden"></div>
            </div>
            <p class="text-center text-xs text-ward-600 mt-3">Scenario ${breakChainIndex + 1} of ${breakChainScenarios.length}</p>
        `;
    }

    function answerBreakChain(selected) {
        const s = breakChainScenarios[breakChainIndex];
        const bcOptions = normalizeBreakChainOptions(s);
        const opt = bcOptions[selected];
        const isCorrect = opt.correct;

        if (isCorrect) breakChainCorrect++;

        document.querySelectorAll('#bc-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (bcOptions[i].correct) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('bc-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            const src = s.source ? `<button onclick='showSource(${JSON.stringify(s.source)})' class="btn-verify text-xs mt-2">Verify Source</button>` : '';
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${isCorrect ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${isCorrect ? 'text-ward-success' : 'text-ward-danger'}">${isCorrect ? 'Correct!' : 'Incorrect.'}</p>
                    <p class="text-ward-300 mt-1">${opt.explanation}</p>
                    ${s.clinical_why ? `<p class="text-xs text-ward-accent mt-2">${s.clinical_why}</p>` : ''}
                    ${src}
                </div>
                <button onclick="Microbiology.nextBreakChain()" class="btn-primary w-full mt-3 text-sm">Next Scenario</button>
            `;
        }
    }

    function nextBreakChain() {
        breakChainIndex++;
        showBreakChainScenario();
    }

    // ── What-If Scenarios ─────────────────────────────────────────────────────
    async function loadWhatIfScenarios() {
        const area = document.getElementById('what-if-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading what-if scenarios…</p>';

        const res = await fetch('/api/microbiology/scenarios/what-if?count=3');
        const data = await res.json();
        whatIfScenarios = data.scenarios;
        whatIfIndex = 0;
        whatIfCorrect = 0;
        showWhatIfScenario();
    }

    function showWhatIfScenario() {
        const area = document.getElementById('what-if-area');
        const scoreEl = document.getElementById('what-if-score');
        if (!area) return;

        if (whatIfIndex >= whatIfScenarios.length) {
            const pct = whatIfScenarios.length
                ? Math.round((whatIfCorrect / whatIfScenarios.length) * 100)
                : 0;
            area.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl font-bold text-ward-success mb-2">${whatIfCorrect}/${whatIfScenarios.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">What-if scenarios build clinical judgment for infection control.</p>
                    <button onclick="Microbiology.loadWhatIfScenarios()" class="btn-primary mt-4 text-sm">New Scenarios</button>
                </div>`;
            if (scoreEl) scoreEl.textContent = `Final: ${whatIfCorrect}/${whatIfScenarios.length}`;
            reportProgress(whatIfCorrect, 'what_if', pct);
            return;
        }

        const s = whatIfScenarios[whatIfIndex];
        if (scoreEl) scoreEl.textContent = `${whatIfCorrect}/${whatIfIndex}`;

        area.innerHTML = `
            <div class="scenario-card">
                <div class="scenario-title">${s.title}</div>
                <p class="scenario-setup">${s.setup || s.scenario || ''}</p>
                <p class="text-sm font-medium text-ward-200 mb-3">${s.question}</p>
                <div class="space-y-2" id="wi-options">
                    ${s.options.map((opt, i) => `
                        <button type="button" class="practice-option" onclick="Microbiology.answerWhatIf(${i}, ${s.correct_index})">
                            <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${opt}
                        </button>
                    `).join('')}
                </div>
                <div id="wi-feedback" class="mt-4 hidden"></div>
            </div>
            <p class="text-center text-xs text-ward-600 mt-3">Scenario ${whatIfIndex + 1} of ${whatIfScenarios.length}</p>
        `;
    }

    function answerWhatIf(selected, correct) {
        const s = whatIfScenarios[whatIfIndex];
        const isCorrect = selected === correct;
        if (isCorrect) whatIfCorrect++;

        document.querySelectorAll('#wi-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (i === correct) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('wi-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            const src = s.source ? `<button onclick='showSource(${JSON.stringify(s.source)})' class="btn-verify text-xs mt-2">Verify Source</button>` : '';
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${isCorrect ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${isCorrect ? 'text-ward-success' : 'text-ward-danger'}">${isCorrect ? 'Correct!' : 'Incorrect.'}</p>
                    <p class="text-ward-300 mt-1">${s.explanation}</p>
                    ${s.clinical_why ? `<p class="text-xs text-ward-accent mt-2">${s.clinical_why}</p>` : ''}
                    ${src}
                </div>
                <button onclick="Microbiology.nextWhatIf()" class="btn-primary w-full mt-3 text-sm">Next Scenario</button>
            `;
        }
    }

    function nextWhatIf() {
        whatIfIndex++;
        showWhatIfScenario();
    }

    // ── Practice ──────────────────────────────────────────────────────────────
    function setPracticeMode(mode) {
        practiceMode = mode;
        document.querySelectorAll('.mode-pill').forEach(p => {
            p.classList.toggle('active', p.dataset.mode === mode);
        });
    }

    async function startPractice(count) {
        const area = document.getElementById('practice-question-area');
        if (area) area.innerHTML = '<p class="text-ward-500 text-sm">Loading questions…</p>';

        const res = await fetch(`/api/microbiology/practice?count=${count}&mode=${practiceMode}`);
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
                    <div class="text-4xl font-bold text-ward-success mb-2">${practiceCorrect}/${practiceQuestions.length}</div>
                    <p class="text-ward-400 mb-1">${pct}% correct</p>
                    <p class="text-sm text-ward-500">${pct >= 80 ? 'Strong infection control knowledge!' : 'Review concepts and try break-chain scenarios.'}</p>
                </div>`;
            if (scoreEl) scoreEl.textContent = `Final: ${practiceCorrect}/${practiceQuestions.length}`;
            reportProgress(practiceCorrect, 'practice', pct);
            return;
        }

        const q = practiceQuestions[practiceIndex];
        if (scoreEl) scoreEl.textContent = `${practiceCorrect}/${practiceIndex}`;

        const typeLabel = q.type === 'application' ? 'Application' : 'NCLEX-Style';
        const cat = q.nclex_category ? `<span class="text-xs text-ward-600 ml-2">${q.nclex_category}</span>` : '';

        area.innerHTML = `
            <div class="mb-2 text-xs text-ward-success uppercase tracking-wide">${typeLabel}${cat}</div>
            <p class="text-ward-100 mb-4">${q.question}</p>
            <div class="space-y-2" id="practice-options">
                ${q.options.map((opt, i) => `
                    <button type="button" class="practice-option" onclick="Microbiology.answerPractice(${i}, ${q.correct_index})">
                        <span class="text-ward-500 mr-2">${String.fromCharCode(65 + i)}.</span>${opt}
                    </button>
                `).join('')}
            </div>
            <div id="practice-feedback" class="mt-4 hidden"></div>
        `;
    }

    function answerPractice(selected, correct) {
        const q = practiceQuestions[practiceIndex];
        const isCorrect = selected === correct;
        if (isCorrect) practiceCorrect++;

        document.querySelectorAll('#practice-options .practice-option').forEach((btn, i) => {
            btn.disabled = true;
            if (i === correct) btn.classList.add('correct');
            else if (i === selected) btn.classList.add('incorrect');
        });

        const feedback = document.getElementById('practice-feedback');
        if (feedback) {
            feedback.classList.remove('hidden');
            const src = q.source ? `<button onclick='showSource(${JSON.stringify(q.source)})' class="btn-verify text-xs mt-2">Verify Source</button>` : '';
            feedback.innerHTML = `
                <div class="p-3 rounded-lg text-sm ${isCorrect ? 'bg-ward-success/10 border border-ward-success/30' : 'bg-ward-danger/10 border border-ward-danger/30'}">
                    <p class="font-medium ${isCorrect ? 'text-ward-success' : 'text-ward-danger'}">${isCorrect ? 'Correct!' : 'Incorrect.'}</p>
                    <p class="text-ward-300 mt-1">${q.explanation}</p>
                    ${src}
                </div>
                <button onclick="Microbiology.nextPracticeQuestion()" class="btn-primary w-full mt-3 text-sm">Next Question</button>
            `;
        }
    }

    function nextPracticeQuestion() {
        practiceIndex++;
        showPracticeQuestion();
    }

    // ── Flashcards ────────────────────────────────────────────────────────────
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
        const knownEl = document.getElementById('micro-fc-known');
        const reviewEl = document.getElementById('micro-fc-review');
        if (knownEl) knownEl.textContent = known;
        if (reviewEl) reviewEl.textContent = review;
    }

    async function loadFlashcards(count, shuffle = false) {
        const stage = document.getElementById('micro-flashcard-stage');
        const frontEl = document.getElementById('mfc-front');
        if (frontEl) frontEl.textContent = 'Loading…';

        try {
            const url = count
                ? `/api/microbiology/flashcards?count=${count}`
                : '/api/microbiology/flashcards';
            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            flashcards = data.cards || [];
            if (!flashcards.length && window.WardData?.Microbiology?.flashcards) {
                const fb = await WardData.Microbiology.flashcards(count ?? null);
                flashcards = fb.cards || [];
            }
        } catch (err) {
            console.error('[Microbiology] flashcard load failed:', err);
            if (window.WardData?.Microbiology?.flashcards) {
                try {
                    const fb = await WardData.Microbiology.flashcards(count ?? 8);
                    flashcards = fb.cards || [];
                } catch { /* fall through */ }
            }
            if (!flashcards.length) {
                if (stage) {
                    stage.innerHTML = '<p class="text-ward-danger text-center py-8 text-sm">Could not load flashcards. Refresh the page or check that study content is available.</p>';
                }
                showToast('Flashcard load failed — try refreshing the page.', 'error');
                return;
            }
            showToast('Loaded flashcards from local content.', 'info');
        }

        if (shuffle && flashcards.length > 1) {
            flashcards = (WardData?.shuffleArray || ((a) => [...a].sort(() => Math.random() - 0.5)))(flashcards);
        }
        cardIndex = 0;
        cardFlipped = false;
        hideDeckComplete();
        showCard();
        updateFcStats();
        reportProgress(flashcards.length, 'flashcards');
    }

    function renderFcDots() {
        const dots = document.getElementById('micro-fc-dots');
        if (!dots) return;
        dots.innerHTML = flashcards.map((c, i) => {
            const rating = fcRatings[c.id] || '';
            const cls = [
                'micro-fc-dot',
                i === cardIndex ? 'active' : '',
                rating === 'know' ? 'known' : '',
                rating === 'review' ? 'review' : '',
            ].filter(Boolean).join(' ');
            return `<button type="button" class="${cls}" title="Card ${i + 1}" aria-label="Go to card ${i + 1}" onclick="Microbiology.goToCard(${i})"></button>`;
        }).join('');
    }

    function goToCard(index) {
        if (index < 0 || index >= flashcards.length) return;
        cardIndex = index;
        showCard();
    }

    function setRatingButtons(enabled) {
        document.getElementById('mfc-btn-review')?.toggleAttribute('disabled', !enabled);
        document.getElementById('mfc-btn-know')?.toggleAttribute('disabled', !enabled);
    }

    function showCard() {
        if (!flashcards.length) {
            const stage = document.getElementById('micro-flashcard-stage');
            if (stage) stage.innerHTML = '<p class="text-ward-500 text-center py-8">No cards loaded.</p>';
            return;
        }
        const card = flashcards[cardIndex];
        const inner = document.getElementById('micro-flashcard-inner');
        if (inner) inner.classList.remove('flipped');
        cardFlipped = false;

        document.getElementById('mfc-front').textContent = card.front;
        const typeEl = document.getElementById('mfc-type');
        if (typeEl) typeEl.textContent = card.type || '';
        document.getElementById('mfc-back-name').textContent = card.back || '';
        document.getElementById('mfc-back-precautions').textContent = card.precautions || '—';
        document.getElementById('mfc-back-nursing').textContent = card.nursing_action || '—';
        document.getElementById('mfc-back-clinical').textContent = card.clinical_why || '';
        document.getElementById('mfc-front-view')?.classList.remove('hidden');
        document.getElementById('mfc-back-view')?.classList.add('hidden');
        document.getElementById('mfc-verify-btn')?.classList.remove('hidden');
        document.getElementById('micro-flashcard-counter').textContent = `${cardIndex + 1} / ${flashcards.length}`;
        setRatingButtons(false);
        renderFcDots();
    }

    function flipCard() {
        if (!flashcards.length) return;
        cardFlipped = !cardFlipped;
        document.getElementById('micro-flashcard-inner')?.classList.toggle('flipped', cardFlipped);
        document.getElementById('mfc-front-view')?.classList.toggle('hidden', cardFlipped);
        document.getElementById('mfc-back-view')?.classList.toggle('hidden', !cardFlipped);
        if (cardFlipped) setRatingButtons(true);
    }

    function rateCard(rating) {
        const card = flashcards[cardIndex];
        if (!card) return;
        fcRatings[card.id] = rating;
        saveFcRatings();
        updateFcStats();
        renderFcDots();
        if (cardIndex < flashcards.length - 1) {
            cardIndex++;
            showCard();
        } else {
            setRatingButtons(false);
            showDeckComplete();
        }
        reportProgress(1, 'flashcards');
    }

    function showDeckComplete() {
        const known = Object.values(fcRatings).filter(r => r === 'know').length;
        const review = Object.values(fcRatings).filter(r => r === 'review').length;
        const complete = document.getElementById('micro-fc-complete');
        const stage = document.getElementById('micro-flashcard-stage');
        if (!complete) return;
        if (stage) stage.classList.add('hidden');
        complete.classList.remove('hidden');
        complete.innerHTML = `
            <div class="text-center py-8">
                <div class="text-xl font-bold text-ward-success mb-2">Deck Complete!</div>
                <p class="text-sm text-ward-400 mb-4">Known: <strong>${known}</strong> · Review: <strong>${review}</strong></p>
                <div class="flex flex-wrap justify-center gap-2">
                    <button type="button" class="btn-primary text-sm" onclick="Microbiology.loadFlashcards(8, true)">New Deck (8)</button>
                    <button type="button" class="btn-secondary text-sm" onclick="Microbiology.exportCurrentDeck()">Export Deck</button>
                </div>
            </div>`;
    }

    function hideDeckComplete() {
        document.getElementById('micro-fc-complete')?.classList.add('hidden');
        document.getElementById('micro-flashcard-stage')?.classList.remove('hidden');
    }

    function exportCurrentDeck() {
        if (!flashcards.length) {
            showToast('Load flashcards first.', 'error');
            return;
        }
        const lines = flashcards.map((c, i) => {
            const rating = fcRatings[c.id] ? ` [${fcRatings[c.id]}]` : '';
            return `## ${i + 1}. ${c.front}${rating}\n\n**Type:** ${c.type || '—'}\n\n**Precautions:** ${c.precautions || '—'}\n\n**Nursing Action:** ${c.nursing_action || '—'}\n\n${c.clinical_why || ''}\n`;
        });
        const header = `# The Ward — Microbiology Flashcards\n\nExported ${new Date().toLocaleDateString()} · ${flashcards.length} cards\n\n---\n\n`;
        WardExport.downloadText('ward-microbiology-deck.md', header + lines.join('\n'), 'text/markdown;charset=utf-8');
        showToast('Deck exported as Markdown.');
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

        if (e.key === ' ' || e.key === 'Spacebar') {
            e.preventDefault();
            flipCard();
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            nextCard();
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault();
            prevCard();
        }
    }

    document.addEventListener('keydown', handleFlashcardKeys);

    // ── Export ────────────────────────────────────────────────────────────────
    async function copyToClipboard() {
        const res = await fetch('/api/microbiology/export/clipboard');
        const data = await res.json();
        await WardExport.copyToClipboard(data.content, 'Microbiology study sheet copied to clipboard!');
    }

    async function exportStudySheet() {
        const res = await fetch('/api/microbiology/export/study-sheet');
        const html = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const body = doc.body.innerHTML;
        const meta = doc.querySelector('.meta')?.textContent || 'Open RN Microbiology';
        WardExport.openPrintableHtml('Microbiology Study Sheet', body, meta);
    }

    async function exportMarkdown() {
        const res = await fetch('/api/microbiology/export/flashcards');
        const data = await res.json();
        WardExport.downloadText('ward-microbiology-flashcards.md', data.content, 'text/markdown;charset=utf-8');
    }

    async function exportFlashcardsPDF() {
        const esc = WardExport.escapeHtml;
        let cards = flashcards.length ? [...flashcards] : [];
        if (!cards.length) {
            const res = await fetch('/api/microbiology/flashcards?count=20');
            const data = await res.json();
            cards = data.cards || [];
        }

        const rows = cards.map((c, i) => `
            <div class="card" style="margin-bottom:1rem;padding:1rem;border:1px solid #ccc;break-inside:avoid">
                <div style="font-weight:700;font-size:14pt;margin-bottom:0.5rem">${i + 1}. ${esc(c.front)}</div>
                <div style="font-size:10pt;color:#444">${esc(c.type || '')}</div>
                <hr style="margin:0.5rem 0;border-color:#ddd">
                <div><strong>Full name:</strong> ${esc(c.back || '')}</div>
                <div><strong>Precautions:</strong> ${esc(c.precautions || '')}</div>
                <div><strong>Nursing:</strong> ${esc(c.nursing_action || '')}</div>
                <div style="font-size:9pt;color:#666;margin-top:0.25rem">${esc(c.clinical_why || '')}</div>
            </div>
        `).join('');

        WardExport.openPrintableHtml(
            'Microbiology Pathogen Flashcards',
            rows,
            `${cards.length} pathogens · Open RN Microbiology`,
        );
    }

    // ── Enhanced exports (WardExport client-side builders) ────────────────────
    async function exportPathogenCheatSheet() {
        await ensureLearnData();
        const pathogens = learnData?.pathogens || [];
        if (!pathogens.length) {
            showToast('Pathogen data not loaded.', 'error');
            return;
        }

        const esc = WardExport.escapeHtml;
        const rows = pathogens.map((p, i) => `
            <tr>
                <td>${i + 1}</td>
                <td><strong>${esc(p.name)}</strong><br><span class="muted">${esc(p.full_name || '')}</span></td>
                <td>${esc(p.type)}</td>
                <td>${esc(p.transmission)}</td>
                <td><strong>${esc(p.precautions)}</strong></td>
                <td class="muted">${esc(p.nursing_action)}</td>
            </tr>
        `).join('');

        WardExport.openPrintableHtml(
            'Pathogen Cheat Sheet',
            `<table>
                <thead>
                    <tr>
                        <th>#</th><th>Pathogen</th><th>Type</th>
                        <th>Transmission</th><th>Precautions</th><th>Nursing Action</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>`,
            `${pathogens.length} pathogens · Open RN Microbiology`,
        );
    }

    async function exportPathogenJSON() {
        await ensureLearnData();
        const pathogens = learnData?.pathogens || [];
        if (!pathogens.length) {
            showToast('Pathogen data not loaded.', 'error');
            return;
        }
        const payload = {
            format: 'json',
            module: 'microbiology',
            total: pathogens.length,
            source: 'Open RN Microbiology',
            pathogens,
        };
        WardExport.downloadText(
            'ward-microbiology-pathogens.json',
            JSON.stringify(payload, null, 2),
            'application/json;charset=utf-8',
        );
    }

    async function exportInfectionChainSheet() {
        if (!chainData.links.length) await loadChainBuilder();

        const esc = WardExport.escapeHtml;
        const rows = chainData.links.map((link, i) => `
            <tr>
                <td>${i + 1}</td>
                <td><strong>${esc(link.name)}</strong></td>
                <td>${esc(link.description)}</td>
                <td class="avoid">${esc(link.intervention)}</td>
            </tr>
        `).join('');

        WardExport.openPrintableHtml(
            'Chain of Infection Reference',
            `<table>
                <thead><tr><th>#</th><th>Link</th><th>Description</th><th>Break It With</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
            <p class="muted">Break any link to prevent transmission. Hand hygiene is the single most effective intervention.</p>`,
            `${chainData.links.length} chain links · NCLEX infection control`,
        );
    }

    // ── Progress ──────────────────────────────────────────────────────────────
    async function reportProgress(items, activityType, score) {
        await fetch('/api/microbiology/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items_studied: items, activity_type: activityType, score: score ?? null }),
        });
        refreshModuleProgress();
    }

    async function refreshModuleProgress() {
        const res = await fetch('/api/microbiology/stats');
        const data = await res.json();
        const bar = document.getElementById('module-progress-bar');
        const pct = document.getElementById('module-progress-pct');
        if (bar) bar.style.width = data.percentage + '%';
        if (pct) pct.textContent = data.percentage + '%';
    }

    // ── Init ──────────────────────────────────────────────────────────────────
    function init() {
        WardTabs.register('/modules/microbiology', { validTabs: VALID_TABS, defaultTab: DEFAULT_TAB, switchTab });
        WardTabs.init('/modules/microbiology');
        loadChainBuilder();
    }

    return {
        switchTab,
        selectChainLink,
        submitChainBreak,
        nextChainChallenge,
        resetChainBuilder,
        switchLearnSubtab,
        toggleRefCard,
        loadBreakChainScenarios,
        answerBreakChain,
        nextBreakChain,
        loadWhatIfScenarios,
        answerWhatIf,
        nextWhatIf,
        setPracticeMode,
        startPractice,
        answerPractice,
        nextPracticeQuestion,
        loadFlashcards,
        goToCard,
        flipCard,
        rateCard,
        nextCard,
        prevCard,
        exportCurrentDeck,
        copyToClipboard,
        exportStudySheet,
        exportMarkdown,
        exportFlashcardsPDF,
        exportPathogenCheatSheet,
        exportPathogenJSON,
        exportInfectionChainSheet,
        init,
    };
})();

document.addEventListener('DOMContentLoaded', () => Microbiology.init());