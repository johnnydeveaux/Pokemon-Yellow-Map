// Offline support for the v16.0.a design preview. It only handles pages inside this folder,
// and only ever looks in (or clears) its own caches, so the main app is never touched.
const PREFIX = 'kanto-yellow-v16a-';
const VERSION = PREFIX + '1';
const SPRITES = 'kanto-sprites'; // shared with the main app: sprites are the same everywhere
const FILES = ['./', './index.html', './manifest.webmanifest', '../dex-data.js', '../maps-data.js', '../maps-img.js', '../icon-180.png', '../icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith(PREFIX) && k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
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
  e.respondWith(caches.open(VERSION).then(c => c.match(e.request, { ignoreSearch: true }).then(hit => hit ||
    fetch(e.request).then(res => {
      if (res.ok) c.put(e.request, res.clone());
      return res;
    }).catch(() => e.request.mode === 'navigate' ? c.match('./index.html') : Response.error()))));
});
