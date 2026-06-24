/**
 * The Ward — Static site overrides (loaded after ward.js)
 * Disables socratic/progress/audit; ensures no pharmacy track surfaces in the UI.
 */
(function () {
    // No-op progress (static site)
    window.syncProgress = async function () {
        showToast('Progress tracking is disabled in the static study site.');
    };

    window.openSocraticMode = function () {
        showToast('Socratic tutor is not available in the static study site.', 'error');
    };
    window.closeSocraticModal = function () {};
    window.clearSocraticHistory = function () {};
    window.submitSocratic = function () {};
    window.askSocraticIntent = function () {};

    // Filter command palette: remove pharmacy track, socratic, sync, audit
    const REMOVE_CMD = /pharmacy|socratic|sync|audit|content-audit|naplex|mpje|pharmd/i;
    const origGetAll = getAllCommands;
    getAllCommands = function () {
        return origGetAll().filter(c => {
            const blob = [c.id, c.name, c.section, c.keywords].filter(Boolean).join(' ');
            return !REMOVE_CMD.test(blob);
        });
    };

    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 's') {
            e.preventDefault();
            e.stopImmediatePropagation();
        }
    }, true);
})();