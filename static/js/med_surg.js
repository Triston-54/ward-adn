/**
 * The Ward — Medical-Surgical Nursing Module (Static)
 */
const MedSurg = (() => {
    const MODULE_ID = 'med_surg';
    const VALID_TABS = ['core-concepts', 'body-systems', 'procedures', 'priority-actions', 'flashcards', 'practice', 'export'];
    const DEFAULT_TAB = 'core-concepts';
    const esc = (s) => (WardExport?.escapeHtml || (x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))))(String(s ?? ''));

    let moduleData = null;
    let flashcards = [];
    let cardIndex = 0;
    let cardFlipped = false;
    let practiceQuestions = [];
    let practiceIndex = 0;
    let practiceCorrect = 0;
    let priorityIndex = 0;
    let priorityCorrect = 0;
    let priorityDrill = [];

    function switchTab(tab) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.querySelectorAll('.ms-tab-btn').forEach(b => b.classList.remove('active'));
        const panel = document.getElementById('tab-' + tab);
        const btn = document.querySelector(`[data-tab="${tab}"]`);
        if (panel) panel.classList.remove('hidden');
        if (btn) btn.classList.add('active');

        if (tab === 'core-concepts' && moduleData) renderConcepts();
        if (tab === 'body-systems' && moduleData) renderBodySystems();
        if (tab === 'procedures' && moduleData) renderProcedures();
        if (tab === 'priority-actions' && !priorityDrill.length) loadPriorityDrill();
        if (tab === 'flashcards' && !flashcards.length) loadFlashcards(15);

        history.replaceState(null, '', location.pathname + (tab !== DEFAULT_TAB ? '#' + tab : ''));
    }

    async function loadData() {
        if (moduleData) return moduleData;
        const res = await fetch('/api/med-surg/content');
        moduleData = await res.json();
        return moduleData;
    }

    function renderConcepts() {
        const el = document.getElementById('ms-concepts-container');
        if (!el || !moduleData) return;
        const concepts = moduleData.core_concepts || [];
        el.innerHTML = `
            <p class="text-xs text-ward-500 mb-3">${concepts.length} foundational concepts</p>
            <div class="ms-concept-list">
                ${concepts.map(c => `
                    <details class="ms-concept-card">
                        <summary>${esc(c.title)}</summary>
                        <div class="px-4 pb-3">
                            <p class="text-sm text-ward-300">${esc(c.summary)}</p>
                            <p class="text-xs text-ward-400 mt-2">${esc(c.content)}</p>
                            <p class="text-xs text-sky-400 mt-2"><strong>NCLEX:</strong> ${esc(c.clinical_relevance)}</p>
                        </div>
                    </details>
                `).join('')}
            </div>`;
    }

    function renderBodySystems(filter = 'all') {
        const el = document.getElementById('ms-systems-container');
        const sel = document.getElementById('ms-system-filter');
        if (!el || !moduleData) return;

        const systems = moduleData.body_systems || [];
        if (sel && sel.options.length <= 1) {
            systems.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = s.title;
                sel.appendChild(opt);
            });
        }

        const filtered = filter === 'all' ? systems : systems.filter(s => s.id === filter);
        el.innerHTML = filtered.map(s => `
            <details class="ms-system-card" open>
                <summary>${esc(s.title)}</summary>
                <div class="ms-system-body">
                    <p class="text-sm text-ward-300">${esc(s.pathophysiology)}</p>
                    <div class="ms-section-label">Nursing Care</div>
                    <ul class="ms-list">${(s.nursing_care || []).map(n => `<li>${esc(n)}</li>`).join('')}</ul>
                    <div class="ms-section-label">Safety</div>
                    <ul class="ms-list">${(s.safety || []).map(n => `<li>${esc(n)}</li>`).join('')}</ul>
                    <div class="ms-section-label">Priority Actions</div>
                    <ul class="ms-list">${(s.priority_actions || []).map(n => `<li>${esc(n)}</li>`).join('')}</ul>
                    <div class="ms-section-label">Key Conditions</div>
                    <p class="text-xs text-ward-400">${(s.key_conditions || []).map(esc).join(' · ')}</p>
                </div>
            </details>
        `).join('');
    }

    function filterBodySystem(id) {
        renderBodySystems(id);
    }

    function renderProcedures() {
        const el = document.getElementById('ms-procedures-container');
        if (!el || !moduleData) return;
        el.innerHTML = (moduleData.procedures || []).map(p => `
            <div class="ms-procedure-card">
                <h3 class="font-semibold text-ward-100 text-sm">${esc(p.title)}</h3>
                <span class="text-xs text-ward-500">${esc(p.category)}</span>
                ${['pre_procedure', 'intra_procedure', 'post_procedure'].map(phase => `
                    <div class="mt-2">
                        <div class="ms-procedure-phase">${phase.replace('_', ' ')}</div>
                        <ul class="ms-list">${(p[phase] || []).map(s => `<li>${esc(s)}</li>`).join('')}</ul>
                    </div>
                `).join('')}
            </div>
        `).join('');
    }

    async function loadPriorityDrill() {
        await loadData();
        priorityDrill = [...(moduleData.priority_drill || [])];
        priorityIndex = 0;
        priorityCorrect = 0;
        document.getElementById('ms-priority-total').textContent = priorityDrill.length;
        renderPriorityQuestion();
    }

    function renderPriorityQuestion() {
        const el = document.getElementById('ms-priority-container');
        if (!el || priorityIndex >= priorityDrill.length) {
            if (el) el.innerHTML = `<p class="text-ward-success text-sm">Drill complete! Score: ${priorityCorrect}/${priorityDrill.length}</p>`;
            return;
        }
        const q = priorityDrill[priorityIndex];
        el.innerHTML = `
            <div class="ms-priority-card">
                <p class="text-sm text-ward-200 mb-4">${esc(q.scenario)}</p>
                ${q.options.map((opt, i) => `
                    <button class="ms-priority-option" onclick="MedSurg.answerPriority(${i})">${esc(opt)}</button>
                `).join('')}
            </div>`;
    }

    function answerPriority(idx) {
        const q = priorityDrill[priorityIndex];
        const opts = document.querySelectorAll('.ms-priority-option');
        opts.forEach((btn, i) => {
            btn.disabled = true;
            if (i === q.correct_index) btn.classList.add('correct');
            else if (i === idx) btn.classList.add('incorrect');
        });
        if (idx === q.correct_index) priorityCorrect++;
        document.getElementById('ms-priority-score').textContent = priorityCorrect;
        setTimeout(() => { priorityIndex++; renderPriorityQuestion(); }, 1500);
    }

    async function loadFlashcards(count) {
        await loadData();
        flashcards = (WardData?.shuffleArray || (a => [...a].sort(() => Math.random() - 0.5)))([...(moduleData.flashcards || [])]).slice(0, count);
        cardIndex = 0;
        cardFlipped = false;
        renderCard();
    }

    function renderCard() {
        const front = document.getElementById('msfc-front');
        const back = document.getElementById('msfc-back');
        const backView = document.getElementById('msfc-back-view');
        const frontView = document.getElementById('msfc-front-view');
        const counter = document.getElementById('msfc-counter');
        const cat = document.getElementById('msfc-category');
        if (!flashcards.length) return;
        const c = flashcards[cardIndex];
        if (front) front.textContent = c.front;
        if (back) back.textContent = c.back;
        if (cat) cat.textContent = c.category || '';
        if (counter) counter.textContent = `${cardIndex + 1}/${flashcards.length}`;
        if (cardFlipped) {
            frontView?.classList.add('hidden');
            backView?.classList.remove('hidden');
        } else {
            frontView?.classList.remove('hidden');
            backView?.classList.add('hidden');
        }
    }

    function flipCard() {
        cardFlipped = !cardFlipped;
        renderCard();
    }

    function nextCard() {
        if (cardIndex < flashcards.length - 1) { cardIndex++; cardFlipped = false; renderCard(); }
    }

    function prevCard() {
        if (cardIndex > 0) { cardIndex--; cardFlipped = false; renderCard(); }
    }

    async function startPractice(count) {
        const res = await fetch(`/api/med-surg/practice?count=${count}`);
        const data = await res.json();
        practiceQuestions = data.questions || [];
        practiceIndex = 0;
        practiceCorrect = 0;
        renderPracticeQuestion();
    }

    function renderPracticeQuestion() {
        const area = document.getElementById('ms-practice-area');
        const score = document.getElementById('ms-practice-score');
        if (!area) return;
        if (practiceIndex >= practiceQuestions.length) {
            area.innerHTML = `<p class="text-ward-success">Session complete! ${practiceCorrect}/${practiceQuestions.length} correct.</p>`;
            if (score) score.textContent = `${practiceCorrect}/${practiceQuestions.length}`;
            return;
        }
        const q = practiceQuestions[practiceIndex];
        if (score) score.textContent = `${practiceCorrect}/${practiceIndex}`;
        area.innerHTML = `
            <div class="ms-practice-q">
                <p class="text-sm text-ward-100 mb-3">${esc(q.question)}</p>
                <span class="stat-pill text-[10px]">${esc(q.category)}</span>
                ${q.options.map((opt, i) => `
                    <button class="ms-practice-option" onclick="MedSurg.answerPractice(${i})">${esc(opt)}</button>
                `).join('')}
            </div>`;
    }

    function answerPractice(idx) {
        const q = practiceQuestions[practiceIndex];
        const opts = document.querySelectorAll('.ms-practice-option');
        opts.forEach((btn, i) => {
            btn.disabled = true;
            if (i === q.correct_index) btn.classList.add('correct');
            else if (i === idx) btn.classList.add('incorrect');
        });
        if (idx === q.correct_index) practiceCorrect++;
        const area = document.getElementById('ms-practice-area');
        const rat = document.createElement('div');
        rat.className = 'ms-rationale';
        rat.innerHTML = `<strong>Rationale:</strong> ${esc(q.rationale)}`;
        area.appendChild(rat);
        setTimeout(() => { practiceIndex++; renderPracticeQuestion(); }, 2000);
    }

    async function exportFlashcards() {
        await loadData();
        let md = '# The Ward — Med-Surg Flashcards\n\n';
        (moduleData.flashcards || []).forEach((c, i) => {
            md += `## ${i + 1}. ${c.front}\n**Answer:** ${c.back}\n**Category:** ${c.category}\n\n`;
        });
        WardExport?.downloadText?.(md, 'ward-med-surg-flashcards.md') || downloadBlob(md, 'ward-med-surg-flashcards.md');
    }

    async function exportBodySystems() {
        await loadData();
        let md = '# The Ward — Med-Surg Body Systems Summary\n\n';
        (moduleData.body_systems || []).forEach(s => {
            md += `## ${s.title}\n${s.pathophysiology}\n\n`;
        });
        WardExport?.downloadText?.(md, 'ward-med-surg-systems.md') || downloadBlob(md, 'ward-med-surg-systems.md');
    }

    function downloadBlob(content, filename) {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([content], { type: 'text/markdown' }));
        a.download = filename;
        a.click();
    }

    function init() {
        const hash = location.hash.replace('#', '');
        loadData().then(() => {
            renderConcepts();
            if (hash && VALID_TABS.includes(hash)) switchTab(hash);
            else switchTab(DEFAULT_TAB);
        });
        document.querySelector('[data-nav="med_surg"]')?.closest('nav')?.querySelector('[data-nav="med_surg"]')?.classList.add('active');
        const navLink = document.querySelector('.sidebar-link[data-nav="med_surg"]');
        if (navLink) navLink.classList.add('active');
    }

    return {
        init, switchTab, filterBodySystem, loadFlashcards, flipCard, nextCard, prevCard,
        startPractice, answerPractice, answerPriority, loadPriorityDrill,
        exportFlashcards, exportBodySystems,
    };
})();