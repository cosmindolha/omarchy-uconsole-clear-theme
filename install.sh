#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $EUID != 0 ]] || { echo 'Run this as your desktop user; sudo is requested only for the backlight rule.' >&2; exit 1; }
export OMARCHY_PATH=/usr/share/omarchy
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
export PATH="$OMARCHY_PATH/bin:$HOME/.local/bin:$PATH"
for command in hyprctl python3 rsvg-convert xkbcli omarchy-theme-set omarchy-display-text-size; do
  command -v "$command" >/dev/null || { echo "Missing dependency: $command" >&2; exit 1; }
done
hyprctl -i 0 version | head -1
hyprctl -i 0 -j monitors | python3 -c 'import json,sys; m=json.load(sys.stdin); assert sum(x["name"].startswith("DSI-") for x in m)==1, "One active DSI panel is required"'
id -nG | tr ' ' '\n' | grep -qx video || { echo 'Your user must be in the video group for the backlight keys.' >&2; exit 1; }
if [[ ${1:-} == --check ]]; then echo 'Preflight passed; no settings changed.'; exit 0; fi
[[ $# == 0 ]] || { echo 'Usage: ./install.sh [--check]' >&2; exit 1; }
previous=$(cat "$HOME/.local/state/omarchy/current/theme.name")
stage=/tmp/uconsole-theme
if [[ -e $stage ]]; then
  [[ -d $stage && ! -L $stage && -O $stage ]] || { echo 'Staging path is not an owned directory.' >&2; exit 1; }
else
  mkdir -m700 "$stage"
fi
mkdir -p "$stage/uconsole-clear/backgrounds"
install -m644 "$repo/colors.toml" "$repo/shell.toml" "$repo/icons.theme" "$repo/preview.png" "$stage/uconsole-clear/"
cp -a "$repo/backgrounds/." "$stage/uconsole-clear/backgrounds/"
for source in "$repo"/gui/* "$repo"/scripts/*; do
  [[ -f $source ]] || continue
  cp -- "$source" "$stage/"
done
bash "$stage/apply-readable-theme.sh"
bash "$stage/apply-keyboard.sh"
bash "$stage/apply-theme-editor.sh"
bash "$stage/apply-screensaver.sh"
case "$previous" in uconsole-clear*) omarchy-theme-set "$previous" ;; esac
omarchy-restart-shell
echo 'Installed. Alt+K opens the guide. Menu > Style > Theme colors opens the editor.'
