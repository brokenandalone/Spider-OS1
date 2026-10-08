#!/usr/bin/env python3
"""Bounded, read-only Spider OS diagnostics. Never collect private logs or configs."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from datetime import datetime, timezone

SERVICES = {
    'spider-core': (False, 'spider-os.service'),
    'webbie': (True, 'webbie.service'),
    'ollama': (False, 'ollama.service'),
    'ai-dj': (True, 'spider-ai-dj.service'),
}


def probe(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        return result.returncode, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None, ''


def health():
    services = {}
    for name, (user, unit) in SERVICES.items():
        code, output = probe(['systemctl', *(['--user'] if user else []),
                              'show', unit, '--property=ActiveState', '--value'])
        services[name] = output if code == 0 and output in {
            'active', 'inactive', 'failed', 'activating', 'deactivating', 'reloading'
        } else 'unavailable'
    _, plasma = probe(['plasmashell', '--version'])
    _, audio = probe(['arecord', '-l'])
    _, network = probe(['nmcli', '-t', '-f', 'STATE', 'general'])
    disk = shutil.disk_usage(Path.home())
    release = {}
    try:
        for line in Path('/etc/os-release').read_text().splitlines():
            key, _, value = line.partition('=')
            if key in {'NAME', 'VERSION_ID', 'VERSION_CODENAME'}:
                release[key] = value.strip('"')
    except OSError:
        pass
    return {
        'schema': 1, 'collected_at': datetime.now(timezone.utc).isoformat(),
        'os': release, 'kernel': platform.release(),
        'plasma': plasma if plasma.startswith('plasmashell ') else 'unavailable',
        'services': services,
        'storage': {'total_bytes': disk.total, 'free_bytes': disk.free,
                    'free_percent': round(100 * disk.free / disk.total, 1)},
        'network': network if network in {'connected', 'connecting', 'disconnected',
                                         'connected (local only)', 'connected (site only)'}
                    else 'unavailable',
        'microphone_present': 'card ' in audio,
        'tools': {name: bool(shutil.which(name)) for name in
                  ('python3', 'rclone', 'whisper-cli', 'ollama', 'podman', 'distrobox')},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--bundle', type=Path, help='Write a private JSON report; refuses overwrite')
    args = parser.parse_args()
    report = health()
    if args.bundle:
        fd = os.open(args.bundle, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as handle:
            json.dump(report, handle, indent=2)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print('SPIDER GUARDIAN')
        print(f"Kernel: {report['kernel']}  Plasma: {report['plasma']}")
        for name, state in report['services'].items():
            print(f'{name}: {state}')
        print(f"Storage free: {report['storage']['free_percent']}%")
        print(f"Network: {report['network']}  Capture device: {report['microphone_present']}")
        print('Service activity does not prove conversation or broadcast playback works.')


if __name__ == '__main__':
    main()
