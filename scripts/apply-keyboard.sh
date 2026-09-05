#!/bin/bash
set -euo pipefail
export LANG=en_US.UTF-8 OMARCHY_PATH=/usr/share/omarchy
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)} WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-1}
export PATH="$OMARCHY_PATH/bin:$HOME/.local/bin:$PATH"
stage=/tmp/uconsole-theme
backup="$HOME/.local/state/uconsole-before-keyboard"
mkdir -p "$backup" "$HOME/.local/share/uconsole" "$HOME/.local/share/applications"
if [[ ! -f $backup/complete ]]; then
  cp -a "$HOME/.config/hypr" "$backup/"
  touch "$backup/complete"
fi
install -m644 "$stage/uconsole.xkb" "$stage/uconsole-keyboard.lua" "$HOME/.config/hypr/"
xkbcli compile-keymap --keymap "$HOME/.config/hypr/uconsole.xkb" --test
install -m755 "$stage/uconsole-brightness" "$stage/uconsole-keyboard-help" "$stage/uconsole-activity" "$HOME/.local/bin/"
sudo install -m644 "$stage/90-uconsole-backlight.rules" /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=backlight --action=add
sudo udevadm settle
install -m644 "$stage/keyboard.html" "$HOME/.local/share/uconsole/keyboard.html"
python3 "$stage/install-keyboard-menu.py"
if ! grep -q '^require("hypr.uconsole-keyboard")' "$HOME/.config/hypr/bindings.lua"; then
  printf '\n-- uConsole physical-key overrides and visual guide.\nrequire("hypr.uconsole-keyboard")\n' >> "$HOME/.config/hypr/bindings.lua"
fi
cat > "$HOME/.local/share/applications/uconsole-keys.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=uConsole Keys
Comment=Learn shortcuts on a drawing of your keyboard
Exec=uconsole-keyboard-help
Icon=input-keyboard
Categories=Utility;Accessibility;
Terminal=false
EOF
hyprctl -i 0 reload
errors=$(hyprctl -i 0 configerrors)
if [[ -n $errors ]]; then printf '%s\n' "$errors" >&2; exit 1; fi
echo UCONSOLE_KEYBOARD_APPLIED
