# Spider OS In-Place Upgrade Path

The preferred migration path is now an in-place staged upgrade. A fresh installer is a fallback, not the default.

## Stage A: 24.04.5 -> 26.04.1 LTS

Ubuntu officially enables the 24.04 LTS to 26.04.1 LTS release upgrade through `do-release-upgrade`.

Before starting:

1. Run `distro/preflight-inplace-upgrade.sh`.
2. Review disk/LUKS/GRUB/boot-mode/package/service state.
3. Create an external backup of personal and Spider project data.
4. Preserve the current LUKS unlock flow.
5. Record a known-good rollback point.
6. Make sure Spider Core, Webbie, The Web, networking and storage are healthy.
7. Do not proceed if the package manager is broken or root free space is inadequate.

Then fully update the current 24.04 installation before invoking the release upgrader.

After the 26.04.1 upgrade, reboot and qualify Spider OS before any further release transition.

## Stage B: 26.04.1 -> 26.10

Do not move to 26.10 until:

- 26.04.1 boots reliably
- LUKS unlock works
- GRUB/initramfs work
- KDE works
- networking and audio work
- Spider Core works
- Webbie works
- The Web works
- a second reboot succeeds

When Ubuntu Studio 26.10 final is available and the system is configured to follow interim releases, perform the next supported release upgrade.

## Installer fallback

A clean Spider OS 26.10 installer remains a tested recovery/fallback path. It is not the preferred migration method unless the in-place path fails or produces an unstable system.

## Safety rule

Never use `do-release-upgrade -d` on the only known-good Spider OS installation just to reach the 26.10 beta.
