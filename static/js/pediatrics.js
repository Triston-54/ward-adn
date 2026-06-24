/**
 * The Ward — Pediatric Nursing Module (Static)
 */
const Pediatrics = (() => {
    const VALID_TABS = ['milestones', 'growth', 'immunizations', 'safety', 'flashcards', 'practice'];
    const DEFAULT_TAB = 'milestones';
    const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

    let pedsData = null;
    let flashcards = [];
    let cardIndex = 0;
    let cardFlipped = false;
    let practiceQuestions = [];
    let practiceIndex = 0;
    let practiceCorrect = 0;

    function switchTab(tab) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
        document.querySelectorAll('.mc-tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('tab-' + tab)?.classList.remove('hidden');
        document.querySelector(`[data-tab="${tab}"]`)?.classList.add('active');

        if (tab === 'milestones') loadMilestones();
        if (tab === 'growth') loadGrowth();
        if (tab === 'immunizations') loadImmunizations();
        if (tab === 'safety') loadSafety();
        if (tab === 'flashcards' && !flashcards.length) loadFlashcards();
        if (tab === 'practice' && !practiceQuestions.length) { /* wait for start */ }

        history.replaceState(null, '', location.pathname + (tab !== DEFAULT_TAB ? '#' + tab : ''));
    }

    async function loadData() {
        if (pedsData) return pedsData;
        const res = await fetch('/data/content/maternal_child.json');
        pedsData = await res.json();
        return pedsData;
    }

    function renderCards(el, items, titleKey = 'title') {
        if (!el) return;
        el.innerHTML = (items || []).map(item => {
            const body = item.summary || item.content || '';
            const nursing = item.nursing_action
                || (item.nursing_actions || []).join('; ');
            const clinical = item.clinical_why || '';
            return `
            <details class="mc-topic-card">
                <summary class="font-medium text-ward-100 text-sm">${esc(item[titleKey] || item.age_group)}</summary>
                <div class="px-4 pb-3">
                    ${body ? `<p class="text-sm text-ward-300">${esc(body)}</p>` : ''}
                    ${(item.key_points || []).length ? `<ul class="list-disc pl-5 mt-2 text-xs text-ward-400">${item.key_points.map(k => `<li>${esc(k)}</li>`).join('')}</ul>` : ''}
                    ${nursing ? `<p class="text-xs text-pink-400 mt-2"><strong>Nursing:</strong> ${esc(nursing)}</p>` : ''}
                    ${clinical ? `<p class="text-xs text-ward-accent mt-2">${esc(clinical)}</p>` : ''}
                </div>
            </details>`;
        }).join('') || '<p class="text-ward-500 text-sm">No content available.</p>';
    }

    async function loadMilestones() {
        await loadData();
        const topics = (pedsData.pediatric_essentials || []).filter(t =>
            (t.category || '').match(/milestone|development|growth/i) || (t.title || '').match(/milestone|month|year|development/i)
        );
        renderCards(document.getElementById('peds-milestones-container'), topics.length ? topics : pedsData.pediatric_essentials?.slice(0, 8));
    }

    async function loadGrowth() {
        await loadData();
        const growth = (pedsData.pediatric_essentials || []).filter(t =>
            (t.category || '').match(/growth|nutrition|vital/i)
        );
        const items = growth.length ? growth : (pedsData.pediatric_essentials || []).slice(4, 12);
        renderCards(document.getElementById('peds-growth-container'), items);
    }

    async function loadImmunizations() {
        await loadData();
        const imm = pedsData.immunization_schedule || pedsData.immunizations || [];
        const el = document.getElementById('peds-immunizations-container');
        if (!el) return;
        if (imm.length) {
            el.innerHTML = imm.map(v => `
                <div class="card p-4 mb-2">
                    <div class="flex justify-between"><span class="font-medium text-ward-100 text-sm">${esc(v.vaccine || v.title)}</span>
                    <span class="text-xs text-ward-500">${esc(v.age || v.schedule || '')}</span></div>
                    <p class="text-xs text-ward-400 mt-1">${esc(v.nursing_considerations || v.notes || '')}</p>
                </div>
            `).join('');
        } else {
            const fallback = (pedsData.pediatric_essentials || []).filter(t => (t.title || '').match(/immun|vaccin/i));
            renderCards(el, fallback.length ? fallback : [{ title: 'CDC Immunization Schedule', summary: 'Review CDC recommended childhood immunization schedule. Key vaccines: HepB at birth, DTaP/IPV/MMR series, Varicella, HPV adolescent series.', key_points: ['Document lot number and site', 'Screen for contraindications', 'Observe 15 min post-vaccination'] }]);
        }
    }

    async function loadSafety() {
        await loadData();
        const safety = (pedsData.pediatric_essentials || []).filter(t =>
            (t.category || '').match(/safety|injury|prevention/i) || (t.title || '').match(/safety|injury|SIDS|choking/i)
        );
        const flags = pedsData.safety_red_flags || [];
        const el = document.getElementById('peds-safety-container');
        if (!el) return;
        renderCards(el, safety.length ? safety : flags.filter(f => (f.population || '').match(/ped|child|infant/i)));
    }

    async function loadFlashcards() {
        const front = document.getElementById('pedsfc-front');
        if (front) front.textContent = 'Loading…';
        try {
            await loadData();
            const shuffle = WardData?.shuffleArray || ((a) => [...a].sort(() => Math.random() - 0.5));
            let pool = (pedsData.flashcards || []).filter(c =>
                (c.category || '').match(/ped|child|infant|immun|milestone|Pediatric/i)
            );
            if (!pool.length) {
                pool = (pedsData.pediatric_essentials || []).map(p => ({
                    id: p.id,
                    front: p.title,
                    back: [p.content, ...(p.nursing_actions || [])].filter(Boolean).join(' — '),
                    category: 'Pediatric',
                }));
            }
            flashcards = shuffle([...pool]).slice(0, 15);
        } catch (err) {
            console.error('[Pediatrics] flashcard load failed:', err);
            if (front) front.textContent = 'Could not load flashcards.';
            showToast('Flashcard load failed.', 'error');
            return;
        }
        cardIndex = 0;
        cardFlipped = false;
        renderCard();
    }

    function renderCard() {
        const front = document.getElementById('pedsfc-front');
        const back = document.getElementById('pedsfc-back');
        const counter = document.getElementById('pedsfc-counter');
        if (!flashcards.length) return;
        const c = flashcards[cardIndex];
        if (front) { front.textContent = c.front; front.classList.toggle('hidden', cardFlipped); }
        if (back) { back.textContent = c.back; back.classList.toggle('hidden', !cardFlipped); }
        if (counter) counter.textContent = `${cardIndex + 1}/${flashcards.length}`;
    }

    function flipCard() { cardFlipped = !cardFlipped; renderCard(); }
    function nextCard() { if (cardIndex < flashcards.length - 1) { cardIndex++; cardFlipped = false; renderCard(); } }
    function prevCard() { if (cardIndex > 0) { cardIndex--; cardFlipped = false; renderCard(); } }

    async function startPractice(count) {
        const res = await fetch(`/api/maternal-child/practice?count=${count}`);
        const data = await res.json();
        practiceQuestions = (data.questions || []).filter(q => (q.category || '').match(/ped|child|infant|growth|immun/i) || true);
        if (!practiceQuestions.length) practiceQuestions = data.questions || [];
        practiceIndex = 0;
        practiceCorrect = 0;
        renderPractice();
    }

    function renderPractice() {
        const area = document.getElementById('peds-practice-area');
        if (!area) return;
        if (practiceIndex >= practiceQuestions.length) {
            area.innerHTML = `<p class="text-ward-success text-sm">Complete! ${practiceCorrect}/${practiceQuestions.length}</p>`;
            return;
        }
        const q = practiceQuestions[practiceIndex];
        area.innerHTML = `
            <p class="text-sm text-ward-100 mb-3">${esc(q.question || q.stem)}</p>
            ${(q.options || []).map((opt, i) => `
                <button class="btn-secondary w-full text-left text-sm mb-2" onclick="Pediatrics.answerPractice(${i})">${esc(opt)}</button>
            `).join('')}`;
    }

    function answerPractice(idx) {
        const q = practiceQuestions[practiceIndex];
        if (idx === q.correct_index) practiceCorrect++;
        const area = document.getElementById('peds-practice-area');
        area.innerHTML += `<p class="text-xs text-ward-accent mt-2">${esc(q.rationale || q.explanation || '')}</p>`;
        setTimeout(() => { practiceIndex++; renderPractice(); }, 2000);
    }

    function init() {
        const hash = location.hash.replace('#', '');
        loadMilestones();
        const navLink = document.querySelector('.sidebar-link[data-nav="pediatrics"]');
        if (navLink) navLink.classList.add('active');
        if (hash && VALID_TABS.includes(hash)) switchTab(hash);
    }

    return { init, switchTab, flipCard, nextCard, prevCard, startPractice, answerPractice };
})();