#!/bin/bash
set -euo pipefail
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
command -v rsvg-convert >/dev/null || { echo 'Install librsvg for theme previews.' >&2; exit 1; }
stage=/tmp/uconsole-theme
mkdir -p "$HOME/.local/share/uconsole" "$HOME/.config/systemd/user"
install -m644 "$stage/theme-editor.py" "$stage/theme-editor.html" "$HOME/.local/share/uconsole/"
install -m755 "$stage/uconsole-theme-editor" "$HOME/.local/bin/"
cat > "$HOME/.config/systemd/user/uconsole-theme-editor.service" <<'EOF'
[Unit]
Description=uConsole theme colors editor
After=graphical-session.target
PartOf=graphical-session.target
[Service]
ExecStart=/usr/bin/python3 %h/.local/share/uconsole/theme-editor.py
Restart=on-failure
RestartSec=3
[Install]
WantedBy=graphical-session.target
EOF
cat > "$HOME/.local/share/applications/uconsole-theme-editor.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Theme colors
Comment=Choose an accent with a live preview
Exec=uconsole-theme-editor
Icon=preferences-desktop-theme
Categories=Utility;Settings;Accessibility;
Terminal=false
EOF
python3 - <<'PY'
import json
from pathlib import Path
p=Path.home()/'.config/omarchy/extensions/omarchy-menu.jsonc'
data=json.loads(p.read_text())
data['style.uconsole-colors']={'label':'Theme colors','action':'uconsole-theme-editor','description':'Accent colors with live preview'}
p.write_text(json.dumps(data,indent=2)+'\n')
PY
systemctl --user daemon-reload
systemctl --user enable --now uconsole-theme-editor.service
systemctl --user restart uconsole-theme-editor.service
echo UCONSOLE_THEME_EDITOR_INSTALLED
