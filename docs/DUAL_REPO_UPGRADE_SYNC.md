# Spider OS Dual-Repository Upgrade Sync

This project is intentionally tracked in both repositories:

- `brokenandalone/spider-narive-os`
- `brokenandalone/Spider-OS1`

## Authority and preservation rule

`spider-narive-os` is the repository that produced the Spider OS build that successfully installed and booted. Its working installer, QEMU install/boot qualification, service wiring, live-session fixes, writable installed filesystem behavior, and boot repairs are authoritative.

`Spider-OS1` remains a synchronized companion/staging repository for the same upgrade roadmap.

Never replace the mature `spider-narive-os` implementation wholesale with an older scaffold from `Spider-OS1`. Port changes deliberately and preserve the working boot/install tests.

## Shared upgrade scope

Both repositories track the same planned Spider OS 26.10 upgrade:

- Ubuntu Studio 26.10 Stonking Stingray base migration
- boot/install/reboot qualification and rollback protection
- School workspace linked to SNHU
- Author workspace
- Spider Studio upgrade
- Spider Media Center integration
- Webbie continuous voice conversation
- Webbie multi-mode behavior
- Webbie site/browser operation
- local-first model routing with online fallback
- Webbie autonomous research
- at least one self-chosen learning topic per day
- Forage and Deep Forage integration
- Dev Bay
- Art & Design
- Communications
- Productivity
- Devices
- Kali Bay / Kali Purple
- System with Recovery underneath it
- workspace-specific background designs
- 256 GB Webbie Intelligence Vault
- 64 GB Portable AI DJ
- preservation of current LUKS password unlock during migration

## Branch policy

Keep the current working base protected by a baseline branch.

Do all 26.10 base work on:

`migration/ubuntu-studio-26.10`

Do not merge the migration branch into `main` until the install-and-boot qualification gate passes.

## Guardian and Vault source batch

The companion carries matching system tools, recovery tests and usage documentation. Installed/live ISO packaging is implemented in `spider-narive-os`; this older scaffold does not establish installed qualification. Follow `docs/INSTALLED_SPIDER_OS_MASTER_CHECKLIST.md` for the installed system, retaining all live-machine gates.
