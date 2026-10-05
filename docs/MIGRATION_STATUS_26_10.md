# Spider OS 26.10 Migration Status

Updated: 2026-10-04

## Repository policy

The upgrade is being carried in both:

- `brokenandalone/spider-narive-os`
- `brokenandalone/Spider-OS1`

`spider-narive-os` is the authoritative bootable implementation because it is the repository that produced the install that actually boots. `Spider-OS1` mirrors the roadmap and migration work without replacing the mature installer/qualification logic.

## Current phase

### Phase 0: Preserve working system
Status: COMPLETE IN GIT

- working baseline branch exists
- main remains untouched by 26.10 base changes
- migration work is isolated from the current booting installation
- current LUKS password unlock behavior remains unchanged

### Phase 1: Ubuntu Studio 26.10 migration foundation
Status: IN PROGRESS

Implemented on `migration/ubuntu-studio-26.10`:

- base configuration points to Ubuntu Studio 26.10 beta
- codename is Stonking Stingray / `stonking`
- beta image naming is centralized in `distro/config/base.env`
- ISO builder now reads base settings from `base.env`
- installed and live Spider OS identity follows the configured base
- GitHub Actions resolves the Spider ISO name from configuration
- build publishing notes follow the configured base
- master plan and dual-repository sync rules are present on the migration branch

Next gate:

- validate the exact 26.10 ISO layer layout
- adapt installer/source handling if 26.10 changed the Casper layout
- build the migration ISO
- boot live image
- install to disposable virtual disk
- remove ISO
- boot installed virtual disk
- verify writable root
- verify Spider Core
- verify Webbie
- verify The Web
- verify backgrounds/workspaces
- reboot installed virtual disk again

Do not merge into `main` until the installed-boot gate passes.

## Shared feature queue after the 26.10 boot gate

1. Rebuild The Web workspace framework and workspace backgrounds.
2. School workspace with SNHU integration and the former Study background.
3. Author workspace with manuscript/canon/research/publishing tools.
4. Spider Studio upgrade on the 26.10 creative stack.
5. Spider Media Center reintegration and qualification.
6. Webbie Jarvis upgrade: continuous voice, modes, permissions, browser/site control, local/online routing, system/app control.
7. Webbie autonomous research plus at least one self-selected learning topic every day.
8. 256 GB Webbie Intelligence Vault.
9. 64 GB Portable AI DJ.
10. Kali Purple / Kali Bay.
11. System + Recovery.
12. Full final qualification.

## Boot safety rule

A feature is not worth losing the currently booting Spider OS.

Any change that touches the base OS, bootloader, initramfs, encryption, Plasma startup, installer, Spider Core startup, Webbie startup, or The Web startup must have a tested rollback path before it is promoted.
