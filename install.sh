#!/bin/sh
# Set yogo up on this Mac: hidapi, the venv, the Claude Code hooks, the daemon.
#
#   ./install.sh              # from wherever the repo was unpacked
#   ./install.sh --no-start   # everything but starting the daemon
#
# Safe to run again: the Claude Code hooks are merged into
# ~/.claude/settings.json, replacing any earlier yogo hooks and keeping every
# other setting. The file is backed up first.
set -eu

REPO=$(cd "$(dirname "$0")" && pwd)
SETTINGS="$HOME/.claude/settings.json"
TEMPLATE="$REPO/adapters/claude-code/settings-hooks.json"
START=1
[ "${1:-}" = "--no-start" ] && START=0

say() { printf '==> %s\n' "$*"; }
die() { printf 'install: %s\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = Darwin ] || die "macOS only"
command -v brew >/dev/null 2>&1 || die "Homebrew is needed for hidapi: https://brew.sh"

brew list --formula hidapi >/dev/null 2>&1 || { say "installing hidapi"; brew install hidapi; }
command -v jq >/dev/null 2>&1 || { say "installing jq"; brew install jq; }

# The CLT python3 is 3.9; yogo needs 3.10+.
PY=
for c in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1 &&
        "$c" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
        PY=$(command -v "$c")
        break
    fi
done
if [ -z "$PY" ]; then
    say "installing python"
    brew install python
    PY="$(brew --prefix)/bin/python3"
fi

# A venv does not survive being moved, so rebuild one that no longer runs.
VPY="$REPO/.venv/bin/python"
if ! "$VPY" -m pip --version >/dev/null 2>&1; then
    say "creating venv with $PY"
    rm -rf "$REPO/.venv"
    "$PY" -m venv "$REPO/.venv"
fi
say "installing python packages"
"$VPY" -m pip install -q --disable-pip-version-check -r "$REPO/requirements.txt"
"$REPO/bin/yogo" --help >/dev/null || die "bin/yogo does not run"

# Hooks name the repo as ${YOGO_REPO:-$HOME/Yogo}; pin the real path when the
# repo lives anywhere else.
DIR=
[ "$REPO" = "$HOME/Yogo" ] || DIR=$REPO

mkdir -p "$(dirname "$SETTINGS")"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
jq -e . "$SETTINGS" >/dev/null 2>&1 || die "$SETTINGS is not valid JSON; fix it first"
BACKUP="$SETTINGS.bak-$(date +%Y%m%d%H%M%S)"
cp "$SETTINGS" "$BACKUP"

TMP="$SETTINGS.yogo.$$"
jq --slurpfile t "$TEMPLATE" --arg dir "$DIR" '
  ($t[0].hooks
   | if $dir == "" then .
     else walk(if type == "string"
               then gsub("\\$\\{YOGO_REPO:-\\$HOME/Yogo\\}"; $dir) else . end)
     end) as $yogo
  | .hooks = (reduce ($yogo | keys[]) as $ev (.hooks // {};
      .[$ev] = ([(.[$ev] // [])[]
                 | select(any(.hooks[]?; (.command // "") | test("yogo-signal|bin/yogo")) | not)]
                + $yogo[$ev])))
' "$SETTINGS" > "$TMP" && jq -e . "$TMP" >/dev/null && mv "$TMP" "$SETTINGS" || {
    rm -f "$TMP"
    die "could not merge the hooks; $SETTINGS is unchanged"
}
say "Claude Code hooks merged into $SETTINGS (backup: $BACKUP)"

if [ "$START" = 1 ]; then
    "$REPO/bin/yogo" daemon --stop >/dev/null 2>&1 || true
    "$REPO/bin/yogo" daemon --idle breathe
fi

say "done. Restart Claude Code (or open /hooks once) so it loads the hooks."
