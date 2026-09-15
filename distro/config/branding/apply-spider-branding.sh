#!/usr/bin/env bash

WALLPAPER="/usr/share/backgrounds/spider-os-wallpaper.png"

if command -v plasma-apply-wallpaperimage >/dev/null 2>&1; then
    plasma-apply-wallpaperimage "$WALLPAPER" >/dev/null 2>&1 || true
fi

mkdir -p "$HOME/.config"
touch "$HOME/.config/spider-os-branding-applied"
