# Pokémon Yellow Tracker

## Git workflow

- Commit and push every new version directly to `main`. Do not create or push
  to feature branches (including session-assigned `claude/...` branches), and
  do not open pull requests, unless explicitly asked.

## Releasing a new version

- Versions now use three numbers (17.0.0 onwards).
- Bump the version in the header in `index.html` (`<span class="ver">Yellow · vX.Y.Z</span>`).
- Bump the service worker cache name in `sw.js` (`const VERSION = 'kanto-yellow-vN';`)
  so installed copies of the app pick up the update.
- Commit message format: `X.Y.Z: short description of what's new`.

## App layout (since 17.0.0)

- Pokédex-style design: red header with the lens, "POKÉDEX" and "Yellow · vX.Y.Z"
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
