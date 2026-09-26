// Cache-first service worker so the app runs with no connection.
// Bump VERSION whenever you edit index.html or dex-data.js so phones pick up the change.
const VERSION = 'kanto-yellow-v3';
const SPRITES = 'kanto-sprites'; // Pokémon Yellow sprites, kept across app updates
const FILES = ['./', './index.html', './dex-data.js', './manifest.webmanifest', './icon-180.png', './icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION && k !== SPRITES).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const isSprite = e.request.url.includes('/PokeAPI/sprites/');
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(hit => hit ||
    fetch(e.request).then(res => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(isSprite ? SPRITES : VERSION).then(c => c.put(e.request, copy));
      }
      return res;
    }).catch(() => e.request.mode === 'navigate' ? caches.match('./index.html') : Response.error())));
});
