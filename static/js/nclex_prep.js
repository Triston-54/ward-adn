/**
 * The Ward — NCLEX Prep Center (Static)
 */
const NclexPrep = (() => {
    const esc = (s) => (WardExport?.escapeHtml || (x => String(x)))(String(s ?? ''));

    let content = null;
    let mode = 'topic';
    let selectedCategory = 'all';
    let sessionSize = 25;
    let questions = [];
    let currentIndex = 0;
    let score = 0;
    let missed = JSON.parse(localStorage.getItem('ward_nclex_missed') || '[]');

    async function loadContent() {
        if (content) return content;
        const res = await fetch('/api/nclex-prep/content');
        content = await res.json();
        return content;
    }

    function setMode(m) {
        mode = m;
        document.querySelectorAll('.nclex-mode-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('mode-' + m)?.classList.add('active');
        if (m === 'mixed') selectedCategory = 'mixed';
        if (m === 'weak') selectedCategory = 'weak';
    }

    function setSessionSize(n) {
        sessionSize = n;
        document.querySelectorAll('.nclex-size-btn').forEach(b => {
            b.classList.toggle('active', parseInt(b.dataset.size, 10) === n);
        });
    }

    function selectCategory(cat) {
        selectedCategory = cat;
        document.querySelectorAll('.nclex-topic-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.category === cat);
        });
    }

    function renderTopics() {
        const el = document.getElementById('nclex-topic-list');
        if (!el || !content) return;
        const cats = content.categories || [];
        el.innerHTML = `
            <button class="nclex-topic-btn ${selectedCategory === 'all' ? 'active' : ''}" data-category="all" onclick="NclexPrep.selectCategory('all')">
                All Topics <span class="nclex-topic-count">${content.total_questions || 0}</span>
            </button>
            ${cats.map(c => `
                <button class="nclex-topic-btn ${selectedCategory === c.name ? 'active' : ''}" data-category="${esc(c.name)}" onclick="NclexPrep.selectCategory('${esc(c.name).replace(/'/g, "\\'")}')">
                    ${esc(c.name)} <span class="nclex-topic-count">${c.count}</span>
                </button>
            `).join('')}`;
    }

    async function startSession() {
        await loadContent();
        let pool = content.all_questions || [];

        if (mode === 'weak' || selectedCategory === 'weak') {
            pool = pool.filter(q => missed.includes(q.id));
            if (!pool.length) {
                document.getElementById('nclex-question-area').innerHTML =
                    '<p class="text-ward-warning text-sm">No missed questions yet. Complete a practice session first.</p>';
                return;
            }
        } else if (selectedCategory !== 'all' && selectedCategory !== 'mixed') {
            pool = (content.questions_by_category || {})[selectedCategory] || pool;
        }

        questions = (WardData?.shuffleArray || (a => [...a].sort(() => Math.random() - 0.5)))([...pool]).slice(0, sessionSize);
        currentIndex = 0;
        score = 0;
        document.getElementById('nclex-rationale-panel')?.classList.add('hidden');
        renderQuestion();
    }

    function renderQuestion() {
        const area = document.getElementById('nclex-question-area');
        const progress = document.getElementById('nclex-progress');
        const bar = document.getElementById('nclex-progress-bar');
        const scoreEl = document.getElementById('nclex-score');

        if (!area) return;
        if (currentIndex >= questions.length) {
            area.innerHTML = `<div class="text-center py-8">
                <p class="text-lg font-semibold text-ward-accent">Session Complete</p>
                <p class="text-ward-300 mt-2">Score: ${score}/${questions.length} (${Math.round(100 * score / questions.length)}%)</p>
            </div>`;
            if (progress) progress.textContent = 'Complete';
            if (bar) bar.style.width = '100%';
            return;
        }

        const q = questions[currentIndex];
        if (progress) progress.textContent = `Question ${currentIndex + 1} of ${questions.length}`;
        if (bar) bar.style.width = `${((currentIndex) / questions.length) * 100}%`;
        if (scoreEl) scoreEl.textContent = `Score: ${score}/${currentIndex}`;

        area.innerHTML = `
            <div class="nclex-question-meta">
                <span class="stat-pill">${esc(q.category)}</span>
                ${q.ncj_step ? `<span class="nclex-ncj-tag">${esc(q.ncj_step)}</span>` : ''}
                ${q.difficulty ? `<span class="stat-pill">${esc(q.difficulty)}</span>` : ''}
            </div>
            <p class="nclex-question-stem">${esc(q.question)}</p>
            ${q.options.map((opt, i) => `
                <button class="nclex-option" onclick="NclexPrep.answer(${i})">${String.fromCharCode(65 + i)}. ${esc(opt)}</button>
            `).join('')}`;
    }

    function answer(idx) {
        const q = questions[currentIndex];
        const opts = document.querySelectorAll('.nclex-option');
        const correct = idx === q.correct_index;

        opts.forEach((btn, i) => {
            btn.disabled = true;
            if (i === q.correct_index) btn.classList.add('correct');
            else if (i === idx) btn.classList.add('incorrect');
        });

        if (correct) score++;
        else {
            if (!missed.includes(q.id)) {
                missed.push(q.id);
                localStorage.setItem('ward_nclex_missed', JSON.stringify(missed));
            }
        }

        const panel = document.getElementById('nclex-rationale-panel');
        const contentEl = document.getElementById('nclex-rationale-content');
        if (panel && contentEl) {
            panel.classList.remove('hidden');
            contentEl.innerHTML = `
                <p class="nclex-rationale-text ${correct ? 'text-ward-success' : 'text-ward-danger'}">
                    ${correct ? '✓ Correct' : '✗ Incorrect'} — Correct answer: <strong>${esc(q.options[q.correct_index])}</strong>
                </p>
                <p class="nclex-rationale-text mt-2">${esc(q.rationale)}</p>
                ${q.clinical_judgment_focus ? `<div class="nclex-cj-focus"><strong>Clinical Judgment:</strong> ${esc(q.clinical_judgment_focus)}</div>` : ''}
                ${q.ncj_step ? `<p class="text-xs text-ward-500 mt-2">NCJ Step: ${esc(q.ncj_step)}</p>` : ''}`;
        }

        document.getElementById('nclex-score').textContent = `Score: ${score}/${currentIndex + 1}`;

        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn-primary text-sm mt-4';
        nextBtn.textContent = currentIndex < questions.length - 1 ? 'Next Question →' : 'View Results';
        nextBtn.onclick = () => {
            currentIndex++;
            document.getElementById('nclex-rationale-panel')?.classList.add('hidden');
            renderQuestion();
        };
        contentEl?.appendChild(nextBtn);
    }

    async function init() {
        await loadContent();
        renderTopics();
        const navLink = document.querySelector('.sidebar-link[data-nav="nclex_prep"]');
        if (navLink) navLink.classList.add('active');
    }

    return { init, setMode, setSessionSize, selectCategory, startSession, answer };
})();