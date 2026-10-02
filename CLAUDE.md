# Pokémon Yellow Tracker

## Git workflow

- Commit and push every new version directly to `main`. Do not create or push
  to feature branches (including session-assigned `claude/...` branches), and
  do not open pull requests, unless explicitly asked.

## Releasing a new version

- Bump the version label in `index.html` (`<span class="ver">vN.0</span>`).
- Bump the service worker cache name in `sw.js` (`const VERSION = 'kanto-yellow-vN';`)
  so installed copies of the app pick up the update.
- Commit message format: `N.0: short description of what's new`.

## Design previews

- `v16a/`, `v16b/` and `v16c/` are alternative designs (16.0.a, 16.0.b, 16.0.c) of the
  v16.0 app: same features, different theme and layout. Each folder has its own
  `index.html`, `sw.js` and `manifest.webmanifest`, and loads the shared data files
  (`dex-data.js`, `maps-data.js`, `maps-img.js`, icons) from the repo root.
- They share saved progress with the main app (same `localStorage` key), so never
  change the save format in one place only.
- The root `index.html` is the main app; leave it alone when working on a preview.
