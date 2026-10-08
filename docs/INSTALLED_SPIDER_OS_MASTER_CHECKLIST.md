# Installed Spider OS: Master Build and Upgrade Checklist

**Decision date:** 2026-10-07  
**Scope:** The installed Spider OS system first. The future installer/ISO is a separate, gated deliverable.  
**Canonical implementation repository:** `brokenandalone/spider-narive-os`  
**Companion/staging repository:** `brokenandalone/Spider-OS1`  
**Status:** Planned checklist; unchecked items are NOT evidence that the feature is absent. Verify against the live machine before marking done.

## Completed source work (not installed-machine completion)

Updated 2026-10-07, America/Indiana/Indianapolis. Checked items below mean implemented source and named regression validation. All upgrades are on open, stacked PR branches; none of these batches has been merged or deployed by this session. Full phase gates below remain pending live verification.

- [x] Spider Guardian read-only health report and private diagnostics file. Native [PR #2](https://github.com/brokenandalone/spider-narive-os/pull/2); source and desktop CI passed.
- [x] Selected-source verified local snapshots, transaction-safe SQLite backups and restore into a new directory. Native PR #2; recovery regressions passed.
- [x] Optional encrypted OneDrive-copy implementation, upload guard and disabled daily snapshot timer. Native PR #2; policy tests passed. Real authentication/upload/restore is pending.
- [x] Automatic source CI on pinned Ubuntu 24.04 runners in both repositories. All three previous source batches passed GitHub checks.
- [x] Native Studio app/launcher and missing-DAW dependency messages. Native [PR #3](https://github.com/brokenandalone/spider-narive-os/pull/3); source and GUI smoke tests passed.
- [x] Independent Author launcher with Kate/Writer routing and separate project folders. Native PR #3; this is an editor foundation, not the full manuscript library.
- [x] Media Center launcher naming and recovered legacy-executable compatibility. Native PR #3; resolver tests passed; live playback is pending.
- [x] Separate Studio/Author entry points in The Web and scrolling card area. Native PR #3; desktop smoke tests passed.
- [x] Webbie fixed-action gateway, exact-request approvals, expiry and replay prevention. Native [PR #4](https://github.com/brokenandalone/spider-narive-os/pull/4); 37 native source tests and GitHub desktop checks passed.
- [x] Nine workspace modes and role guidance for a future assistant adapter. Native PR #4; not connected to the live voice agent.
- [x] Forage selected-source text index, source URIs/provenance, stale/deleted-source handling and atomic rebuild. Current `upgrades/forage-local-index` batch; 46 native source tests passed locally. GitHub CI status is recorded on the batch PR.

## Immediate remaining delivery steps

- [ ] Merge the validated stacked source PRs in dependency order.
- [ ] Inventory/backup the installed files and preserve local-only Webbie, media and boot fixes.
- [ ] Deploy selected modules and verify their real launch/close/relaunch behavior.
- [ ] Configure OneDrive locally, then prove encrypted upload/download and restore.
- [ ] Verify the microphone and both authorized voice profiles, conversations, interruption and dismissal.
- [ ] Connect the action gateway through a trusted approval UI and authenticated voice/session adapter.
- [ ] Select Forage source folders on the PC and verify real searches and source links.

## Non-negotiable rules

- Keep the known-booting encrypted installation usable throughout development. Do not replace known-good installed components with older scaffold code.
- Record the actual installed Ubuntu and KDE Plasma versions first. Repository `base.env` values do not establish the installed release.
- Preserve existing LUKS password unlock, bootloader, initramfs and Plasma startup; make recoverable backups before risky changes.
- Keep Webbie's runtime, fast fallback model and active data local; OneDrive is optional sync/backup, never the live operating environment.
- Default voice authorization: owner only until the second trusted speaker is enrolled and validated. Never leave the speaker gate bypassed because a second user has not enrolled. Reject other speakers, TV/movies and Webbie's own TTS. Require stronger confirmation for security-sensitive changes.
- Source-control repositories are public: no cloud tokens, encryption keys, passwords, personal manuscripts, school submissions, private memories or LUKS secrets in Git.
- Webbie may research automatically but must not silently rewrite code, change security settings, install packages, alter boot configuration or commit manuscript changes.
- Every phase passes a smoke test and a rollback/restore check before proceeding.
- No automatic migration to Ubuntu Studio 26.10 on the only working machine. Qualify a VM/USB build and an installed reboot with encryption before considering physical migration.

## Phase 0: Preserve and measure the working machine

- [ ] Capture installed OS release, kernel, KDE Plasma version, graphics/audio backend and storage capacity.
- [ ] Record disk layout, BIOS/UEFI boot mode, LUKS metadata, `fstab`, `crypttab`, GRUB, initramfs and working unlock process. Protect LUKS-header backups.
- [ ] Inventory Spider OS installation paths, source revisions, launchers, services, Python environments and media recovery bundles.
- [ ] Compare installed files to the authoritative repository; identify local-only fixes and safely port them into source control.
- [ ] Back up projects, configurations, current OS build artifacts and service settings to recoverable local storage.
- [ ] Create and test at least one known-good restoration path before editing critical services.
- [ ] Verify the current boot, graphical login, The Web, Spider Core, Webbie, Ollama, network and audio.
- [ ] Review CI workflows that have historically failed or shown no jobs; distinguish successful ISO builds from successful installation tests.
- **Gate:** System continues to boot from its internal encrypted disk without installation media, and recovery materials can actually be used.

## Phase 1: Repair Webbie's existing service and voice security

- [ ] Confirm actual microphone capture device and sound levels (including the existing webcam microphone setup).
- [ ] Verify speech-recognition assets and speaker-recognition model, audio capture, and health reporting on the installed machine.
- [ ] Successfully enroll and validate the owner voice profile; enable the owner-only gate immediately, even without a second enrollment.
- [ ] Add the second trusted voice only after explicit enrollment and validation; test both identities and permitted access levels.
- [ ] Reject unknown speakers and environmental/TV audio; prevent Webbie's own speech from triggering commands.
- [ ] Replace fragile fixed-length listen/respond behavior with VAD and reliable state transitions.
- [ ] Implement wake -> listen -> answer -> listen conversational sessions without repeating the wake word each turn.
- [ ] Make dismissal/end phrases work reliably; add an inactivity timeout and a manual mute control.
- [ ] Support barge-in/interruption while speaking without false wake triggers or truncated commands.
- [ ] Provide clear listening/thinking/speaking/muted feedback and useful error logs.
- [ ] Recover automatically from microphone, transcription, TTS and Ollama failures without an endless conversation loop.
- [ ] Test quiet-room, TV-on, two-speaker, TTS echo, long-conversation, interruption and restart behavior.
- **Gate:** Authorized users can hold several-turn conversations, stop Webbie, and use normal commands without waking her accidentally.

## Phase 2: Spider Guardian, diagnostics and recoverability

- [ ] Add a System Health view covering Spider Core, Webbie, Ollama, media/AI DJ, storage, network and microphones.
- [ ] Implement a diagnostics bundle that captures package/service status, errors and useful non-secret logs.
- [ ] Add service repair/restart actions with permissions and explicit user confirmation as appropriate.
- [ ] Create configuration snapshots and rollback manifests for high-risk Spider components.
- [ ] Add a safe update checker with release notes and compatibility warnings.
- [ ] Add recovery tools for GRUB/initramfs, service startup, media packages and Webbie configuration.
- [ ] Implement backup verification and a documented restore exercise.
- **Gate:** A common broken service can be diagnosed and recovered without rebuilding the entire machine.

## Phase 3: Webbie Intelligence Vault using OneDrive

- [ ] Define local active-memory directories, SQLite/database backup strategy, research journal and project indexes.
- [ ] Connect the user's OneDrive via supported authentication (e.g. rclone) without storing credentials in the repository.
- [ ] Use encrypted cloud-side storage for private memories and sensitive project backups; keep keys solely in protected local storage and a user-controlled recovery method.
- [ ] Establish selective sync areas: Webbie memory snapshots, research, School, Author, Studio metadata, configs and recovery manifests.
- [ ] Keep the active Webbie models, services and live databases on internal storage; never operate directly against a cloud-mounted database.
- [ ] Use consistent/transaction-safe database snapshots; do not copy live SQLite database files without a safe backup method.
- [ ] Add scheduled incremental sync, file-version recovery, integrity checks and conflict handling.
- [ ] Allow per-workspace exclusion/consent for sensitive or large content; avoid uploading private data unintentionally.
- [ ] Verify offline startup and normal Webbie use with OneDrive disconnected.
- [ ] Restore a test memory/research backup to prove recoverability.
- **Gate:** OneDrive loss does not break Webbie; a complete, encrypted backup can be restored to a fresh local profile.

## Phase 4: Repair immediate app and launcher regressions

- [ ] Make the Spider Studio launcher open the real native Studio UI rather than Dolphin/folder fallback.
- [ ] Create Author as its own first-class workspace and launcher, not a submenu of Studio.
- [ ] Replace legacy Spider Media Player launcher/status references with Spider Media Center v1.0.
- [ ] Preserve and test the recovered v7.0-era visualizer/media components; do not overwrite them with the broken v7.5 path.
- [ ] Fix the mismatch between AI DJ "On Air" and radio playback/broadcast state.
- [ ] Check The Web and Plasma taskbar menu behavior, open-window filters, layout and startup ordering.
- [ ] Test launch/close/relaunch and missing-dependency messaging for each installed module.
- **Gate:** No featured module merely opens the wrong application or reports contradictory status.

## Phase 5: Rebuild The Web as the native workspace shell

- [ ] Create a reusable PyQt/KDE workspace framework rather than independent duplicate launch panels.
- [ ] Add a persistent dock, running-app indicator, notifications, workspace history and quick search.
- [ ] Provide native workspaces: Home, School, Author, Studio, Media Center, Webbie, Forage, Deep Forage, Dev Bay, Art & Design, Communications, Productivity, Devices, Kali Bay, System.
- [ ] Design and integrate distinct wallpapers/backgrounds for each workspace with consistent Spider branding.
- [ ] Add persistent workspace layouts, restore-on-login, window tracking and keyboard shortcuts.
- [ ] Embed a compact Webbie control/status surface and Spider Pulse performance/service display.
- [ ] Refine splash, login, lock screen, scaling/multi-monitor, dark theme and accessibility behavior.
- [ ] Ensure a broken optional application cannot prevent KDE or The Web from starting.
- **Gate:** Workspace switching, launchers, taskbar and status work across sessions without disabling the normal desktop.

## Phase 6: Upgrade Webbie intelligence and shared services

- [ ] Introduce a modular action API/permissions gateway instead of one ever-growing assistant script.
- [ ] Add role/mode awareness: Normal, School Tutor, Author Editor, Studio Producer, AI DJ, Researcher, Developer, System Technician and Security Assistant.
- [ ] Route workloads between a fast offline command model, stronger local models and an explicitly configured online fallback.
- [ ] Measure CPU/RAM/GPU usage and latency; select models the machine can run reliably.
- [ ] Implement persistent local memory retrieval, project-specific context and visible memory controls.
- [ ] Integrate navigation, supported website operations and native app actions through permissioned tools.
- [ ] Separate permission levels: safe read/open, project edits requiring approval, privileged/destructive changes requiring strong confirmation.
- [ ] Add Webbie research queue, source evaluation, confidence assessment and a searchable Research Journal.
- [ ] Add one self-selected curiosity topic per day and avoid repeated research; do not allow unapproved self-modification.
- [ ] Add useful opt-in proactive notices for assignments, system health and project developments.
- **Gate:** Webbie can assist across installed apps and retain useful knowledge without risking system integrity or exposing data.

## Phase 7: School workspace

- [ ] Build native School dashboard and move prior Study capabilities into it without data loss.
- [ ] Add courses, module schedule, assignment tracker, due dates, progress and grade views.
- [ ] Add rubric storage, papers, notes, discussion support, completed-work archive and source organizer.
- [ ] Add APA formatting assistance and document templates.
- [ ] Add Webbie Tutor with active-course context and instructor preferences.
- [ ] Provide supported SNHU portal links/integrations without insecure credential handling.
- [ ] Add optional selective encrypted OneDrive document backups.
- **Gate:** All active school material can be found and organized from School.

## Phase 8: Author workspace and Broken World tools

- [ ] Create a truly local-first manuscript editor with book library, chapter navigation and autosave.
- [ ] Add snapshots, version history, compare/revisions and recovery from interrupted saves.
- [ ] Add character profiles, location map, plot timeline, canon rules, clues and relationship graphs.
- [ ] Build a continuity checker for Broken World and an approval-before-edit workflow.
- [ ] Add chapter read-aloud, notes, writing goals and scene tracking.
- [ ] Add export to manuscript/ebook/print formats and backup bundles.
- [ ] Import existing manuscripts and companion materials without duplicate or overwritten chapters.
- [ ] Add encrypted selective OneDrive backups.
- **Gate:** Author can edit, save, search and recover a complete manuscript offline.

## Phase 9: Spider Studio and creative production

- [ ] Integrate installed Ubuntu Studio DAWs, audio interfaces, PipeWire/JACK, MIDI and plugins.
- [ ] Build songwriting/lyrics library, projects, arrangements, session notes and reusable templates.
- [ ] Add guitar effects, live monitoring, recording, mixing and mastering workflow shortcuts.
- [ ] Add Webbie producer controls for approved edits, research, brainstorming and project management.
- [ ] Integrate artwork, photo/video production and export presets (including album artwork).
- [ ] Add production-to-Media Center handoff and encrypted cloud backup of selected project files.
- **Gate:** Studio works as a useful creative workstation, not just a file manager.

## Phase 10: Spider Media Center, BCN and AI DJ

- [ ] Validate music, movies, TV shows, radio, photos, library/queues and saved playlists.
- [ ] Repair the GPU/audio-reactive visualizer without sacrificing existing playback functionality.
- [ ] Fix live radio playback versus "On Air" state; use one authoritative playback/broadcast status.
- [ ] Integrate AI DJ voice generation, breaks, ducking, crossfade, model selection and Webbie control.
- [ ] Add live TV support, network media sources, devices and casting where supported.
- [ ] Integrate BCN programming, station IDs, public relay and listener/broadcast diagnostics.
- [ ] Preserve a known-good media build, versioned rollback and regression tests.
- **Gate:** Playback, broadcast status, AI DJ and visualizer pass a continuous end-to-end session test.

## Phase 11: Forage, Deep Forage, Threads and Timeline

- [ ] Index local authorized files, projects, application entries and saved research.
- [ ] Add fast global search and per-workspace search with source links.
- [ ] Add Deep Forage multi-step research, source collection, synthesis and citation tracking.
- [ ] Create Spider Threads for linking research/materials across workspaces without copying everything.
- [ ] Create a searchable Spider Timeline of files, active projects, completed builds and approved actions.
- [ ] Make local indexes rebuildable from primary storage and protected backups.
- **Gate:** One search finds the right local material and preserves source/provenance.

## Phase 12: Dev Bay, Art & Design, Communications and Productivity

- [ ] Finish Dev Bay editor/terminal/project manager, GitHub, Python/C++ toolchains and development environments.
- [ ] Add build/test dashboards and validated continuous integration workflows.
- [ ] Build a Spider App Manager for modules, dependency checks, versioning, updates and permissions.
- [ ] Integrate drawing, painting, tattoo design, photo editing and graphics/video utilities into Art & Design.
- [ ] Add communications entry points for supported email, calendar and contacts integrations.
- [ ] Add productivity tasks, notes, reminders, schedules and an activity organizer.
- **Gate:** Each workspace has a defined useful workflow and consistent integration contract.

## Phase 13: Devices, remote access and Kali Bay

- [ ] Build Devices dashboard for storage, USB, Bluetooth, display, network and audio peripherals.
- [ ] Verify the usable 64 GB drive and diagnose the questionable "256 GB" drive capacity before allocating data.
- [ ] Provide secure remote desktop/control from phone and laptop with authentication and network access controls.
- [ ] Test up to three desired remote sessions subject to hardware/resource capacity.
- [ ] Finish isolated Kali Bay/Kali Purple environment and safe graphical security tool launchers.
- [ ] Keep Kali package changes inside its isolated environment rather than polluting the host.
- [ ] Add Webbie Security Assistant through an explicitly permissioned boundary.
- **Gate:** Remote access is secure, hardware tools are reliable and Kali cannot silently alter the host.

## Phase 14: Portable AI DJ and recovery media

- [ ] Build the portable 64 GB AI DJ edition only after the installed Media Center and Webbie audio paths are stable.
- [ ] Package small offline model/runtime, voice assets, cues, station liners, break cache and configuration within actual tested USB capacity.
- [ ] Make portable storage removable without breaking normal Spider OS operation.
- [ ] Design a bootable Spider Recovery environment with diagnostics and encrypted-disk repair support.
- [ ] Document how to restore the working internal-drive installation and key data from backup.
- **Gate:** The portable build works on its target machine and the recovery path is tested.

## Phase 15: Future OS release migration and final qualification

- [ ] Keep the working install as baseline; confirm the actual supported upgrade path before selecting an Ubuntu Studio release.
- [ ] Prepare a dedicated migration branch; pin GitHub Actions runner images and release dependencies.
- [ ] Port packaging, KDE/Plasma, kernel, systemd, audio and desktop dependencies without discarding working fixes.
- [ ] Build ISO, checksums, reproducible logs and a VM boot/install test.
- [ ] Validate installed-VM first boot, encrypted unlock, launcher/service startup and second reboot after install media removal.
- [ ] Run physical-media and physical-machine qualification only with tested rollback options.
- [ ] Test installed Webbie, The Web, OneDrive offline behavior, School, Author, Studio, Media Center, Forage, Kali Bay and Recovery end to end.
- [ ] Promote the migration to the new baseline only after all qualification gates pass.
- **Gate:** A genuinely bootable, supportable Spider OS release, not merely a successful ISO build.

## Tracking convention

- Keep tasks unchecked until verified on the **installed** machine or in the named test environment.
- For completed tasks, append the test date, version/commit and evidence link or short log reference.
- Add blockers under their phase; do not skip a safety gate because an exciting feature is waiting.
- Revisit priority order after each phase, but preserve the rule: **working installed system -> reliable Webbie -> recovery/OneDrive -> workspaces -> future distribution release**.
- Keep `docs/SPIDER_OS_26_10_MASTER_PLAN.md` as the broader release roadmap; use this document as the ordered installed-system execution checklist.

## GitHub implementation batch: workspace launchers

2026-10-08 UTC: Native Studio source/launcher, an independent Author editor launcher, common media resolution and Media Center menu naming are implemented in the workspace-launcher branch. The Web exposes Studio and Author separately, and packaging includes their modules. See `docs/WORKSPACE_LAUNCHER_REPAIRS.md` for the deliberately limited Author foundation and the remaining installed-machine checks. No live checkbox is marked complete from source tests.

## GitHub implementation batch: Webbie action gateway

2026-10-08 UTC: A local fixed-action registry, request-bound approval queue and workspace mode context are implemented under `webbie/actions`. The existing voice agent and its installed fixes are preserved. See `docs/WEBBIE_ACTION_GATEWAY.md` for the trust boundary and pending voice/approval-surface integration. No live-machine checkbox is marked complete.
