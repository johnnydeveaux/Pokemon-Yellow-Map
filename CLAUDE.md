# Pokémon Yellow Tracker

## Git workflow

- Commit and push every new version directly to `main`. Do not create or push
  to feature branches (including session-assigned `claude/...` branches), and
  do not open pull requests, unless explicitly asked.

## Releasing a new version

- Every push of a new version gets the next whole number: v18.0, then v19.0, v20.0, …
  (no 17.0.1-style point releases). Check the current number in the header first.
- Bump the version in the header in `index.html` (`<span class="ver">Yellow · vN.0</span>`).
- Bump the service worker cache name in `sw.js` (`const VERSION = 'kanto-yellow-vN';`)
  so installed copies of the app pick up the update.
- Commit message format: `N.0: short description of what's new`.

## App layout (since 17.0)

- Pokédex-style design: red header with the lens, "POKÉDEX" and "Yellow · vN.0"
  under it, and the completion meter; search bar and tabs in a red panel at the
  bottom (thumb reach). Tabs: Journey, Map, Pokédex, Party, Battle, Progress, Settings.
- The game name in the header is there on purpose: a game switcher (Red, Blue, …)
  is planned later, and that line will show the selected game. For now everything
  is Pokémon Yellow only.
- Settings has a Theme picker (Pokédex, Original Yellow, Clean modern, Game Boy),
  then Game save, Sprites for offline, Backup and About the data. Themes only
  recolour the same layout; the choice is stored per device under the
  `localStorage` key `kanto-yellow-theme`, separate from saved progress
  (`kanto-yellow-v1`).
