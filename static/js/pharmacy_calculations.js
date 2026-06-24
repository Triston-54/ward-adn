/**
 * Pharmacy Calculations module — scaffold UI
 */
const PharmacyCalc = (() => {
    const MODULE_PATH = '/pharmacy/modules/calculations';
    const VALID_TABS = ['overview', 'topics'];
    const DEFAULT_TAB = 'overview';

    let _topics = [];
    let _calcTypes = [];

    function switchTab(tabId) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.getElementById(`tab-${tabId}`)?.classList.remove('hidden');
        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.tab === tabId);
        });
        if (location.hash.replace('#', '') !== tabId) {
            history.replaceState(null, '', `${MODULE_PATH}#${tabId}`);
        }
        const labels = { overview: 'Overview', topics: 'Topic Outline' };
        window.WardSocratic?.setModuleContext({
            module: 'pharmacy_calculations',
            tab: tabId,
            subject: `Pharmacy Calculations · ${labels[tabId] || tabId}`,
            topic: tabId === 'topics' ? 'compounding' : 'calculation',
        });
    }

    function init() {
        WardTabs.register(MODULE_PATH, { validTabs: VALID_TABS, defaultTab: DEFAULT_TAB, switchTab });
        WardTabs.init(MODULE_PATH);
        loadContent();
    }

    async function loadContent() {
        try {
            const res = await fetch('/api/pharmacy/calculations/topics');
            if (!res.ok) throw new Error('Failed to load');
            const data = await res.json();
            _topics = data.topics || [];
            _calcTypes = data.calc_types || [];
            renderCalcTypes();
            renderTopics();
            recordOverviewVisit();
        } catch {
            const typesEl = document.getElementById('pharm-calc-types');
            const topicsEl = document.getElementById('pharm-topic-grid');
            if (typesEl) typesEl.innerHTML = '<p class="text-ward-danger text-sm">Failed to load content.</p>';
            if (topicsEl) topicsEl.innerHTML = '<p class="text-ward-danger text-sm">Failed to load topics.</p>';
        }
    }

    function renderCalcTypes() {
        const el = document.getElementById('pharm-calc-types');
        if (!el) return;
        if (!_calcTypes.length) {
            el.innerHTML = '<p class="text-ward-500 text-sm">No calculator types defined yet.</p>';
            return;
        }
        el.innerHTML = _calcTypes.map(ct => `
            <span class="calc-type-pill ${ct.status || 'planned'}" title="${esc(ct.description || '')}">
                <span class="text-pharm-primary font-medium">${esc(ct.name)}</span>
                <span class="text-ward-600">· ${esc(ct.status || 'planned')}</span>
            </span>
        `).join('');
    }

    function renderTopics() {
        const el = document.getElementById('pharm-topic-grid');
        if (!el) return;
        el.innerHTML = _topics.map(t => `
            <div class="topic-card priority-${(t.priority || 'p2').toLowerCase()}">
                <div class="flex items-start justify-between gap-2 mb-2">
                    <h3 class="text-sm font-semibold text-ward-100">${esc(t.title)}</h3>
                    <span class="text-[10px] font-semibold uppercase tracking-wider text-ward-500">${esc(t.priority || '')}</span>
                </div>
                <span class="text-[10px] text-pharm-secondary uppercase tracking-wider">${esc(t.status || 'planned')}</span>
                ${t.subtopics?.length ? `
                    <ul class="mt-2 text-xs text-ward-400 space-y-1 list-disc list-inside">
                        ${t.subtopics.map(s => `<li>${esc(s)}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `).join('');
    }

    async function recordOverviewVisit() {
        try {
            await fetch('/api/pharmacy/calculations/progress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items_studied: 1, activity_type: 'overview' }),
            });
        } catch { /* silent */ }
    }

    function esc(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    return { switchTab, init };
})();