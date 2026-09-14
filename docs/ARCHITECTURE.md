# Spider OS Architecture

## Mission

Spider OS is a native Linux operating system built around the user's life,
creative work, development work, security work, and resident AI assistant.

Spider OS is not a web application and The Web is not a browser homepage.

## Base System

Spider OS uses Ubuntu LTS as its underlying Linux foundation and installs the
Ubuntu Studio creative software stack on top of it.

The distribution remains branded and configured as Spider OS.

Ubuntu provides:
- Kernel
- Hardware support
- APT package management
- systemd
- Linux userspace
- KDE/Plasma compatibility

Ubuntu Studio provides the creative software foundation for:
- Audio
- Music production
- Graphics
- Photography
- Video
- Publishing

## Desktop

KDE Plasma is the graphical desktop foundation.

Spider OS adds its own native desktop experience called:

    The Web

The Web is a native desktop shell/integration layer and must never require a
browser to function.

The Web contains:
- Spider command center
- Anchors
- Threads
- Personal Knowledge Web
- Forage search
- Deep Forage
- Webbie interface
- Native application areas
- Kali Bay launcher
- Spider Media integration

## Webbie

Webbie is the resident AI of Spider OS.

Webbie runs as a persistent native system/user service.

Webbie must:
- Start automatically
- Remain available while the user is logged in
- Support voice input
- Support voice output
- Respond to wake phrases
- Integrate with The Web
- Access Forage
- Access Deep Forage
- Work with local applications
- Provide proactive assistance
- Periodically check whether the user needs anything while logged in

Voice support is a core feature and is not optional.

Wake phrases:
- Hey Webbie
- Webbie
- Hey Web
- Web

## Forage

Forage is Spider OS's native search and research layer.

Forage handles:
- Local file search
- Application search
- Personal Knowledge Web search
- Indexed content search
- System search

Deep Forage handles:
- Multi-step research
- Autonomous research tasks
- Source collection
- Research synthesis
- Web-assisted research when permitted

## Kali Bay

Kali Bay is an isolated security workspace.

Kali tools must not pollute the normal Spider OS host.

Kali Bay contains a complete Kali Linux environment and provides graphical
access to Kali tool categories.

Isolation may use containers, systemd-nspawn, virtual machines, or another
appropriate Linux isolation mechanism.

The full Kali toolset is the target, not a reduced selection.

## Application Areas

Applications are organized into dedicated Spider OS areas rather than one
undifferentiated application list.

Primary areas include:
- Creative Studio
- Development
- Media
- Productivity
- Education
- Communications
- System
- Kali Bay

## Branding

Spider OS branding uses:
- Black
- Graphite
- Purple/violet
- Bone/off-white accents

The Spider OS identity must replace upstream Ubuntu branding wherever practical.

Tagline:

    YOUR LIFE. ONE WEB.

## Boot Requirements

An installed Spider OS system must boot directly into the native Linux system.

No browser or remote server is required to obtain the Spider OS desktop.

The boot process must ultimately provide:
1. Linux kernel
2. systemd
3. graphical target
4. KDE Plasma
5. Spider OS services
6. Webbie
7. The Web

## Build Requirements

The project must eventually produce:

- Spider OS installer ISO
- Installed-system image
- Build checksums
- Build logs
- Automated boot tests
- Automated install tests
- Installed-system qualification tests

The qualification test must verify:
- Successful installation
- Reboot from installed disk
- KDE starts
- Spider OS service starts
- Webbie service starts
- The Web components exist
- Forage components exist
- Kali Bay environment can be initialized
