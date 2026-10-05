# Spider OS 26.10 Master Plan

Status: Canonical roadmap  
Date locked: 2026-10-04  
Owner intent: Spider OS must remain bootable while evolving into a Jarvis-style personal operating system centered around Webbie.

## Non-negotiable rules

1. The current internal-drive Spider OS boot is the safety baseline.
2. The 26.10 migration must not sacrifice reliable booting.
3. The current LUKS unlock-at-boot flow stays in place during the migration.
4. Every major phase has a boot/install/reboot qualification gate before the next phase begins.
5. Preserve known-good rollback points before changing boot, initramfs, GRUB, encryption, Plasma, Webbie startup, or The Web startup.
6. Do not call an ISO "good" merely because it builds. A good build must boot, install, remove USB, unlock the disk, boot from the internal drive, start KDE, start Spider Core, start Webbie, start The Web, and survive another reboot.
7. Webbie may research and learn autonomously, but autonomous learning means curated knowledge growth, not unapproved self-modification of system code, security policy, or model weights.

---


## Available removable storage

Known USB inventory for planned roles:

- 256 GB USB drive: the single large removable drive. Preferred candidate for the full portable AI DJ build, or for a split portable AI/Webbie storage layout if we later decide that is more useful. It is large enough for multiple local models, voice assets, track intelligence, research indexes, caches, runtime files, and backups.
- 64 GB USB drive: suitable for Spider OS 26.10 installer/test media, recovery media, or a lighter portable AI DJ build.

Webbie's primary runtime should remain on the internal drive for speed and reliability. The 256 GB drive can still carry selected Webbie models, research caches, recovery assets, or portable support data if useful.

Do not dedicate a drive permanently until the 26.10 migration and recovery-media needs are settled.

# Phase 0: Freeze the current working Spider OS

Before the 26.10 migration:

- tag the current booting 24.04.5/Noble state
- back up the current Spider OS source and build configuration
- capture the current partition table and boot mode
- capture GRUB configuration
- capture /etc/fstab and /etc/crypttab
- back up the LUKS header safely
- record installed kernel/package versions
- record enabled system and user services
- preserve the current Spider Media Center known-good build and recovery ASARs
- preserve current Spider Core, The Web, Webbie, Studio, Author, and Kali Bay files
- record a known-good boot checklist

This is the restore point for the entire migration.

---


## Migration method from the running Spider OS system

The currently booting Spider OS may be used as the build and migration workstation.

Do not attempt an unsupported one-step in-place jump from the current Ubuntu 24.04-based Spider OS directly to Ubuntu Studio 26.10.

Preferred path:

1. Preserve and snapshot the currently booting Spider OS.
2. Use the running Spider OS to update the source tree, build the 26.10 Spider OS image, create test media, and run VM qualification.
3. Keep the host on the known-working boot configuration while the 26.10 beta/final image is being qualified.
4. If an in-place base transition is used, first use the supported Ubuntu 24.04 LTS -> Ubuntu 26.04.1 LTS release upgrade path.
5. Only after that base is stable, move from 26.04 to 26.10 using the supported interim-release path when appropriate. Do not use a development-release upgrade on the only working installation unless a full rollback path has already been tested.
6. Prefer a controlled 26.10 install/migration if it proves safer than carrying custom Spider OS state through multiple release upgrades.
7. Preserve LUKS encryption and the existing password-unlock behavior throughout the migration unless a separate later project explicitly changes it.

The running system is therefore the control station for the upgrade, not disposable test media.


# Phase 1: Create the Ubuntu Studio 26.10 migration branch

Create a dedicated Spider OS 26.10 migration branch.

Refactor the build system so these values are centralized instead of scattered through scripts:

- Ubuntu Studio release
- Ubuntu Studio point/beta/final image version
- codename
- ISO URL
- checksum URL
- Spider OS release metadata
- output ISO name
- GitHub Actions release notes

Target:

- Ubuntu Studio 26.10 base
- Spider OS identity preserved everywhere
- The Web remains the native Spider shell/integration layer
- KDE Plasma remains the desktop foundation

Do not hardcode assumptions about BIOS/UEFI or disk layout. Detect and preserve the working boot path.

---

# Phase 2: Port Spider OS to 26.10 and prove boot stability

Port the current Spider OS payload onto the 26.10 Ubuntu Studio base.

Audit and fix:

- package name changes
- Python/runtime changes
- KDE/Plasma changes
- PipeWire/JACK/audio changes
- installer/bootstrap changes
- kernel/initramfs behavior
- systemd service behavior
- graphics/audio dependencies
- branding paths
- live-session defaults
- user-service startup

## Boot qualification gate

This phase does not pass until all of the following work:

1. USB/ISO boots.
2. Spider OS live desktop reaches KDE.
3. The Web starts.
4. Webbie user service starts.
5. Spider Core starts.
6. Network works.
7. Audio works.
8. Installer launches.
9. Installation completes.
10. USB is removed.
11. Internal encrypted disk requests the existing LUKS password.
12. Disk unlock succeeds.
13. GRUB/bootloader works.
14. Initramfs finds the encrypted root correctly.
15. Installed Spider OS reaches KDE.
16. Spider Core starts.
17. Webbie starts.
18. The Web starts.
19. Reboot succeeds again without installation media.

Known past failures that must have explicit tests:

- /cow path contamination
- GRUB generation/install issues
- installed system failing after USB removal
- Plasma live-session theme/layout crashes
- kactivitymanagerd ordering
- NetworkManager wait-online startup delays
- Webbie files present but user service not enabled
- Spider Core present but service not enabled
- The Web present but not autostarting
- Ubuntu Studio branding leaking through Spider branding
- read-only/live-session behavior being mistaken for an installed system
- build success despite missing Spider components

---

# Phase 3: Rebuild The Web as the workspace shell

The Web becomes the visual and functional command center for Spider OS.

Top-level workspaces:

1. Home / The Web
2. School
3. Author
4. Spider Studio
5. Spider Media Center
6. Webbie
7. Forage
8. Deep Forage
9. Dev Bay
10. Art & Design
11. Communications
12. Productivity
13. Devices
14. Kali Bay
15. System

Recovery lives inside System rather than as a separate top-level workspace.

Every workspace gets its own designed Spider OS background.

Background direction:

- Home: existing Spider OS identity
- School: reuse/refine the current Study background
- Author: dark literary/gothic Spider visual
- Spider Studio: music/creative production visual
- Media Center: media/BCN visual
- Webbie: dedicated resident-AI visual
- Forage: search/index visual
- Deep Forage: intelligence/research visual
- Dev Bay: coding/build/terminal visual
- Art & Design: visual arts/branding visual
- Communications: network/connection visual
- Productivity: planning/organization visual
- Devices: hardware/peripheral visual
- Kali Bay: security/Kali Purple visual
- System: control/diagnostics visual

The workspace shell is built once so future tools plug into a stable structure.

---

# Phase 4: Build School as a first-class SNHU workspace

School replaces the old top-level Study workspace. The old Study identity becomes part of School.

School includes:

- Dashboard
- Current courses
- Assignments
- Due dates
- Calendar
- Discussion boards
- Papers
- Grades/progress
- Course resources
- APA Center
- Study Planner
- SNHU portal access
- Webbie Tutor
- Course-specific notes
- Course memory/context
- Instructor preferences/rules
- Rubrics
- Feedback history
- Completed work archive
- Research/source organizer

School should be linked to SNHU through safe supported portal/web integration. Do not scrape or store credentials insecurely.

Webbie should automatically understand the active course and switch into the appropriate academic context.

---

# Phase 5: Build Author as a first-class workspace

Author remains separate from Spider Studio.

Author includes:

- manuscript editor
- book/project library
- chapter navigation
- autosave
- snapshots
- version history
- compare/revision tools
- character database
- character relationship maps
- locations
- timelines
- world/lore database
- canon rules
- continuity checker
- series planning
- scene tracker
- plot-thread tracker
- unresolved-clue tracker
- research notes
- source library
- read-aloud
- writing goals
- word counts
- synopsis tools
- query/package preparation
- cover planning
- publishing metadata
- ebook export
- print export
- backup/export bundles

For Broken World specifically, Webbie must be able to check new writing against established canon and flag contradictions.

Webbie may suggest edits directly in the manuscript UI, but manuscript changes require approval before being committed.

---

# Phase 6: Upgrade Spider Studio on the 26.10 creative stack

Spider Studio is for music/audio, songwriting, recording, mixing/mastering, graphics, video, and creative production.

Upgrade it around the real Ubuntu Studio 26.10 stack:

- DAWs
- PipeWire/JACK routing
- MIDI
- audio interfaces
- plugins
- recording
- editing
- mixing
- mastering
- songwriting
- graphics
- artwork
- video
- production utilities
- project management
- Media Center handoff
- Webbie producer mode

Do not put school writing or long-form book authoring inside Studio.

---

# Phase 7: Reintegrate and qualify Spider Media Center

Use the stabilized Spider Media Center codebase rather than restarting from scratch.

Preserve and qualify:

- audio playback
- video playback
- visualizers
- BCN
- live radio
- AutoDJ
- AI DJ controls
- Talk to Spider
- queue/library
- network media
- public relay
- broadcast status
- Webbie control interface

Do not casually rebuild the old React source if doing so would erase the recovered compiled functionality.

---

# Phase 8: Major Webbie upgrade, the Jarvis phase

Webbie is the resident intelligence layer for Spider OS, not a chatbot bolted onto the desktop.

## Voice

Wake phrases remain:

- Hey Webbie
- Webbie
- Hey Web
- Web

One wake phrase opens a continuous conversation session:

wake -> listen -> answer -> listen -> answer -> continue

The conversation remains active until:

- the user says a dismissal phrase such as "Thanks Webbie", "Go to sleep", "That's all", or "Stop listening"
- or a sensible inactivity timeout expires

Add:

- barge-in/interruption while Webbie is speaking
- natural turn-taking
- low-latency listening
- voice activity detection
- clear listening/thinking/speaking status
- recovery from microphone/TTS failures

## Webbie operating modes

Webbie can automatically switch context while retaining one consistent core personality:

- Normal Webbie
- Studio Producer
- Author Editor
- School Tutor
- AI DJ
- Researcher
- Developer
- System Technician
- Security Assistant

## Permission model

Level 1: Safe actions, act immediately

Examples:

- open an app
- open a webpage
- search files
- play media
- switch workspace
- gather information

Level 2: Content/project changes, require approval

Examples:

- edit manuscript
- modify project files
- submit generated content
- change project configuration

Level 3: System/sensitive actions, require explicit confirmation

Examples:

- package changes
- bootloader changes
- disk/encryption changes
- destructive file operations
- security policy changes
- privileged system configuration

## Web and application control

Webbie should be able to:

- open webpages
- navigate websites
- run supported web applications
- search sites
- fill forms
- download permitted files
- upload files
- collect research
- move research into the appropriate workspace
- control Spider OS applications
- control Spider Media Center
- assist inside Spider Studio
- work in School
- work in Author
- use Forage and Deep Forage

Consequential web actions still obey the permission system.

## Intelligence routing

Default policy:

local first -> stronger local model if needed -> online intelligence if local capability is insufficient

Suggested routing:

- wake-word/VAD: tiny local service
- simple commands: very fast local model
- normal conversation: fast local model
- AI DJ: dedicated local model
- writing: larger local model
- coding/system analysis: strongest appropriate local model or online model
- deep research: online intelligence + Forage
- complex repair: best available model with explicit permissions

## Memory and project context

Webbie needs persistent context for:

- Spider OS state
- active projects
- School courses
- Author projects
- Spider Studio projects
- Media Center/BCN
- known system preferences
- project-specific rules/canon
- recent activity

Workspace context should resolve ambiguous commands. For example, "open chapter 15" should route to Author while "open the mixer" should route to Studio.

## Proactive behavior

Webbie should proactively surface:

- upcoming School deadlines
- project changes
- completed builds
- system problems
- relevant research
- Media Center/BCN status
- storage/device problems
- updates that affect Spider OS

She should not nag constantly. Proactive behavior must be useful and inspectable.

---

# Phase 9: Webbie autonomous research and daily learning

This is a core Jarvis behavior.

When not actively serving the user, Webbie may maintain a research queue.

She researches two categories:

## A. User-interest research

Topics connected to:

- Spider OS
- software/projects
- music/audio
- Broken World/Author work
- psychology/sociology/school
- AI tools
- security
- other known interests and active projects

## B. Daily curiosity research

At least once each day, Webbie chooses one topic herself that is not required to match the user's known interests.

The purpose is broader knowledge growth and intellectual curiosity.

The chosen topic may come from science, history, technology, art, culture, engineering, language, nature, philosophy, design, mathematics, music, or another legitimate field.

The daily topic should be recorded so Webbie does not simply repeat the same material.

## Research pipeline

research -> source evaluation -> synthesis -> confidence assessment -> store -> index -> connect to relevant knowledge -> journal

Webbie keeps a Research Journal containing:

- topic
- why it was selected
- date
- sources
- key findings
- confidence
- connections to existing knowledge/projects
- whether the user should be notified
- whether the result changed any working assumption

Important boundary:

Autonomous learning updates Webbie's curated knowledge base and retrieval memory. It does not silently retrain model weights, install software, rewrite system code, alter permissions, or change security settings.

Webbie can propose such changes separately through the permission system.

---

# Phase 10: Build the portable AI DJ system

Use the user's available USB drives, including the 200+ GB drive.

The large drive becomes the full portable AI DJ edition.

Potential layout:

- DJ runtime
- fast live model
- larger show-prep model
- Ollama/llama.cpp assets
- TTS voices
- station IDs
- liners/drops
- transition logic
- track analysis database
- BPM/key/mood/cue metadata
- generated break cache
- configuration
- logs
- backup manifests

Smaller USB drives can be used for:

- lightweight AI DJ builds
- recovery
- station packs
- portable configuration
- model subsets

Do not begin this phase until Media Center and Webbie integration are stable.

---

# Phase 11: Finish Kali Bay / Kali Purple

Kali Bay remains isolated from the Spider OS host.

Target:

- Kali Purple environment
- full Kali toolset where practical
- graphical category launchers
- safe networking integration
- Webbie Security Assistant mode
- clear host/container/VM boundary
- no uncontrolled package pollution of the Spider OS host

---

# Phase 12: Build System and Recovery

Recovery lives under System.

System areas:

- Overview
- Updates
- Storage
- Services
- Hardware
- Network
- Audio
- Graphics
- Logs
- Diagnostics
- Boot
- Encryption
- Recovery
- Backups
- Rollback
- Developer information

Recovery capabilities:

- known-good configuration snapshots
- boot repair
- GRUB repair
- initramfs repair
- service repair
- log collection
- package rollback information
- Spider OS version/build identification
- Media Center rollback references
- Webbie service diagnostics
- installer diagnostics
- backup/restore guidance

Keep the current LUKS password unlock flow until the upgraded OS is proven stable through repeated real boot tests.

---

# Phase 13: Final integration and qualification

Do not ship the final Spider OS 26.10 build until all major workspaces and services pass.

Final checks:

- ISO build
- checksums
- VM boot
- VM install
- installed VM reboot
- physical boot
- physical install if required
- LUKS unlock
- GRUB
- initramfs
- KDE
- The Web
- Spider Core
- Webbie
- continuous voice conversation
- local model routing
- online fallback
- autonomous research queue
- daily curiosity learning
- School
- SNHU access
- Author
- Spider Studio
- Spider Media Center
- BCN
- AutoDJ
- Forage
- Deep Forage
- Dev Bay
- Art & Design
- Communications
- Productivity
- Devices
- Kali Bay
- System
- Recovery
- audio
- video
- network
- connected devices
- second reboot
- rollback test

Only after this qualification does Spider OS 26.10 become the new baseline.

---

# Canonical execution order

0. Freeze current booting system.
1. Create/configure 26.10 migration branch.
2. Port to Ubuntu Studio 26.10 and pass boot/install/reboot gate.
3. Rebuild The Web workspace framework and backgrounds.
4. Build School/SNHU workspace.
5. Build Author workspace.
6. Upgrade Spider Studio.
7. Reintegrate and qualify Spider Media Center.
8. Upgrade Webbie into the Jarvis-style resident intelligence layer.
9. Add autonomous research and once-daily self-chosen learning.
10. Build portable AI DJ USB system.
11. Finish Kali Purple/Kali Bay.
12. Build System/Recovery.
13. Perform final full-system qualification.

This order is intentionally conservative around boot and aggressive around capability only after the 26.10 foundation proves reliable.
