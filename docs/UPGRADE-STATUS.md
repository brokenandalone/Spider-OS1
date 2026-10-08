# Upgrade status — 8 October 2026

GitHub source completion does not establish installation on the owner PC.
Earlier owner confirmations cover the Guardian/Vault/Studio/Author foundations,
Webbie action gateway, Forage foundations, microphone watchdog, local Ollama
models, research timer, USB memory, and the original workspace wallpaper set.
Preserve those local configurations, including modified Webbie source.

The following newer additions have source tests, but no owner-PC installation
confirmation:

| Upgrade | Source location | Owner check after installing |
| --- | --- | --- |
| Author library, chapter history, canon notebook and bundle import | `author/` | Open Author; import the private bundle; edit, restart, restore a chapter version. |
| School dashboard and APA student papers | `study/` | Open School; check assignments; export and open a paper. |
| Installed Ubuntu Studio tool catalog | `studio/tools.py`, `studio/main.py` | Refresh tool detection and launch the already installed creative applications. |
| AI DJ HTTP reliability | `media/ai-dj/service.py` | Restart the user service; check health and prepare a spoken transition. |
| Media playback, visible errors, local compatibility preparation and radio state | Separate `brokenandalone/Spider-Media-Center` repository | Update the actual packaged application, then test Play/Pause/seek, a local movie, compatibility cancellation, and stop/start broadcast. |

The seven-workspace wallpaper pack was prepared previously; its newer wallpaper
connections have no installation confirmation. Do not replace the confirmed
original wallpapers merely because alternatives exist.

The Media Center code repairs do not update an installed Kabel 7.5 executable.
They must be included in its next build. Follow that repository's playback
verification notes; the native compatibility action prepares a separate local
movie copy for the embedded player. Full direct libVLC decoding remains pending.

For the installed AI DJ, after this service source has been deployed to its
existing path:

```bash
systemctl --user restart spider-ai-dj.service
curl --fail http://127.0.0.1:9876/health
curl --fail -H 'Content-Type: application/json' \
  -d '{"currentTrack":{"title":"First track"},"nextTrack":{"title":"Next track"}}' \
  http://127.0.0.1:9876/dj/prepare
```

A successful prepare response includes `script` and a local `audioFile` URL.
Listen to the result before calling the installed AI DJ verified. This work does
not migrate the OS base or replace owner-modified Webbie files.
