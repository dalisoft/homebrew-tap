# dalisoft/homebrew-tap

Personal Homebrew tap for upstream projects requesting Homebrew support.
Clean state: all legacy formulae/casks removed on 2026-09-21; only actively
maintained, verifiable packages below are shipped.

## Install

```sh
brew install dalisoft/tap/<formula>
# e.g.
brew install dalisoft/tap/command-code
brew install dalisoft/tap/cua-driver
brew install dalisoft/tap/lume
brew install dalisoft/tap/reason-language-server
```

Direct (auto-tap):

```sh
brew install dalisoft/tap/command-code
```

## Formulae

| Formula | Upstream | Version | Type | Min OS | Notes |
|---|---|---|---|---|---|
| `command-code` | CommandCodeAI/command-code (npm `command-code`) | 1.58.1 | formula (npm) | macOS Monterey+ | `depends_on "node"` (>=22). Bins: `command-code`, `commandcode`, `cmd`, `cmdc`. |
| `cua-driver` | trycua/cua (`cua-driver-rs`) | 0.28.2 | formula (prebuilt binary, per-OS/arch) | macOS Sonoma+ / Linux | Per-arch SHA-256 from `checksums.txt`. CLI only; no `/Applications` writes. |
| `lume` | trycua/cua (`lume`) | 0.5.3 | formula (prebuilt binary, macOS ARM64 only) | macOS Ventura+ (13+), ARM64 | `depends_on :macos`, `arch: :arm64`. CLI only. |
| `reason-language-server` | jaredly/reason-language-server | 1.7.13 | formula (prebuilt zip, per-OS) | macOS / Linux (x86_64-era, Rosetta on ARM) | Deprecated upstream; kept for compatibility. |

All formulae include:

- `desc`, `homepage`, `license`, `version`
- Immutable `url` + `sha256` **per OS/arch** (`on_macos` / `on_linux`, `on_arm` / `on_intel` where needed)
- `depends_on` minimum macOS (`:monterey`, `:sonoma`, `:ventura`) and runtime deps (`node`, `gcc`)
- `livecheck` (live update) with `strategy :npm` or `:github_latest` + tag-prefix regex
- `test do` functional checks (version output, or existence checks for LSP servers that block on stdin)
- `caveats` for login, daemons, Rosetta, deprecation

## Intentionally not packaged

- **penpot/penpot#4792** — server web app (Clojure, Docker Compose: frontend/backend/exporter + Postgres/Redis). No DMG/zip/CLI to package. A cask would be wrong; target would be unofficial `author-more/penpot-desktop` (Electron), not this repo.
- **onivim/oni2#3400** — unmaintained since 2021 (`v0.5.7`, no GitHub Releases assets), commercial-gated DMG via portal/EULA, x86_64-only, no public versioned URL, no livecheck possible. Cask declined on security/correctness grounds.

## Security / correctness

- All `sha256` values verified read-only via `curl -L <URL> | shasum -a 256` or upstream `checksums.txt` / `release-manifest.json`. No `curl | sh` install scripts were executed during authoring.
- Upstream install scripts (`cua.ai/driver/install.sh`, `lume/install.sh`) perform PATH edits, LaunchAgents, `/Applications` moves and telemetry hints — none of that is replicated in formulae.
- `brew audit --strict --online` and `ruby -c` should pass before any push.

## Uninstall / `zap` handling (how Homebrew does it)

**Formulae have no `zap` stanza — this is by Homebrew design, not an omission.**

- `zap` (`def zap` in `Homebrew/cask/installer.rb`, `cask/artifact/zap.rb`) exists only in the **Cask DSL**. The **Formula DSL** (`Formula-Cookbook`, `rubydoc Formula`) defines no `zap`/`uninstall` stanza: a formula installs into its own keg (`/opt/homebrew/Cellar/<name>/<version>`) with symlinks into `bin`, so `brew uninstall --force <formula>` removes everything the formula installed. Verified: `grep def zap` hits only `cask/`, and adding `zap` to a `Formula` fails `brew audit`/`brew style` as an unknown stanza.
- All four packages here are CLI formulae (correct per `Adding-Software-to-Homebrew`: formula for CLI, cask for GUI), so no `zap` applies. Each formula's `caveats` documents **Full uninstall** instead:
  - `brew uninstall --force <formula>` (removes keg + symlinks), plus
  - manual user-data cleanup only where upstream creates it (`~/.commandcode`, `~/.cua-driver`, `~/.local/share/lume`, LaunchAgents from upstream scripts — none created by these formulae).
- If a GUI counterpart is packaged later as a cask (e.g. desktop DMG), it will ship a proper `zap trash:` block (app support, caches, preferences, saved state) following `Cask-Cookbook` (`huly`, `tablepro`, `comfy`, `visual-studio-code` patterns reviewed).

## CI / hourly auto-update

- `ci.yml` (push/PR): `ruby -c`, `brew style`, `brew audit --strict --online --new`, `brew livecheck` sanity.
- `autobump.yml` (hourly `0 * * * *` + manual dispatch): mirrors [`homebrew-core autobump.yml`](https://github.com/Homebrew/homebrew-core/blob/main/.github/workflows/autobump.yml) — container `ghcr.io/homebrew/brew:main`, `Homebrew/actions/setup-homebrew`, `git-user-config`, then `brew bump --no-fork --open-pr --formulae --bump-synced --tap=dalisoft/tap` (bumps `version` + per-OS/arch `sha256`, opens PR). Supports `formulae:` + `dry_run:` inputs.
- Fallback: `.github/scripts/autobump.py` (npm + `cua-driver-rs-v*` / `lume-v*` tag-prefix handling, `checksums.txt` / `release-manifest.json` parsing). Check-only mode: `python3 .github/scripts/autobump.py --check-only`.

## Clean recreation of the origin repo (via `gh`)

Local state is already clean (legacy `*.rb` + `Casks/*` staged for deletion, new `Formula/`, `Casks/.keep`, `README`, `.github/` ready). Remote recreation is destructive (drops history) — confirm before running:

```sh
# 1. Inspect what will be lost (0 stars, 0 forks as of 2026-09-21; issues disabled; last push 2024-10-13)
gh repo view dalisoft/homebrew-tap --json nameWithOwner,stargazerCount,forkCount,pushedAt,visibility

# 2. Delete origin (irreversible — requires confirmation prompt)
gh repo delete dalisoft/homebrew-tap --confirm

# 3. Re-create empty public repo
gh repo create dalisoft/homebrew-tap --public --description "Personal Homebrew tap"

# 4. Push clean state from a fresh clone (from scratch)
git clone https://github.com/dalisoft/homebrew-tap.git homebrew-tap-clean
cp -R /path/to/prepared/Formula /path/to/prepared/Casks /path/to/prepared/README.md /path/to/prepared/.github homebrew-tap-clean/
cd homebrew-tap-clean
git add Formula Casks README.md .github
git commit -m "Re-create tap from scratch: hardened formulae + hourly autobump CI"
git push -u origin HEAD:master
```

## Docs & examples reviewed (mandatory)

Docs: `Formula-Cookbook`, `Cask-Cookbook`, `How-to-Create-and-Maintain-a-Tap`,
`Adding-Software-to-Homebrew`, `Language-Specific-Formulae` (Node.js/npm).

Formulae (6): `dprint`, `cassowary`, `rust-analyzer`, `opencode`, `fnm`, `lazygit`.
Casks (5): `lapce`, `huly`, `tablepro`, `comfy`, `visual-studio-code`.

## Maintenance

```sh
brew audit --strict --online --new dalisoft/tap/<formula>
brew test dalisoft/tap/<formula>
brew livecheck dalisoft/tap/<formula>
```
