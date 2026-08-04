/**
 * Offline Sales Service Worker
 *
 * Provides offline support for the Offline Sales application by caching
 * essential application resources and serving them when network connectivity
 * is unavailable.
 */
const CACHE_NAME = 'offline-sale-v19';
const UI_URL = '/offline_sale/ui';

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll([
                UI_URL,
                '/offline_sale/manifest.json',
            ]);
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

self.addEventListener('fetch', (event) => {
    // Only handle GET requests and http/https schemes
    if (event.request.method !== 'GET') return;
    if (!event.request.url.startsWith('http')) return;

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // If the response is valid, clone it and save it to the cache
                if (response.ok) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // If network fails, try to serve from cache
                return caches.match(event.request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // Handle specifically the root UI
                    if (event.request.url.includes(UI_URL)) {
                        return caches.match(UI_URL);
                    }
                });
            })
    );
});
