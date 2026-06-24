/**
 * The Ward — Shared module tab hash routing (back/forward + deep links).
 * Includes accessible tablist keyboard navigation and ARIA sync.
 */
const WardTabs = (() => {
    const routes = new Map();

    /** Normalize module paths so `/modules/foo` matches `/modules/foo.html` (static site). */
    function normalizePath(path) {
        return String(path || '').replace(/\.html$/, '');
    }

    function pathsMatch(currentPath, registeredPath) {
        const current = normalizePath(currentPath);
        const registered = normalizePath(registeredPath);
        return current === registered || currentPath.startsWith(registered + '/') || currentPath.startsWith(registeredPath + '/');
    }

    function getRoute(path) {
        return routes.get(normalizePath(path)) || routes.get(path);
    }

    function register(path, config) {
        routes.set(normalizePath(path), {
            validTabs: config.validTabs || [],
            defaultTab: config.defaultTab || '',
            switchTab: config.switchTab,
        });
    }

    function applyHash(path) {
        const route = getRoute(path);
        if (!route || typeof route.switchTab !== 'function') return;

        const hash = location.hash.replace('#', '');
        if (hash && route.validTabs.includes(hash)) {
            route.switchTab(hash);
        } else if (!hash && route.defaultTab) {
            route.switchTab(route.defaultTab);
        }
    }

    function init(path) {
        applyHash(path);
        window.addEventListener('hashchange', () => {
            if (pathsMatch(location.pathname, path)) {
                applyHash(path);
            }
        });
    }

    /**
     * Navigate to a module tab — in-page switch when already on module, else full navigation.
     */
    function goTo(path, tab, defaultTab) {
        const route = getRoute(path);
        const onModule = pathsMatch(location.pathname, path);
        if (onModule) {
            if (route && route.validTabs.includes(tab) && typeof route.switchTab === 'function') {
                route.switchTab(tab);
                return;
            }
            location.hash = tab;
            return;
        }
        const href = tab && tab !== defaultTab ? `${path}#${tab}` : path;
        location.href = href;
    }

    function syncTablistAria(tablist) {
        const tabs = [...tablist.querySelectorAll('.tab-btn[role="tab"]')];
        tabs.forEach((tab) => {
            const active = tab.classList.contains('active');
            tab.setAttribute('aria-selected', active ? 'true' : 'false');
            tab.setAttribute('tabindex', active ? '0' : '-1');
            if (active) {
                tab.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' });
            }
        });
    }

    function handleTabKeydown(e, tablist) {
        const tabs = [...tablist.querySelectorAll('.tab-btn[role="tab"]')];
        if (!tabs.length) return;

        const current = tabs.findIndex((t) => t.classList.contains('active'));
        let next = current;

        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            e.preventDefault();
            next = (current + 1) % tabs.length;
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            e.preventDefault();
            next = (current - 1 + tabs.length) % tabs.length;
        } else if (e.key === 'Home') {
            e.preventDefault();
            next = 0;
        } else if (e.key === 'End') {
            e.preventDefault();
            next = tabs.length - 1;
        } else {
            return;
        }

        const target = tabs[next];
        target.focus();
        target.click();
    }

    function initTablistA11y(tablist) {
        if (!tablist || tablist.dataset.wardTabsA11y) return;
        tablist.dataset.wardTabsA11y = '1';

        const tabs = [...tablist.querySelectorAll('.tab-btn')];
        tabs.forEach((tab) => {
            tab.setAttribute('role', 'tab');
            const tabId = tab.dataset.tab;
            if (!tabId) return;

            const panelId = `tab-${tabId}`;
            const panel = document.getElementById(panelId);
            const labelId = `tab-label-${tabId}`;

            if (!tab.id) tab.id = labelId;
            tab.setAttribute('aria-controls', panelId);

            if (panel) {
                panel.setAttribute('role', 'tabpanel');
                panel.setAttribute('aria-labelledby', labelId);
            }
        });

        syncTablistAria(tablist);

        const observer = new MutationObserver(() => syncTablistAria(tablist));
        tabs.forEach((tab) => observer.observe(tab, { attributes: true, attributeFilter: ['class'] }));

        tablist.addEventListener('keydown', (e) => handleTabKeydown(e, tablist));
    }

    function enhanceAccessibility() {
        document.querySelectorAll('.module-tabs[role="tablist"]').forEach(initTablistA11y);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', enhanceAccessibility);
    } else {
        enhanceAccessibility();
    }

    return { register, init, goTo, applyHash, enhanceAccessibility, syncTablistAria };
})();