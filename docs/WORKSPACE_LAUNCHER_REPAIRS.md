# Native workspace launcher repairs

This is a source implementation batch stacked on the Guardian/Vault upgrade branch. It is not evidence of deployment to the installed PC. Preserve locally repaired Webbie, media binaries and boot configuration when installing selected modules.

## Studio

`studio/bin/studio` starts the actual native Python/Qt Studio application. The existing companion layout is deliberately ported into the authoritative repository; the old Author web link is removed. Studio contains music, media and artwork entry points. It does not create a new Author directory inside Studio or delete any old Author data.

A missing DAW produces a clear dependency message rather than silently opening Dolphin. Service probes are bounded, and missing systemd/Ollama does not prevent Studio construction. Studio's media entry uses the same media resolver as The Web.

## Author

`author/bin/author` opens an independent local writing session, with project folders under `~/Documents/Spider OS/Author`. Kate uses the named `Spider-Author` session, and supported office manuscripts open in LibreOffice Writer. The wrapper accepts one existing manuscript path. It does not copy, import or overwrite manuscripts. Old Studio/Author directories remain untouched.

This completes the independent launcher foundation. It does not implement the Phase 8 book library, chapter-navigation editor, autosave/snapshots, canon checker or publishing exports. Existing Writer documents continue to use Writer; Kate is for text manuscripts. A full dedicated Author application remains planned.

Examples after selected-module installation:

```bash
/usr/local/lib/spider-os/studio/bin/studio
/usr/local/lib/spider-os/author/bin/author
/usr/local/lib/spider-os/author/bin/author /path/to/book.docx
/usr/local/lib/spider-os/media/bin/spider-media-center
```

Kate session command reference: [KDE handbook](https://docs.kde.org/stable_kf6/en/kate/kate/fundamentals.html).

## Media Center compatibility

The user-facing launchers say Spider Media Center. An executable `/opt/spider-media-center/spider-media-center` is preferred when present. Otherwise the recovered legacy `/opt/spider-media-player/spider-media-player` package remains usable through its existing launcher, retaining the personal AI DJ/profile environment. Merely having a wrapper on PATH is not sufficient evidence that the package exists.

This change does not download or rebuild the media app, change v7.0/v7.5 donor selection, repair the visualizer or establish that radio/AI DJ is on air. Those playback and broadcast checks remain installed-machine gates. The legacy `.desktop` filename is preserved to avoid adding a duplicate menu entry.

## The Web and packaging

Studio and Author have their own buttons and cards. Author is its own workspace ID and uses the existing System background as a temporary fallback; dedicated workspace artwork belongs to the later design phase. The center panel scrolls so extra cards remain reachable at smaller desktop sizes. Existing Study paths are retained.

The installed and live payloads package Studio, Author, the shared launch contracts and desktop entries. Kate is added to future image dependencies. This does not install Kate on the running machine, change the base Ubuntu release or rewrite boot/installer behavior.

Regression tests exercise absent apps, executable detection, legacy compatibility, independent author sessions, office-vs-text routing, old-data preservation and Studio's native target. GitHub's desktop smoke test additionally constructs The Web and Studio and checks all workspace backgrounds. Live launch/close/relaunch with the actual editors/media package remains unqualified until performed on the installed PC. No voice agent files are changed; local Webbie voice/security fixes must be preserved during deployment.
