/* The Ward — Service Worker (static ADN site) */
const CACHE = 'ward-static-v1';
const SHELL = [
    '/',
    '/index.html',
    '/nclex-prep.html',
    '/modules/terminology.html',
    '/modules/microbiology.html',
    '/modules/dosage.html',
    '/modules/assessment.html',
    '/modules/mental-health.html',
    '/modules/pathophysiology.html',
    '/modules/med_surg.html',
    '/modules/maternal_newborn.html',
    '/modules/pediatrics.html',
    '/modules/maternal-child.html',
    '/static/css/ward.css',
    '/static/js/ward.js',
    '/static/js/ward-static.js',
    '/static/js/ward-tabs.js',
    '/static/js/data-api.js',
    '/static/js/export-utils.js',
    '/static/manifest.json',
    '/static/images/ward-icon.svg',
    '/static/images/ward-icon-192.png',
];

self.addEventListener('install', (e) => {
    e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL).catch(() => {})));
    self.skipWaiting();
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', (e) => {
    if (e.request.method !== 'GET') return;
    e.respondWith(
        caches.match(e.request).then((cached) => {
            const fetched = fetch(e.request).then((response) => {
                if (response.ok && (e.request.url.includes('/static/') || e.request.url.includes('/data/content/'))) {
                    const clone = response.clone();
                    caches.open(CACHE).then((c) => c.put(e.request, clone));
                }
                return response;
            }).catch(() => cached);
            return cached || fetched;
        })
    );
});