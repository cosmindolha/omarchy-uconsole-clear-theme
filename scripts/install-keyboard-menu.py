"""Use the supported user menu extension and a user-owned full-list helper."""
from pathlib import Path
import json
import re
import shutil

home = Path.home()
menu = home / '.config/omarchy/extensions/omarchy-menu.jsonc'
backup = home / '.local/state/uconsole-before-keyboard/menu.jsonc'
if menu.exists() and not backup.exists():
    shutil.copy2(menu, backup)
source = menu.read_text() if menu.exists() else '{}'
# Strip JSONC comments and trailing commas while retaining quoted strings.
source = re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/', lambda m: m[0] if m[0].startswith('"') else '', source)
source = re.sub(r'"(?:\\.|[^"\\])*"|,(?=\s*[}\]])', lambda m: m[0] if m[0].startswith('"') else '', source)
data = json.loads(source)
data['learn.keybindings'] = {'label':'uConsole keyboard','action':'uconsole-keyboard-help','description':'Physical key diagram and shortcuts'}
data['learn.all-keybindings'] = {'label':'All keybindings','action':'uconsole-keybindings-all','description':'Complete live shortcut list'}
menu.parent.mkdir(parents=True, exist_ok=True)
menu.write_text(json.dumps(data, indent=2)+'\n')

# RC1's source scanner returns a table for unknown hl functions; qconsole now
# probes an active monitor at load time, so the scan stops before all bindings.
# Keep the package file untouched and make a compatible copy for this device.
upstream = Path('/usr/share/omarchy/bin/omarchy-menu-keybindings').read_text()
needle = '  get_config = function()\n'
if needle not in upstream:
    raise SystemExit('Keybinding scanner changed; review compatibility patch')
patched = upstream.replace(needle, '  get_active_monitor = function() return nil end,\n'+needle, 1)
mask_needle = "    64) printf 'SUPER' ;;"
if mask_needle not in patched:
    raise SystemExit('Keybinding modifier decoder changed; review compatibility patch')
patched = patched.replace(mask_needle, "    32) printf 'MOD3' ;;\n" + mask_needle, 1)
patched = patched.replace("printf 'v13\\n'", "printf 'v13-uconsole-v2\\n'")
patched = patched.replace('key_combo = $1 " + " $2;', 'key_combo = $1 " + " $2;\n    gsub(/SUPER/, "Right Alt", key_combo);\n    gsub(/MOD3/, "Speaker", key_combo);')
helper = home / '.local/bin/uconsole-keybindings-all'
helper.write_text(patched)
helper.chmod(0o755)
