#!/bin/bash
set -euo pipefail
stage=/tmp/uconsole-theme
install -m755 "$stage/uconsole-screensaver" "$HOME/.local/bin/"
python3 - <<'PY'
from pathlib import Path
import json
home=Path.home()
source=Path('/usr/share/omarchy/bin/omarchy-launch-screensaver').read_text()
needle='-e omarchy-screensaver'
if needle not in source: raise SystemExit('Screensaver launcher changed; review integration.')
source=source.replace(needle,'-e uconsole-screensaver')
source=source.replace('# Exit early if screensaver is already running', '''# Fail before opening a fullscreen terminal if the renderer is unavailable.
if ! command -v ttfx >/dev/null; then
  omarchy-notification-send "Screensaver unavailable" "Install ttfx using the uConsole toolkit instructions."
  exit 1
fi
# Exit early if screensaver is already running''',1)
out=home/'.local/bin/uconsole-launch-screensaver'
out.write_text(source);out.chmod(0o755)
p=home/'.config/omarchy/extensions/omarchy-menu.jsonc'
data=json.loads(p.read_text())
data['system.screensaver']={'label':'Screensaver','action':'uconsole-launch-screensaver force'}
p.write_text(json.dumps(data,indent=2)+'\n')
PY
echo UCONSOLE_SCREENSAVER_INSTALLED
