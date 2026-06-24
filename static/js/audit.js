/**
 * Content Audit — verify concepts/calculations and flag items for review.
 */
const ContentAudit = (() => {
    const PAGE_SIZE = 50;
    let offset = 0;
    let total = 0;
    let modules = {};
    let searchTimer = null;
    let activeItem = null;

    function itemUrl(moduleId, itemKey, action = '') {
        const base = `/api/audit/items/${encodeURIComponent(moduleId)}/${encodeURIComponent(itemKey)}`;
        return action ? `${base}/${action}` : base;
    }

    function statusLabel(status) {
        const labels = {
            unreviewed: 'Unreviewed',
            verified: 'Verified',
            needs_review: 'Needs Review',
        };
        return labels[status] || status;
    }

    function moduleLabel(moduleId) {
        return modules[moduleId] || moduleId;
    }

    async function loadSummary() {
        try {
            const res = await fetch('/api/audit/summary');
            if (!res.ok) throw new Error('summary failed');
            const data = await res.json();
            modules = data.modules || modules;

            const verified = data.verified ?? 0;
            const flagged = data.needs_review ?? 0;
            const unreviewed = data.unreviewed ?? 0;
            const catalogTotal = data.total ?? 0;

            const el = (id) => document.getElementById(id);
            if (el('audit-stat-verified')) el('audit-stat-verified').textContent = verified;
            if (el('audit-stat-flagged')) el('audit-stat-flagged').textContent = flagged;
            if (el('audit-stat-unreviewed')) el('audit-stat-unreviewed').textContent = unreviewed;

            const pct = catalogTotal ? Math.round((verified / catalogTotal) * 100) : 0;
            if (el('audit-coverage-bar')) el('audit-coverage-bar').style.width = `${pct}%`;
            if (el('audit-coverage-pct')) el('audit-coverage-pct').textContent = `${pct}% verified`;
        } catch {
            showToast('Could not load audit summary.', 'error');
        }
    }

    function getFilters() {
        return {
            module_id: document.getElementById('audit-filter-module')?.value || '',
            status: document.getElementById('audit-filter-status')?.value || '',
            item_type: document.getElementById('audit-filter-type')?.value || '',
            search: document.getElementById('audit-filter-search')?.value?.trim() || '',
        };
    }

    function renderItems(items) {
        const container = document.getElementById('audit-items-list');
        if (!container) return;

        if (!items.length) {
            container.innerHTML = '<p class="text-ward-500 text-sm p-5">No items match the current filters.</p>';
            return;
        }

        container.innerHTML = items.map((item) => {
            const noteBlock = item.status === 'verified' && item.source_note
                ? `<div class="audit-item-note"><span class="text-ward-success font-medium">Source:</span> ${escapeHtml(item.source_note)}${item.verified_date ? ` · ${escapeHtml(item.verified_date)}` : ''}</div>`
                : item.status === 'needs_review' && item.review_note
                    ? `<div class="audit-item-note" style="border-left-color:#fbbf24"><span class="text-ward-warning font-medium">Review:</span> ${escapeHtml(item.review_note)}</div>`
                    : '';

            const clearBtn = item.status !== 'unreviewed'
                ? `<button type="button" class="audit-action-btn clear" data-action="clear" data-module="${escapeHtml(item.module_id)}" data-key="${escapeHtml(item.item_key)}">Reset</button>`
                : '';

            return `
                <div class="audit-item" data-module="${escapeHtml(item.module_id)}" data-key="${escapeHtml(item.item_key)}">
                    <div class="audit-item-main">
                        <div class="audit-item-title">${escapeHtml(item.title)}</div>
                        ${item.subtitle ? `<div class="audit-item-subtitle">${escapeHtml(item.subtitle)}</div>` : ''}
                        <div class="audit-item-meta">
                            <span class="audit-badge module">${escapeHtml(moduleLabel(item.module_id))}</span>
                            <span class="audit-badge type">${escapeHtml(item.item_type)}</span>
                            <span class="audit-badge status-${item.status}">${escapeHtml(statusLabel(item.status))}</span>
                            <span class="text-[10px] text-ward-600 font-mono">${escapeHtml(item.item_key)}</span>
                        </div>
                        ${noteBlock}
                    </div>
                    <div class="audit-actions">
                        <button type="button" class="audit-action-btn verify" data-action="verify" data-module="${escapeHtml(item.module_id)}" data-key="${escapeHtml(item.item_key)}" data-title="${escapeHtml(item.title)}">Verify</button>
                        <button type="button" class="audit-action-btn flag" data-action="flag" data-module="${escapeHtml(item.module_id)}" data-key="${escapeHtml(item.item_key)}" data-title="${escapeHtml(item.title)}">Flag</button>
                        ${clearBtn}
                    </div>
                </div>
            `;
        }).join('');

        container.querySelectorAll('[data-action]').forEach((btn) => {
            btn.addEventListener('click', () => {
                const { action, module, key, title } = btn.dataset;
                if (action === 'verify') openVerifyModal(module, key, title);
                else if (action === 'flag') openFlagModal(module, key, title);
                else if (action === 'clear') clearItem(module, key);
            });
        });
    }

    function updatePagination() {
        const pageInfo = document.getElementById('audit-page-info');
        const prevBtn = document.getElementById('audit-prev-btn');
        const nextBtn = document.getElementById('audit-next-btn');

        const start = total ? offset + 1 : 0;
        const end = Math.min(offset + PAGE_SIZE, total);
        if (pageInfo) pageInfo.textContent = total ? `${start}–${end} of ${total}` : '0 items';
        if (prevBtn) prevBtn.disabled = offset <= 0;
        if (nextBtn) nextBtn.disabled = offset + PAGE_SIZE >= total;
    }

    async function loadItems(resetOffset = false) {
        if (resetOffset) offset = 0;

        const container = document.getElementById('audit-items-list');
        if (container) container.innerHTML = '<p class="text-ward-500 text-sm p-5">Loading…</p>';

        const filters = getFilters();
        const params = new URLSearchParams({
            limit: String(PAGE_SIZE),
            offset: String(offset),
        });
        if (filters.module_id) params.set('module_id', filters.module_id);
        if (filters.status) params.set('status', filters.status);
        if (filters.item_type) params.set('item_type', filters.item_type);
        if (filters.search) params.set('search', filters.search);

        try {
            const res = await fetch(`/api/audit/items?${params}`);
            if (!res.ok) throw new Error('items failed');
            const data = await res.json();
            modules = data.modules || modules;
            total = data.total ?? 0;
            renderItems(data.items || []);
            updatePagination();
        } catch {
            if (container) container.innerHTML = '<p class="text-ward-danger text-sm p-5">Failed to load audit catalog.</p>';
            showToast('Could not load audit items.', 'error');
        }
    }

    function debounceSearch() {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => loadItems(true), 300);
    }

    function prevPage() {
        if (offset <= 0) return;
        offset = Math.max(0, offset - PAGE_SIZE);
        loadItems();
    }

    function nextPage() {
        if (offset + PAGE_SIZE >= total) return;
        offset += PAGE_SIZE;
        loadItems();
    }

    function openVerifyModal(moduleId, itemKey, title) {
        activeItem = { module_id: moduleId, item_key: itemKey, title };
        const modal = document.getElementById('audit-verify-modal');
        const titleEl = document.getElementById('audit-verify-title');
        const sourceEl = document.getElementById('audit-verify-source');
        if (titleEl) titleEl.textContent = title || itemKey;
        if (sourceEl) sourceEl.value = '';
        modal?.classList.remove('hidden');
    }

    function closeVerifyModal() {
        document.getElementById('audit-verify-modal')?.classList.add('hidden');
        activeItem = null;
    }

    async function submitVerify() {
        if (!activeItem) return;
        const verifiedDate = document.getElementById('audit-verify-date')?.value?.trim() || '2026-06';
        const sourceNote = document.getElementById('audit-verify-source')?.value?.trim() || null;

        try {
            const res = await fetch(itemUrl(activeItem.module_id, activeItem.item_key, 'verify'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ verified_date: verifiedDate, source_note: sourceNote }),
            });
            if (!res.ok) throw new Error('verify failed');
            closeVerifyModal();
            showToast('Item marked verified.', 'success');
            await Promise.all([loadSummary(), loadItems()]);
        } catch {
            showToast('Could not save verification.', 'error');
        }
    }

    function openFlagModal(moduleId, itemKey, title) {
        activeItem = { module_id: moduleId, item_key: itemKey, title };
        const titleEl = document.getElementById('audit-flag-title');
        const noteEl = document.getElementById('audit-flag-note');
        if (titleEl) titleEl.textContent = title || itemKey;
        if (noteEl) noteEl.value = '';
        document.getElementById('audit-flag-modal')?.classList.remove('hidden');
    }

    function closeFlagModal() {
        document.getElementById('audit-flag-modal')?.classList.add('hidden');
        activeItem = null;
    }

    async function submitFlag() {
        if (!activeItem) return;
        const reviewNote = document.getElementById('audit-flag-note')?.value?.trim();
        if (!reviewNote) {
            showToast('Add a review note before flagging.', 'error');
            return;
        }

        try {
            const res = await fetch(itemUrl(activeItem.module_id, activeItem.item_key, 'flag'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ review_note: reviewNote }),
            });
            if (!res.ok) throw new Error('flag failed');
            closeFlagModal();
            showToast('Item flagged for review.', 'success');
            await Promise.all([loadSummary(), loadItems()]);
        } catch {
            showToast('Could not flag item.', 'error');
        }
    }

    async function clearItem(moduleId, itemKey) {
        if (!confirm('Reset this item to unreviewed?')) return;

        try {
            const res = await fetch(itemUrl(moduleId, itemKey), { method: 'DELETE' });
            if (!res.ok) throw new Error('clear failed');
            showToast('Audit status cleared.', 'success');
            await Promise.all([loadSummary(), loadItems()]);
        } catch {
            showToast('Could not clear audit status.', 'error');
        }
    }

    function init() {
        loadSummary();
        loadItems();
    }

    return {
        init,
        loadItems,
        debounceSearch,
        prevPage,
        nextPage,
        openVerifyModal,
        closeVerifyModal,
        submitVerify,
        openFlagModal,
        closeFlagModal,
        submitFlag,
        clearItem,
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('audit-items-list')) {
        ContentAudit.init();
    }
});