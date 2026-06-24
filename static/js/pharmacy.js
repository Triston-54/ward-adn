/**
 * Pharmacy Track — dashboard utilities
 */
const Pharmacy = {
    async refreshStats() {
        try {
            const res = await fetch('/api/pharmacy/stats');
            if (!res.ok) return;
            return await res.json();
        } catch {
            return null;
        }
    },
};