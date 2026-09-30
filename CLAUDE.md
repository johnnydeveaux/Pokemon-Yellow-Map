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
