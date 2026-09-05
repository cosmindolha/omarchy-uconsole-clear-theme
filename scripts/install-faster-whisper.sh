#!/usr/bin/env bash
# Install the tested CM5 backend and Settings > Dictation UI as the desktop user.
set -euo pipefail
[[ $(uname -m) == aarch64 && $EUID != 0 ]] || { echo 'Run as the ARM64 desktop user.' >&2; exit 1; }
command -v voxtype >/dev/null || { echo 'Install Voxtype first with install-voxtype.sh.' >&2; exit 1; }
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
[[ $(voxtype status) == idle ]] || { echo 'Finish dictation before installing.' >&2; exit 1; }
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../gui" && pwd)
root="$HOME/.local/share/uconsole"
uv_dir="$HOME/.local/share/uconsole-build/uv"
mkdir -p "$root" "$uv_dir" "$HOME/.local/bin" "$HOME/.config/uconsole" "$HOME/.config/systemd/user/voxtype.service.d"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
curl -fLsS --retry 3 https://github.com/astral-sh/uv/releases/download/0.12.10/uv-aarch64-unknown-linux-gnu.tar.gz -o "$work/uv.tar.gz"
echo "9ff6b9d4665edcdd3a88dcc73cd1eb641754deb927f14e8c62ebfde6bf4f5f5e  $work/uv.tar.gz" | sha256sum -c -
tar xf "$work/uv.tar.gz" -C "$uv_dir" --strip-components=1
if [[ ! -x "$root/faster-whisper-venv/bin/python" ]]; then
  "$uv_dir/uv" venv --python 3.12.14 "$root/faster-whisper-venv"
fi
"$uv_dir/uv" pip install --python "$root/faster-whisper-venv/bin/python" -r "$source_dir/faster-whisper-requirements.txt"
"$root/faster-whisper-venv/bin/python" - <<'PY'
from pathlib import Path
from huggingface_hub import snapshot_download
snapshot_download('Systran/faster-whisper-base',revision='ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66',local_dir=Path.home()/'.local/share/uconsole/faster-whisper-base',allow_patterns=['model.bin','config.json','tokenizer.json','vocabulary.*'])
PY
install -m644 "$source_dir/dictation-server.py" "$source_dir/dictation.html" "$source_dir/theme-editor.py" "$root/"
install -m755 "$source_dir/uconsole-dictation-settings" "$HOME/.local/bin/"
install -m644 "$source_dir/uconsole-dictation.service" "$HOME/.config/systemd/user/"
[[ -e "$HOME/.config/uconsole/dictation.json" ]] || echo '{"language":"en"}' > "$HOME/.config/uconsole/dictation.json"
cat > "$HOME/.config/systemd/user/voxtype.service.d/faster-whisper.conf" <<'UNIT'
[Unit]
Wants=uconsole-dictation.service
After=uconsole-dictation.service
UNIT
systemctl --user daemon-reload
systemctl --user enable uconsole-dictation.service
systemctl --user restart uconsole-dictation.service
ready=false
for attempt in {1..30}; do
  if curl -fsS http://127.0.0.1:8769/health > "$work/health.json" 2>/dev/null; then ready=true; break; fi
  sleep 1
done
$ready || { echo 'Backend did not become ready; Voxtype configuration unchanged.' >&2; exit 1; }
backup="$HOME/.config/voxtype/config.toml.before-faster-whisper"
[[ -e $backup ]] || cp "$HOME/.config/voxtype/config.toml" "$backup"
voxtype config set whisper.mode remote
voxtype config set whisper.remote_endpoint http://127.0.0.1:8769
voxtype config set whisper.remote_model base
# The backend uses dictation.json as the language authority, not this cached field.
voxtype config set whisper.language en
voxtype config set whisper.translate false
python3 - <<'PY'
import json,re
from pathlib import Path
p=Path.home()/'.config/omarchy/extensions/omarchy-menu.jsonc'
s=p.read_text() if p.exists() else '{}'
s=re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/',lambda m:m[0] if m[0].startswith('"') else '',s)
s=re.sub(r'"(?:\\.|[^"\\])*"|,(?=\s*[}\]])',lambda m:m[0] if m[0].startswith('"') else '',s)
data=json.loads(s)
data['setup.uconsole-dictation']={'label':'Dictation','aliases':['speech','language','faster-whisper'],'action':'uconsole-dictation-settings','description':'Choose English or Romanian'}
p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n')
PY
systemctl --user restart voxtype uconsole-theme-editor
printf '%s\n' 'Ready: Menu > Setup > Dictation. English is the initial default; 1/E selects English, 2/R Romanian.'
