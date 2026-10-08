#!/usr/bin/env python3
"""Opt-in local snapshots and encrypted cloud copies; no active cloud databases."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
import uuid

DEFAULT_CONFIG = Path.home() / '.config/spider-os/vault.json'
DEFAULT_ROOT = Path.home() / '.local/share/spider-os/vault'
DENIED = {'.ssh', '.gnupg', '.git', 'rclone', 'rclone.conf', 'credentials',
          'credentials.json', 'token.json', 'tokens.json', 'secrets.json', 'id_rsa', 'id_ed25519'}


def excluded(relative, patterns):
    return (any(part.lower() in DENIED or part.lower().startswith('.env')
                or part.lower().endswith(('.pem', '.key')) for part in relative.parts)
            or any(fnmatch.fnmatch(relative.as_posix(), pattern) for pattern in patterns))


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def sqlite_copy(source, destination):
    # Recognize SQLite by header, not filename; the backup API includes committed WAL data.
    with source.open('rb') as handle:
        is_sqlite = handle.read(16) == b'SQLite format 3\x00'
    if not is_sqlite:
        shutil.copyfile(source, destination)
        return
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=5)) as live:
        with closing(sqlite3.connect(destination)) as backup:
            # Bound lock contention; do not hang indefinitely on a busy or broken database.
            started = time.monotonic()
            def progress(status, remaining, total):
                if time.monotonic() - started > 30:
                    raise RuntimeError('SQLite backup timed out')
            live.backup(backup, pages=256, progress=progress)
            backup.execute('PRAGMA journal_mode=DELETE')
            if backup.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise ValueError('SQLite snapshot integrity check failed')


def snapshot(config, root=DEFAULT_ROOT):
    sources = config.get('sources', {})
    if not isinstance(sources, dict) or not sources:
        raise ValueError('Select at least one source directory in vault.json first')
    root = Path(root).expanduser().resolve()
    patterns = config.get('exclude', [])
    if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
        raise ValueError('exclude must be a list of glob patterns')
    limit = int(config.get('max_file_bytes', 64 * 1024 * 1024))
    if limit <= 0:
        raise ValueError('max_file_bytes must be positive')
    validated = {}
    for label, raw in sources.items():
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', label):
            raise ValueError('Source labels must be simple names')
        source = Path(raw).expanduser().resolve(strict=True)
        if source in {Path('/'), Path.home().resolve()}:
            raise ValueError('Select project directories, not the entire home or filesystem')
        if not source.is_dir() or root == source or root.is_relative_to(source) or source.is_relative_to(root):
            raise ValueError('Sources must be directories outside the vault')
        if excluded(source, []):
            raise ValueError('Credential directories cannot be selected')
        validated[label] = source
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    name = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12]
    staging = Path(tempfile.mkdtemp(prefix='.pending-', dir=root))
    try:
        files = {}
        for label, source in validated.items():
            def walk_error(error):
                raise error
            for directory, dirs, names in os.walk(source, followlinks=False, onerror=walk_error):
                base = Path(directory)
                dirs[:] = sorted(d for d in dirs if not (base / d).is_symlink()
                                 and not excluded((base / d).relative_to(source), patterns))
                for item in sorted(names):
                    path = base / item
                    relative = path.relative_to(source)
                    if path.is_symlink() or excluded(relative, patterns) or item.endswith(('-wal', '-shm', '-journal')):
                        continue
                    if not path.is_file():
                        raise ValueError('Only regular files can be backed up')
                    if path.stat().st_size > limit:
                        raise ValueError('A selected file exceeds max_file_bytes; exclude it or raise the limit')
                    destination = staging / 'data' / label / relative
                    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    before = path.stat()
                    sqlite_copy(path, destination)
                    with path.open('rb') as handle:
                        is_sqlite = handle.read(16) == b'SQLite format 3\x00'
                    after = path.stat()
                    if not is_sqlite and (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                        raise ValueError('File changed during snapshot; retry when the project is idle')
                    if destination.stat().st_size > limit:
                        raise ValueError('Snapshot file exceeds max_file_bytes')
                    destination.chmod(0o600)
                    files[destination.relative_to(staging).as_posix()] = {
                        'sha256': digest(destination), 'bytes': destination.stat().st_size}
        if not files:
            raise ValueError('No eligible files in selected sources')
        for directory in staging.rglob('*'):
            if directory.is_dir():
                directory.chmod(0o700)
        manifest = {'schema': 1, 'snapshot': name, 'files': files}
        (staging / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        (staging / 'manifest.json').chmod(0o600)
        verify(staging)
        destination = root / name
        staging.rename(destination)
        return destination
    except BaseException:
        shutil.rmtree(staging)
        raise


def verify(folder):
    folder = Path(folder)
    if folder.is_symlink() or (folder / 'manifest.json').is_symlink():
        raise ValueError('Snapshot symlinks are forbidden')
    folder = folder.resolve(strict=True)
    manifest = json.loads((folder / 'manifest.json').read_text())
    if manifest.get('schema') != 1 or not isinstance(manifest.get('files'), dict) or not manifest['files']:
        raise ValueError('Invalid snapshot manifest')
    for name, entry in manifest['files'].items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or len(relative.parts) < 3 or relative.parts[0] != 'data':
            raise ValueError('Unsafe snapshot path')
        path = folder / relative
        if any((folder / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
            raise ValueError('Snapshot symlinks are forbidden')
        if not path.is_file() or path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError('Snapshot integrity check failed')
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    if actual != set(manifest['files']) | {'manifest.json'} or any(p.is_symlink() for p in folder.rglob('*')):
        raise ValueError('Snapshot contains untracked files or symlinks')
    return manifest


def restore(folder, destination):
    verify(folder)
    source = Path(folder).resolve(strict=True)
    destination = Path(destination).expanduser().absolute()
    resolved = destination.resolve()
    if resolved == source or resolved.is_relative_to(source) or source.is_relative_to(resolved):
        raise ValueError('Restore target must be outside the snapshot')
    if destination.exists() or destination.is_symlink():
        raise ValueError('Restore target must be a new directory; live data is never overwritten')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.restore-', dir=destination.parent))
    try:
        shutil.copytree(Path(folder), staging, dirs_exist_ok=True)
        verify(staging)
        # mkdir provides no-overwrite behavior even if another process created the target.
        destination.mkdir(mode=0o700)
        try:
            for item in staging.iterdir():
                item.rename(destination / item.name)
        except BaseException:
            shutil.rmtree(destination)
            raise
    finally:
        shutil.rmtree(staging)
    return destination


def rclone(args, capture=False):
    try:
        result = subprocess.run(['rclone', *args], stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, text=True, timeout=3600 if not capture else 15)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError('rclone unavailable or timed out') from None
    if result.returncode:
        raise RuntimeError('rclone failed; check local authentication/connectivity')
    return result.stdout if capture else None


def upload(config, folder):
    manifest = verify(folder)
    if config.get('cloud_enabled') is not True:
        raise ValueError('Cloud upload is disabled; explicitly opt in locally first')
    remote = config.get('crypt_remote', '')
    if not re.fullmatch(r'[A-Za-z0-9_-]+:[A-Za-z0-9_/-]+', remote) or '..' in remote.split('/'):
        raise ValueError('Configure a named rclone crypt remote and backup path')
    remotes = json.loads(rclone(['config', 'dump'], capture=True))
    crypt = remotes.get(remote.split(':', 1)[0], {})
    if crypt.get('type') != 'crypt' or crypt.get('filename_encryption', 'standard') != 'standard' or str(crypt.get('directory_name_encryption', 'true')).lower() != 'true':
        raise ValueError('Cloud backup requires crypt content, standard filename and directory encryption')
    underlying = crypt.get('remote', '').split(':', 1)[0]
    if remotes.get(underlying, {}).get('type') != 'onedrive':
        raise ValueError('The crypt remote must wrap the configured OneDrive remote')
    if not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z-[a-f0-9]{12}', manifest.get('snapshot', '')):
        raise ValueError('Invalid snapshot identifier')
    target = remote.rstrip('/') + '/' + manifest['snapshot']
    # New versioned folders only. Never mirror-delete, overwrite conflicts or mount a live DB.
    rclone(['copy', str(folder), target, '--immutable'])
    rclone(['check', str(folder), target, '--download'])
    return target


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('snapshot')
    for command in ('verify', 'upload', 'restore'):
        child = sub.add_parser(command)
        child.add_argument('snapshot', type=Path)
        if command == 'restore':
            child.add_argument('destination', type=Path)
    sub.add_parser('scheduled')
    args = parser.parse_args()
    try:
        if args.command in {'snapshot', 'upload', 'scheduled'}:
            config = json.loads(args.config.read_text())
        if args.command == 'snapshot':
            print(snapshot(config, args.root))
        elif args.command == 'verify':
            verify(args.snapshot)
            print('Snapshot verified.')
        elif args.command == 'restore':
            print(restore(args.snapshot, args.destination))
        elif args.command == 'upload':
            upload(config, args.snapshot)
            print('Encrypted cloud copy verified.')
        elif args.command == 'scheduled':
            folder = snapshot(config, args.root)
            if config.get('cloud_enabled') is True:
                upload(config, folder)
            print('Scheduled snapshot verified.')
    except (OSError, ValueError, RuntimeError, sqlite3.Error, KeyError, TypeError) as error:
        parser.exit(1, f'Vault: {error}\n')


if __name__ == '__main__':
    main()
