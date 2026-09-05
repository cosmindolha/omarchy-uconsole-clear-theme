#!/bin/bash
set -euo pipefail
export OMARCHY_PATH=/usr/share/omarchy
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
export WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-1}
export DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus
export PATH="$OMARCHY_PATH/bin:$HOME/.local/bin:$PATH"
backup="$HOME/.local/state/uconsole-before-clear"
mkdir -p "$backup"
if [[ ! -f $backup/complete ]]; then
  cp -a "$HOME/.config/hypr" "$HOME/.config/omarchy" "$HOME/.config/alacritty" "$backup/"
  cp "$HOME/.local/state/omarchy/current/theme.name" "$backup/previous-theme"
  touch "$backup/complete"
fi
cp -a /tmp/uconsole-theme/uconsole-clear "$HOME/.config/omarchy/themes/"
mkdir -p "$HOME/.local/bin" "$HOME/.config/omarchy/bar/modules"
install -m755 /tmp/uconsole-theme/uconsole-status "$HOME/.local/bin/"
install -m755 /tmp/uconsole-theme/uconsole-battery "$HOME/.local/bin/"
install -m644 /tmp/uconsole-theme/uconsole-battery.qml "$HOME/.config/omarchy/bar/modules/"
install -m644 /tmp/uconsole-theme/uconsole-workspaces.qml "$HOME/.config/omarchy/bar/modules/"
install -m644 /tmp/uconsole-theme/uconsole-text.qml "$HOME/.config/omarchy/bar/modules/"
install -m644 /tmp/uconsole-theme/shell.json "$HOME/.config/omarchy/shell.json"
panel=$(hyprctl -i 0 -j monitors | python3 -c 'import json,sys; panels=[m["name"] for m in json.load(sys.stdin) if m["name"].startswith("DSI-")]; assert len(panels)==1, "Expected one active uConsole DSI panel"; print(panels[0])')
cat > "$HOME/.config/hypr/monitors.lua" <<EOF
-- ClockworkPi uConsole: 5-inch, 1280x720 landscape; 1024x576 logical.
hl.monitor({ output = "$panel", mode = "preferred", position = "0x0", scale = 1.25, transform = 3 })
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })
hl.env("GDK_SCALE", "1")
EOF
cat > "$HOME/.config/hypr/looknfeel.lua" <<'EOF'
-- uConsole Clear: preserve content area and make focus unmistakable.
hl.config({
  general = { gaps_in = 3, gaps_out = 5, border_size = 2, layout = "scrolling" },
  scrolling = { column_width = 1.0 },
  decoration = { rounding = 4, dim_inactive = false, active_opacity = 1.0, inactive_opacity = 1.0 },
  animations = { enabled = false },
  group = { groupbar = { font_size = 18, height = 28 } },
})
hl.env("XCURSOR_SIZE", "30")
hl.env("HYPRCURSOR_SIZE", "30")
EOF
omarchy-theme-set 'uConsole Clear'
omarchy-display-text-size 20
# Padding should not consume a handheld's terminal width.
sed -i -e 's/padding.x = 14/padding.x = 8/' -e 's/padding.y = 14/padding.y = 8/' "$HOME/.config/alacritty/alacritty.toml"
sed -i 's/style = "Regular"/style = "Medium"/' "$HOME/.config/alacritty/alacritty.toml"
sed -i 's/^pad=14x14$/pad=8x8/' "$HOME/.config/foot/foot.ini"
mkdir -p "$HOME/.config/omarchy/hooks/pre-refresh-pacman.d"
cat > "$HOME/.config/omarchy/hooks/pre-refresh-pacman.d/20-uconsole-kernel" <<'EOF'
#!/bin/bash
# The vendor CM5 kernel lacks Landlock; retain syscall sandboxing and signatures.
if ! grep -q '^DisableSandboxFilesystem' /etc/pacman.conf; then
  sudo sed -i '/^\[options\]/a DisableSandboxFilesystem' /etc/pacman.conf
fi
EOF
chmod +x "$HOME/.config/omarchy/hooks/pre-refresh-pacman.d/20-uconsole-kernel"
hyprctl -i 0 reload
omarchy-shell shell reloadConfig
omarchy-display-text-size
printf 'UCONSOLE_CLEAR_APPLIED\n'
