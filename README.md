# dalisoft/homebrew-tap

Personal Homebrew tap.

## Install

```sh
brew install dalisoft/tap/<formula>
```

## Formulae

| Formula | Upstream | Version |
|---|---|---|
| `command-code` | CommandCodeAI/command-code | 1.58.1 |
| `cua-driver` | trycua/cua (`cua-driver-rs`) | 0.28.2 |
| `lume` | trycua/cua (`lume`) | 0.5.3 |
| `reason-language-server` | jaredly/reason-language-server | 1.7.13 |

## Uninstall

Formulae have no `zap` stanza (cask-only by Homebrew design). Full removal:

```sh
brew uninstall --force <formula>
```

User data lives outside the keg (`~/.commandcode`,
`~/.cua-driver`, `~/.local/share/lume`) —
see each formula's `caveats`.

## CI

Hourly `autobump.yml` runs `brew bump` and opens a PR on updates.
`ci.yml` runs audit/style/livecheck on push/PR.
