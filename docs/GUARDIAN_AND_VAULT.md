# Spider Guardian and OneDrive Vault

Source batch: 2026-10-08 UTC. These tools are implemented in GitHub, not evidence of installation on the owner's PC. The encrypted boot path, Webbie voice code, existing media package and desktop shell are preserved.

## Guardian

After installation, run:

```bash
/usr/local/lib/spider-os/system/bin/spider-guardian
/usr/local/lib/spider-os/system/bin/spider-guardian --json
/usr/local/lib/spider-os/system/bin/spider-guardian --bundle guardian-report.json
```

The read-only report includes the actual OS/kernel/Plasma versions, bounded service probes, free storage, network state, capture-device presence and installed-tool availability. It omits journal contents, microphone recordings, private configuration, network addresses and credentials. Reports are created with mode 0600 and an existing file is never overwritten. Service activity does not establish radio playback, authorized voice recognition or successful conversation. Repair actions and a graphical dashboard remain separate work.

## Select local backup sources

Copy `system/config/vault.example.json` to `~/.config/spider-os/vault.json`, with permissions 0600, and explicitly select directories. The shipped example selects nothing and disables cloud upload. Example selection, to adapt to the actual local paths:

```json
{
  "cloud_enabled": false,
  "crypt_remote": "",
  "sources": {
    "school": "~/Documents/Spider OS/Study",
    "author": "~/Documents/Spider OS/Author"
  },
  "exclude": ["*.log", "models/*", "*.gguf", "*.bin"],
  "max_file_bytes": 67108864
}
```

Only select projects whose contents you want backed up. Each selected source must exist. Missing sources, unreadable files, changed files or size limits fail the snapshot rather than silently declaring a complete backup. Symlinks, common credential paths/files and SQLite sidecars are excluded. This exclusion list is defense in depth; review selected projects for embedded secrets. The tool refuses whole-home and whole-filesystem selection.

Run `spider-vault` using the full path `/usr/local/lib/spider-os/system/bin/spider-vault` (or `system/bin/spider-vault` in a checkout):

```bash
spider-vault snapshot
spider-vault verify /path/to/snapshot
spider-vault restore /path/to/snapshot /path/to/new-recovery-directory
```

Snapshot output supplies the actual versioned folder path. It contains a hash manifest and `data/<source-label>/...`. SQLite files are detected by header and copied through the SQLite backup API, including committed WAL data; each resulting database is checked and made standalone. Ordinary files must remain stable during their copy. This is a per-file snapshot, not a transaction across several databases or projects; pause project edits for an application-wide consistent restore point.

Snapshots remain on local storage in `~/.local/share/spider-os/vault`, with an optional `--root` override. Copies are staged and verified before publication. Restore verifies all files and refuses an existing destination. Inspect the recovered project before moving it into active storage. No active database is opened on OneDrive. There is no automatic retention deletion; monitor local space and remove obsolete backups deliberately. Local snapshots are private by filesystem permissions, not separately encrypted; protect their underlying disk.

## Optional encrypted OneDrive upload

Configure rclone locally through its supported OneDrive authentication flow. Create a `crypt` remote wrapping the OneDrive backup directory, with standard filename encryption and directory encryption enabled. Keep tokens, passwords and recovery keys out of Git. Preserve the crypt password in a user-controlled recovery method; losing it makes the encrypted cloud backups unusable.

Then set `cloud_enabled` to `true` and `crypt_remote` to a path such as `spider-vault-crypt:SpiderOS` in the local configuration. The tool checks that this named remote is crypt and wraps OneDrive before transfer. A plaintext OneDrive remote is rejected.

```bash
spider-vault upload /path/to/verified-snapshot
```

Uploads use new versioned folders, immutable copy semantics and a download-based content check. They do not mirror-delete cloud files or overwrite conflicting versions. Failure leaves the local snapshot available; partial remote copies can be retried. Nothing is uploaded merely by installing the tool or enabling local snapshots.

To restore from cloud, copy the chosen remote snapshot through the crypt remote with rclone to a fresh local directory, run `spider-vault verify`, then run `spider-vault restore` into a separate new recovery directory. The live OneDrive authentication and encrypted round-trip need qualification on the PC.

References: [rclone crypt](https://rclone.org/crypt/) and [download-based content verification](https://rclone.org/commands/rclone_check/).

## Optional daily scheduling

The ISO packages the user service and timer, but does not enable them. On an existing installation, deploy the `system/` payload under `/usr/local/lib/spider-os/system` and install `system/service/spider-vault.*` into the user systemd unit search path. Do not replace other installed components from an older checkout.

After selecting and testing sources, enable deliberately:

```bash
systemctl --user daemon-reload
systemctl --user enable --now spider-vault.timer
```

Disable with `systemctl --user disable --now spider-vault.timer`. The service creates a local snapshot and uploads it only when cloud upload is explicitly enabled. It never starts/stops Webbie, alters voice authorization, installs packages or edits boot configuration.

## Validation and remaining gates

The source regression suite covers committed live-WAL recovery, restoration after source loss, corruption, path traversal, symlinks, untracked files, credential exclusions, size limits, offline operation, unique versioning, disabled cloud behavior, plaintext-remote rejection and bounded diagnostic failures. GitHub source checks run on pushes and pull requests using the pinned Ubuntu 24.04 runner; ISO builds remain separately dispatched and retain their install/reboot qualification.

Installed-machine health, OneDrive authentication, encrypted upload/download, user timer behavior and an actual recovery exercise remain unchecked in the master checklist until tested on their named environment. No installed phase is declared complete by source tests alone.
