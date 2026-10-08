# Ubuntu Studio tools inside Spider Studio

Spider Studio exposes the existing creative applications on the user's machine. It does not install packages, replace DAWs, start audio servers or automatically change routing, device settings, sample rates or buffer sizes.

Four tabs cover recording/mixing, instruments/effects, routing/mastering, and video/artwork. The catalogue includes Ardour, Qtractor, Audacity, Carla, Guitarix, Rakarrack, Hydrogen, Rosegarden, Qsynth, Yoshimi, Ubuntu Studio Audio Configuration, Patchance, Qpwgraph, QjackCtl, Volume Control, JAMin, Kdenlive, OBS, Blender, GIMP, Inkscape and Krita. These are candidates, not a claim that every application is installed.

The application detects available executables, with desktop-entry fallback for versioned applications, wrappers and supported Flatpak exports. Desktop entries open through `gio launch` to preserve their launch arguments. Hidden, malformed and stale entries with missing executables are excluded. Unavailable buttons are disabled; Refresh installed tools reruns detection.

Music Studio selects an available recording/mixing application. Carla is exposed as a plugin host rather than substituted for a DAW. Existing Studio file paths, Media Center handoff and separate Author workspace are preserved.

## Source verification

- [x] Native launch detection and versioned Ardour fallback.
- [x] Desktop launch argument preservation.
- [x] Missing, hidden and stale entry handling.
- [x] Four tool tabs and available/unavailable button states.
- [x] Button launches the resolved existing application.
- [x] Source tests and offscreen GUI smoke checks.

Installed-PC application inventory, actual app launches, audio-interface/MIDI validation and a real recording/mixing session remain open. This batch integrates applications; lyrics/project management and direct Webbie production controls remain future work.

Official Ubuntu Studio references: [Audio tools](https://ubuntustudio.org/tour/audio/) and [Audio tips](https://ubuntustudio.org/help/content/tips/05-audio/).
