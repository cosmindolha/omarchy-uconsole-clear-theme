#!/usr/bin/env bash
# Optional official ARM64 CPU Voxtype installation; run as the desktop user.
set -euo pipefail
[[ $(uname -m) == aarch64 ]] || { echo 'This installer requires ARM64 Linux.' >&2; exit 1; }
[[ $EUID != 0 ]] || { echo 'Run as the desktop user, not root.' >&2; exit 1; }
for cmd in curl sha256sum sudo systemctl wtype; do command -v "$cmd" >/dev/null || { echo "Missing dependency: $cmd" >&2; exit 1; }; done
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
curl -fL --retry 3 https://github.com/peteonrails/voxtype/releases/download/v1.0.1/voxtype-1.0.1-linux-aarch64-cpu -o "$work/voxtype"
echo "b5e31a85aaa952d1a78c12b8a16ba5cbdcd92eb31adc7d1a908f3c9d06edd4f1  $work/voxtype" | sha256sum -c -
sudo install -m755 "$work/voxtype" /usr/local/bin/voxtype
mkdir -p "$HOME/.config/voxtype"
if [[ ! -f "$HOME/.config/voxtype/config.toml" ]]; then
  cat > "$HOME/.config/voxtype/config.toml" <<'CONFIG'
state_file = "auto"
[hotkey]
enabled = false
[audio]
device = "default"
sample_rate = 16000
max_duration_secs = 60
pause_media = true
[whisper]
model = "base"
language = "auto"
threads = 4
[output]
mode = "type"
fallback_to_clipboard = true
type_delay_ms = 1
CONFIG
fi
voxtype setup --download --model base --no-post-install
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
voxtype setup systemd
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python3 -c 'import evdev' || { echo 'Install python-evdev for the gamepad shortcut.' >&2; exit 1; }
mkdir -p "$HOME/.local/bin" "$HOME/.config/systemd/user"
install -m755 "$script_dir/../gui/uconsole-dictation-button" "$HOME/.local/bin/"
install -m644 "$script_dir/../gui/uconsole-dictation-button.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable uconsole-dictation-button.service
systemctl --user restart uconsole-dictation-button.service
hyprctl reload || true
voxtype info devices
echo 'Installed. With the Clear keyboard toolkit: Hold gamepad A to record; release to transcribe. Left Alt+D also toggles dictation. Connect a microphone and select it as the default input. Existing Voxtype settings are retained.'
