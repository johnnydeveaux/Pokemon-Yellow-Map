// Cache-first service worker so the app runs with no connection.
// Bump VERSION whenever you edit index.html or dex-data.js so phones pick up the change.
const VERSION = 'kanto-yellow-v14';
const SPRITES = 'kanto-sprites'; // Pokémon Yellow sprites, kept across app updates
const FILES = ['./', './index.html', './dex-data.js', './maps-data.js', './maps-img.js', './manifest.webmanifest', './icon-180.png', './icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION && k !== SPRITES).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
// Sprites: look them up by address only, and store them with no "Vary" rules,
// so each sprite is saved exactly once and later saves simply replace it. Nothing is ever deleted.
async function sprite(req) {
  const c = await caches.open(SPRITES);
  const hit = await c.match(req.url, { ignoreVary: true, ignoreSearch: true });
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok) {
    const body = await res.clone().blob();
    c.put(req.url, new Response(body, { headers: { 'Content-Type': 'image/png' } }));
  }
  return res;
}
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  if (e.request.url.includes('/PokeAPI/sprites/')) { e.respondWith(sprite(e.request).catch(() => Response.error())); return; }
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(hit => hit ||
    fetch(e.request).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(e.request, copy)); }
      return res;
    }).catch(() => e.request.mode === 'navigate' ? caches.match('./index.html') : Response.error())));
});
