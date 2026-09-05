#!/bin/bash
# Build upstream ttfx natively; no x86 binary or emulation is used.
set -euo pipefail
[[ $(uname -m) == aarch64 ]] || { echo 'This build recipe targets the ARM64 uConsole.' >&2; exit 1; }
for tool in cargo git cc; do command -v "$tool" >/dev/null || { echo "Install $tool before building ttfx." >&2; exit 1; }; done
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
git clone --depth 1 --branch v0.3.2 https://github.com/omacom-io/ttfx.git "$work/ttfx"
cd "$work/ttfx"
[[ $(git rev-parse HEAD) == 7203e354498462064b7c0a89375051f65cf2ce99 ]]
cargo build --release --locked
./target/release/ttfx --version
sudo install -m755 target/release/ttfx /usr/local/bin/ttfx
sudo install -Dm644 LICENSE /usr/local/share/licenses/ttfx/LICENSE
echo 'ttfx 0.3.2 installed in /usr/local/bin. Rebuild explicitly for future updates.'
