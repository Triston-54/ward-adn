/**
 * WardSocratic — reusable global Socratic teaching partner
 * Guiding questions first · track-aware (Nursing / Pharmacy) · module + tab context
 */
const WardSocratic = (() => {
    const STORAGE_KEY = 'ward_socratic_history';
    const MAX_TURNS = 8;

    const TRACK_LABELS = {
        nursing: 'Nursing Track',
        pharmacy: 'Pharmacy Track',
    };

    const MODULE_REGISTRY = {
        terminology: { track: 'nursing', label: 'Medical Terminology', defaultTopic: 'general', topics: ['general', 'assessment_finding'] },
        microbiology: { track: 'nursing', label: 'Microbiology', defaultTopic: 'pathophysiology', topics: ['general', 'pathophysiology', 'assessment_finding'] },
        dosage: { track: 'nursing', label: 'NURS 145 — Dosage', defaultTopic: 'calculation', topics: ['general', 'calculation', 'drug_mechanism'] },
        assessment: { track: 'nursing', label: 'Health Assessment', defaultTopic: 'assessment_finding', topics: ['general', 'assessment_finding', 'pathophysiology'] },
        mental_health: { track: 'nursing', label: 'Mental Health', defaultTopic: 'psychosocial', topics: ['general', 'psychosocial', 'assessment_finding', 'drug_mechanism'] },
        pharmacy: { track: 'pharmacy', label: 'Pharmacy Track', defaultTopic: 'general', topics: ['general', 'drug_mechanism', 'calculation', 'compounding'] },
        pharmacy_calculations: { track: 'pharmacy', label: 'Pharmacy Calculations', defaultTopic: 'calculation', topics: ['general', 'calculation', 'compounding', 'drug_mechanism'] },
        pathophysiology: { track: 'nursing', label: 'Pathophysiology', defaultTopic: 'pathophysiology', topics: ['general', 'pathophysiology', 'drug_mechanism', 'assessment_finding'], status: 'active' },
        maternal_child: { track: 'nursing', label: 'Maternal & Child Health', defaultTopic: 'assessment_finding', topics: ['general', 'pathophysiology', 'assessment_finding', 'psychosocial', 'calculation'], status: 'stub' },
        general: { track: 'nursing', label: 'General Nursing', defaultTopic: 'general', topics: ['general', 'pathophysiology', 'drug_mechanism', 'assessment_finding', 'calculation'] },
    };

    const TOPIC_LABELS = {
        general: 'General',
        pathophysiology: 'Pathophysiology',
        drug_mechanism: 'Drug Mechanism',
        assessment_finding: 'Assessment',
        calculation: 'Calculation',
        psychosocial: 'Psychosocial',
        compounding: 'Compounding',
    };

    const PLACEHOLDERS = {
        nursing: 'Ask about pathophysiology, drug mechanisms, assessment findings, or calculations…',
        pharmacy: 'Ask about mechanisms, compounding math, verification workflows, or NAPLEX-style problems…',
    };

    const PATH_MODULE_MAP = {
        '/modules/terminology': 'terminology',
        '/modules/microbiology': 'microbiology',
        '/modules/dosage': 'dosage',
        '/modules/assessment': 'assessment',
        '/modules/mental-health': 'mental_health',
        '/modules/pathophysiology': 'pathophysiology',
        '/modules/maternal-child': 'maternal_child',
        '/pharmacy/modules/calculations': 'pharmacy_calculations',
        '/pharmacy': 'pharmacy',
    };

    let activeModule = detectModuleFromPath();
    let activeTopic = 'general';
    let pageContext = { tab: '', subject: '', snippet: '', track: '' };
    let serverConfig = null;

    function detectModuleFromPath() {
        const dataMod = document.querySelector('[data-module]')?.dataset?.module;
        if (dataMod && MODULE_REGISTRY[dataMod]) return dataMod;
        const path = window.location.pathname;
        const sorted = Object.keys(PATH_MODULE_MAP).sort((a, b) => b.length - a.length);
        for (const prefix of sorted) {
            if (path.startsWith(prefix)) return PATH_MODULE_MAP[prefix];
        }
        return 'general';
    }

    function modulePlaceholder(moduleId) {
        const cfg = getModuleConfig(moduleId);
        if (cfg.placeholder) return cfg.placeholder;
        if (serverConfig?.modules?.[moduleId]?.placeholder) {
            return serverConfig.modules[moduleId].placeholder;
        }
        if (serverConfig?.placeholder && moduleId === activeModule) {
            return serverConfig.placeholder;
        }
        return PLACEHOLDERS[cfg.track] || PLACEHOLDERS.nursing;
    }

    function detectTrackFromPath() {
        return window.location.pathname.startsWith('/pharmacy') ? 'pharmacy' : 'nursing';
    }

    function mergeServerRegistry() {
        if (!serverConfig?.modules) return;
        for (const [mid, meta] of Object.entries(serverConfig.modules)) {
            MODULE_REGISTRY[mid] = {
                ...MODULE_REGISTRY[mid],
                track: meta.track || MODULE_REGISTRY[mid]?.track || 'nursing',
                label: meta.label || MODULE_REGISTRY[mid]?.label || mid,
                hint: meta.hint || MODULE_REGISTRY[mid]?.hint || '',
                defaultTopic: meta.default_topic || MODULE_REGISTRY[mid]?.defaultTopic || 'general',
                topics: meta.topics || MODULE_REGISTRY[mid]?.topics || ['general'],
                status: meta.status || MODULE_REGISTRY[mid]?.status || 'active',
                placeholder: meta.placeholder || MODULE_REGISTRY[mid]?.placeholder,
            };
        }
        if (serverConfig.path_module_map) {
            Object.assign(PATH_MODULE_MAP, serverConfig.path_module_map);
        }
        if (typeof registerSocraticCommandsFromRegistry === 'function') {
            registerSocraticCommandsFromRegistry(serverConfig);
        }
    }

    function getModuleConfig(moduleId) {
        return MODULE_REGISTRY[moduleId] || MODULE_REGISTRY.general;
    }

    function getTrack(moduleId) {
        return getModuleConfig(moduleId).track || detectTrackFromPath();
    }

    function escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = str ?? '';
        return d.innerHTML;
    }

    function formatText(text) {
        if (!text) return '';
        let html = escapeHtml(text);
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="text-ward-200">$1</strong>');
        html = html.replace(/_(.+?)_/g, '<em class="text-ward-400">$1</em>');
        return html;
    }

    function getHistory() {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch {
            return [];
        }
    }

    function saveTurn(role, content) {
        const history = getHistory();
        history.push({ role, content, ts: Date.now() });
        while (history.length > MAX_TURNS * 2) history.shift();
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    }

    function clearHistory() {
        sessionStorage.removeItem(STORAGE_KEY);
        renderHistory();
        hideSection('socratic-followups');
        hideSection('socratic-sources');
        hideSection('socratic-dynamic-actions');
        updatePhaseBadge('explore', activeTopic);
    }

    function hideSection(id) {
        document.getElementById(id)?.classList.add('hidden');
    }

    function setPageContext(ctx) {
        const mod = getModuleConfig(activeModule);
        pageContext = {
            tab: ctx?.tab || pageContext.tab || '',
            subject: ctx?.subject || '',
            snippet: (ctx?.snippet || '').slice(0, 400),
            track: ctx?.track || mod.track || detectTrackFromPath(),
        };
        updateContextChip();
        applyTrackTheme(pageContext.track);
    }

    /**
     * Preferred API for modules — sets module, tab, subject, and optional snippet/topic.
     */
    function setModuleContext({ module, tab, subject, snippet, topic }) {
        if (module) activeModule = module;
        if (topic) setTopic(topic);
        const cfg = getModuleConfig(activeModule);
        const tabLabel = tab ? ` · ${tab}` : '';
        setPageContext({
            tab: tab || '',
            subject: subject || `${cfg.label}${tabLabel}`,
            snippet: snippet || '',
            track: cfg.track,
        });
    }

    function updateContextChip() {
        const wrap = document.getElementById('socratic-page-context');
        const label = document.getElementById('socratic-context-label');
        const trackBadge = document.getElementById('socratic-track-badge');
        if (!wrap || !label) return;

        const track = pageContext.track || getTrack(activeModule);
        if (trackBadge) {
            trackBadge.textContent = TRACK_LABELS[track] || track;
            trackBadge.className = `socratic-track-badge ${track}`;
        }

        const subj = pageContext.subject;
        const tab = pageContext.tab;
        if (subj || tab) {
            label.textContent = subj ? (tab && !subj.includes(tab) ? `${subj} · ${tab}` : subj) : tab;
            wrap.classList.remove('hidden');
        } else {
            wrap.classList.add('hidden');
        }
    }

    function applyTrackTheme(track) {
        const modal = document.getElementById('socratic-modal');
        if (!modal) return;
        modal.classList.toggle('socratic--pharmacy', track === 'pharmacy');
        modal.classList.toggle('socratic--nursing', track !== 'pharmacy');
        updateProfessionalActionLabel(track);
    }

    function updateProfessionalActionLabel(track) {
        const btn = document.getElementById('socratic-professional-btn');
        if (!btn) return;
        const role = track === 'pharmacy' ? 'pharmacist' : 'nursing';
        btn.textContent = `Key ${role} considerations`;
        btn.title = `What are the key ${role} considerations for this topic?`;
    }

    function renderTopicChips(moduleId) {
        const container = document.getElementById('socratic-topic-chips');
        if (!container) return;
        const cfg = getModuleConfig(moduleId);
        const topics = cfg.topics || ['general'];
        container.innerHTML = topics.map(t => `
            <button type="button" data-topic="${t}" class="socratic-topic-chip${t === activeTopic ? ' active' : ''}"
                    onclick="WardSocratic.setTopic('${t}')">${escapeHtml(TOPIC_LABELS[t] || t)}</button>
        `).join('');
    }

    function setTopic(topic) {
        activeTopic = topic;
        document.querySelectorAll('.socratic-topic-chip').forEach(chip => {
            chip.classList.toggle('active', chip.dataset.topic === topic);
        });
    }

    function updatePhaseBadge(phase, topicCategory) {
        const badge = document.getElementById('socratic-phase-badge');
        if (!badge) return;
        const guiding = phase === 'explore';
        badge.textContent = guiding ? 'Guiding' : 'Teaching';
        badge.className = `socratic-phase-badge ${guiding ? 'explore' : 'teach'}`;
        if (topicCategory && topicCategory !== 'general') {
            badge.title = `Topic: ${(TOPIC_LABELS[topicCategory] || topicCategory)}`;
        }
    }

    function renderHistory() {
        const container = document.getElementById('socratic-history');
        if (!container) return;

        const history = getHistory();
        const cfg = getModuleConfig(activeModule);
        const track = getTrack(activeModule);

        if (!history.length) {
            const ctxHint = pageContext.subject
                ? `<p class="text-xs mt-2 text-ward-accent">Studying: <strong class="text-ward-300">${escapeHtml(pageContext.subject)}</strong></p>`
                : '';
            const trackNote = track === 'pharmacy'
                ? 'Pharmacy depth — verification, compounding, and board-style reasoning.'
                : 'NCLEX-aligned clinical judgment — I ask before I tell.';
            container.innerHTML = `
                <div class="text-center py-6 text-ward-500 text-sm">
                    <p class="mb-1 font-medium text-ward-purple">${escapeHtml(cfg.label)} teaching partner</p>
                    <p class="text-xs">${trackNote}</p>
                    <p class="text-xs mt-2 text-ward-600">Turn 1–2: guiding questions only. Use quick actions when you're ready for deeper teaching.</p>
                    ${ctxHint}
                </div>`;
            return;
        }

        container.innerHTML = history.map(turn => {
            const isUser = turn.role === 'user';
            return `
                <div class="flex ${isUser ? 'justify-end' : 'justify-start'}">
                    <div class="max-w-[85%] px-3 py-2 rounded-lg text-sm ${
                        isUser
                            ? 'bg-ward-purple/20 border border-ward-purple/30 text-ward-200'
                            : 'bg-ward-900 border border-ward-700 text-ward-300'
                    }">
                        <div class="text-[10px] uppercase tracking-wider mb-1 ${isUser ? 'text-ward-purple' : 'text-ward-500'}">
                            ${isUser ? 'You' : 'Socratic Tutor'}
                        </div>
                        <div class="whitespace-pre-wrap leading-relaxed socratic-response-text">${formatText(turn.content)}</div>
                    </div>
                </div>`;
        }).join('');
        container.scrollTop = container.scrollHeight;
    }

    function renderFollowUps(questions) {
        const section = document.getElementById('socratic-followups');
        const chips = document.getElementById('socratic-chips');
        if (!section || !chips || !questions?.length) {
            hideSection('socratic-followups');
            return;
        }
        chips.innerHTML = questions.map(q => `
            <button type="button" onclick="WardSocratic.askFollowUp(${JSON.stringify(q)})"
                    class="text-xs px-3 py-1.5 rounded-full border border-ward-purple/30 bg-ward-purple/10 text-ward-purple hover:bg-ward-purple/20 transition text-left">
                ${escapeHtml(q)}
            </button>
        `).join('');
        section.classList.remove('hidden');
    }

    function renderDynamicActions(actions) {
        const section = document.getElementById('socratic-dynamic-actions');
        const row = document.getElementById('socratic-dynamic-actions-row');
        if (!section || !row || !actions?.length) {
            hideSection('socratic-dynamic-actions');
            return;
        }
        row.innerHTML = actions.map(label => {
            const intent = _actionToIntent(label);
            return `
                <button type="button" onclick="WardSocratic.askIntent('${intent}')"
                        class="socratic-action-btn socratic-action-btn--dynamic">${escapeHtml(label)}</button>`;
        }).join('');
        section.classList.remove('hidden');
    }

    function _actionToIntent(label) {
        const lower = (label || '').toLowerCase();
        if (lower.includes('mechanism')) return 'explain_mechanism';
        if (lower.includes('clinically')) return 'clinical_why';
        if (lower.includes('consideration')) return 'professional_considerations';
        if (lower.includes('further')) return 'explain_further';
        return 'explore';
    }

    function renderSources(sources) {
        const section = document.getElementById('socratic-sources');
        const list = document.getElementById('socratic-sources-list');
        if (!section || !list || !sources?.length) {
            hideSection('socratic-sources');
            return;
        }
        window._socraticSourceCache = sources;
        window._sourceCache = sources;
        list.innerHTML = sources.map((s, i) => `
            <button type="button" onclick="showSource(${i})"
                    class="w-full text-left text-xs text-ward-400 hover:text-ward-accent transition flex items-center gap-1.5">
                <svg class="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                <span class="truncate">${escapeHtml(s.title)}</span>
            </button>
        `).join('');
        section.classList.remove('hidden');
    }

    function updateAiBadge(status, degradedReason) {
        const badge = document.getElementById('socratic-ai-badge');
        if (!badge) return;
        const styles = {
            live: 'border-ward-success/40 text-ward-success bg-ward-success/10',
            placeholder: 'border-ward-500/40 text-ward-500 bg-ward-700/30',
            error: 'border-ward-warning/40 text-ward-warning bg-ward-warning/10',
        };
        const labels = {
            live: 'live',
            placeholder: 'guided',
            error: degradedReason ? `fallback · ${degradedReason}` : 'fallback',
        };
        badge.className = `text-[10px] px-2 py-1 rounded border uppercase ${styles[status] || styles.placeholder}`;
        badge.textContent = labels[status] || status;
        badge.title = degradedReason
            ? `Structured teaching shown (${degradedReason}). Enable Ollama for live dialogue.`
            : (status === 'live' ? 'Ollama connected' : 'Structured Socratic teaching partner');
    }

    function setLoading(loading) {
        const el = document.getElementById('socratic-loading');
        const btn = document.getElementById('socratic-submit-btn');
        if (el) el.classList.toggle('hidden', !loading);
        if (btn) {
            btn.disabled = loading;
            btn.textContent = loading ? 'Thinking…' : 'Ask Tutor';
        }
    }

    function _intentQuestion(intent) {
        const subject = pageContext.subject;
        const history = getHistory();
        const lastUser = [...history].reverse().find(t => t.role === 'user');
        const focus = subject || (lastUser?.content?.slice(0, 120)) || 'what I am studying';
        const track = pageContext.track || getTrack(activeModule);
        const role = track === 'pharmacy' ? 'pharmacist' : 'nurse';

        const prompts = {
            explain_mechanism: `Explain the mechanism behind "${focus}" — target, effect, and what to monitor.`,
            explain_further: `Please explain "${focus}" further — go one layer deeper with a clinical example.`,
            clinical_why: track === 'pharmacy'
                ? `Why does "${focus}" matter clinically? Connect it to patient outcomes, verification, and NAPLEX judgment.`
                : `Why does "${focus}" matter clinically? Connect it to bedside nursing and patient safety.`,
            professional_considerations: `What are the key ${role} considerations for "${focus}"? Include monitoring, counseling, and safety checks.`,
        };
        return prompts[intent] || `Help me think through "${focus}" using guiding questions first.`;
    }

    function open(module, topic, ctx) {
        activeModule = module || detectModuleFromPath();
        const cfg = getModuleConfig(activeModule);
        const track = cfg.track;

        if (topic) setTopic(topic);
        else setTopic(cfg.defaultTopic);

        if (ctx) setPageContext({ ...ctx, track: ctx.track || track });
        else {
            pageContext.track = track;
            updateContextChip();
        }

        applyTrackTheme(track);
        renderTopicChips(activeModule);

        const label = document.getElementById('socratic-module-label');
        if (label) {
            label.textContent = `${cfg.label} · ${TRACK_LABELS[track] || track}`;
        }

        const input = document.getElementById('socratic-input');
        if (input) input.placeholder = modulePlaceholder(activeModule);

        document.getElementById('socratic-modal')?.classList.remove('hidden');
        document.getElementById('socratic-fab')?.classList.add('active');
        renderHistory();
        hideSection('socratic-followups');
        hideSection('socratic-sources');
        hideSection('socratic-dynamic-actions');
        updatePhaseBadge('explore', activeTopic);
        updateAiBadge('placeholder');
        input?.focus();
    }

    function openWithContext(subject, snippet, topic) {
        open(activeModule, topic, {
            tab: pageContext.tab,
            subject,
            snippet,
            track: pageContext.track || getTrack(activeModule),
        });
    }

    function close() {
        document.getElementById('socratic-modal')?.classList.add('hidden');
        document.getElementById('socratic-fab')?.classList.remove('active');
    }

    function askFollowUp(question) {
        const input = document.getElementById('socratic-input');
        if (input) input.value = question;
        submit('explore');
    }

    function askIntent(intent) {
        const modal = document.getElementById('socratic-modal');
        if (modal?.classList.contains('hidden')) open();
        const input = document.getElementById('socratic-input');
        if (input) input.value = _intentQuestion(intent);
        submit(intent);
    }

    async function reportProgress(moduleId) {
        try {
            await fetch('/api/socratic/progress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ module_id: moduleId, topic_category: activeTopic }),
            });
        } catch { /* non-blocking */ }
    }

    async function submit(intentOverride) {
        const input = document.getElementById('socratic-input');
        const question = input?.value?.trim();
        if (!question) return;

        const intent = intentOverride || 'explore';
        saveTurn('user', question);
        renderHistory();
        input.value = '';
        setLoading(true);

        const history = getHistory().slice(0, -1);
        const track = pageContext.track || getTrack(activeModule);

        try {
            const res = await fetch('/api/socratic/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    module_id: activeModule,
                    question,
                    context: JSON.stringify(history),
                    topic_category: activeTopic,
                    socratic_mode: true,
                    intent,
                    page_context: JSON.stringify({ ...pageContext, track }),
                }),
            });
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }
            const data = await res.json();

            saveTurn('assistant', data.response);
            renderHistory();
            renderFollowUps(data.follow_up_questions);
            renderSources(data.sources);
            renderDynamicActions(data.quick_actions);
            updateAiBadge(data.ai_status || 'placeholder', data.degraded_reason);
            updatePhaseBadge(data.phase || 'explore', data.topic_category);
            if (data.module_id) activeModule = data.module_id;
            if (data.topic_category && data.topic_category !== 'general') {
                setTopic(data.topic_category);
            }
            reportProgress(data.module_id || activeModule);
        } catch (err) {
            const msg = err?.message?.includes('HTTP')
                ? 'Tutor request failed. Please try again.'
                : 'Unable to reach tutor. Check that the server is running.';
            saveTurn('assistant', msg);
            renderHistory();
            updateAiBadge('error', 'network');
        } finally {
            setLoading(false);
        }
    }

    async function loadServerConfig() {
        try {
            const mod = detectModuleFromPath();
            const res = await fetch(`/api/socratic/config?module_id=${encodeURIComponent(mod)}`);
            if (res.ok) {
                serverConfig = await res.json();
                mergeServerRegistry();
            }
        } catch { /* use local registry */ }
        return serverConfig;
    }

    function init() {
        activeModule = detectModuleFromPath();
        const cfg = getModuleConfig(activeModule);
        setTopic(cfg.defaultTopic);
        setPageContext({
            tab: location.hash.replace('#', '') || '',
            subject: pageContext.subject || cfg.label,
            track: cfg.track,
        });
        loadServerConfig().then(() => {
            const input = document.getElementById('socratic-input');
            if (input) input.placeholder = modulePlaceholder(activeModule);
        });
        window.addEventListener('popstate', () => {
            activeModule = detectModuleFromPath();
            const modCfg = getModuleConfig(activeModule);
            setTopic(modCfg.defaultTopic);
            setPageContext({ track: modCfg.track, subject: modCfg.label });
        });
        window.addEventListener('hashchange', () => {
            const tab = location.hash.replace('#', '');
            if (tab && pageContext.tab !== tab) {
                const cfg = getModuleConfig(detectModuleFromPath());
                setPageContext({
                    ...pageContext,
                    tab,
                    subject: pageContext.subject || `${cfg.label} · ${tab}`,
                });
            }
        });
    }

    return {
        init,
        open,
        close,
        submit,
        askIntent,
        askFollowUp,
        setTopic,
        setPageContext,
        setModuleContext,
        clearHistory,
        openWithContext,
        detectModuleFromPath,
        getTrack,
        getModuleConfig,
        modulePlaceholder,
        loadServerConfig,
    };
})();

// Backward-compatible globals
window.WardSocratic = WardSocratic;
window.openSocraticMode = (m, t) => WardSocratic.open(m, t);
window.openSocraticModal = (m, t, ctx) => WardSocratic.open(m, t, ctx);
window.openSocraticWithContext = (s, sn, t) => WardSocratic.openWithContext(s, sn, t);
window.closeSocraticModal = () => WardSocratic.close();
window.submitSocratic = (intent) => WardSocratic.submit(intent);
window.askSocraticIntent = (intent) => WardSocratic.askIntent(intent);
window.setSocraticTopic = (t) => WardSocratic.setTopic(t);
window.setSocraticPageContext = (ctx) => WardSocratic.setPageContext(ctx);
window.clearSocraticHistory = () => WardSocratic.clearHistory();
window.askFollowUp = (q) => WardSocratic.askFollowUp(q);

document.addEventListener('DOMContentLoaded', () => WardSocratic.init());