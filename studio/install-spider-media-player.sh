#!/usr/bin/env bash
set -Eeuo pipefail

ZIP="${1:-${HOME}/Downloads/Spider-Media-Player-7.5.0-Kabel-Linux-x64-NORMALIZED.zip}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

if [[ ! -f "$ZIP" ]]; then
    echo "Spider Media Player package not found:"
    echo "  $ZIP"
    echo
    echo "Usage:"
    echo "  $0 /path/to/Spider-Media-Player-7.5.0-Kabel-Linux-x64-NORMALIZED.zip"
    exit 1
fi

command -v unzip >/dev/null || {
    echo "Installing unzip…"
    sudo apt-get update
    sudo apt-get install -y unzip
}

echo "Extracting Spider Media Player…"
unzip -q "$ZIP" -d "$STAGE"

SOURCE="$STAGE/linux-unpacked"
if [[ ! -x "$SOURCE/spider-media-player" ]]; then
    chmod +x "$SOURCE/spider-media-player"
fi

echo "Installing to /opt/spider-media-player…"
sudo rm -rf /opt/spider-media-player
sudo install -d /opt/spider-media-player
sudo cp -a "$SOURCE/." /opt/spider-media-player/
sudo chmod 755 /opt/spider-media-player/spider-media-player

if [[ -f /opt/spider-media-player/chrome-sandbox ]]; then
    sudo chown root:root /opt/spider-media-player/chrome-sandbox
    sudo chmod 4755 /opt/spider-media-player/chrome-sandbox
fi

sudo ln -sfn /opt/spider-media-player/spider-media-player /usr/local/bin/spider-media-player

if [[ -f /usr/local/lib/spider-os/studio/spider-media-player.desktop ]]; then
    sudo install -Dm644         /usr/local/lib/spider-os/studio/spider-media-player.desktop         /usr/share/applications/spider-media-player.desktop
fi

sudo update-desktop-database /usr/share/applications 2>/dev/null || true

echo
echo "Spider Media Player installed."
echo "Run: spider-media-player"
