#!/usr/bin/env python3
"""Local action registry and request-bound approvals. No arbitrary shell or voice bypass."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'system'))
import apps
import guardian
import vault

MODES = {
    'default': 'Normal', 'webbie': 'Normal', 'study': 'School Tutor',
    'school': 'School Tutor', 'author': 'Author Editor', 'studio': 'Studio Producer',
    'media': 'AI DJ', 'forage': 'Researcher', 'deep-forage': 'Researcher',
    'dev-bay': 'Developer', 'system': 'System Technician', 'kali-bay': 'Security Assistant',
}
MODE_GUIDANCE = {
    'Normal': 'Assist with everyday Spider OS tasks; report only observed results.',
    'School Tutor': 'Use active course resources and rubrics; distinguish evidence from inference.',
    'Author Editor': 'Check project canon and propose edits; manuscript changes require approval.',
    'Studio Producer': 'Support songwriting, recording and production; preserve project files.',
    'AI DJ': 'Distinguish playback, service activity and broadcast state; verify before claiming on air.',
    'Researcher': 'Track sources and confidence; research does not authorize code or policy changes.',
    'Developer': 'Explain and validate changes; project edits require request-bound approval.',
    'System Technician': 'Diagnose first; service changes require explicit confirmation.',
    'Security Assistant': 'Use authorized isolated environments; do not modify the host security policy.',
}
LEVELS = {'system.health': 1, 'workspace.open': 1, 'vault.snapshot': 2, 'service.restart': 3}
USER_SERVICES = {'webbie': 'webbie.service', 'ai-dj': 'spider-ai-dj.service'}
DEFAULT_STATE = Path.home() / '.local/state/spider-os/action-gateway'


def mode_for(workspace=None):
    if workspace is None:
        runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
        try:
            workspace = (runtime / 'spider-os/workspace').read_text().strip()
        except OSError:
            workspace = 'default'
    return MODES.get(workspace, 'Normal')


def validate(action, params):
    if action not in LEVELS or not isinstance(params, dict):
        raise ValueError('Unknown action or invalid parameters')
    expected = {'workspace.open': {'workspace'}, 'service.restart': {'service'}}.get(action, set())
    if set(params) != expected:
        raise ValueError('Unexpected or missing action parameters')
    if action == 'workspace.open' and params['workspace'] not in {
        'studio', 'author', 'media', 'study', 'school', 'forage', 'deep-forage', 'kali-bay', 'system'
    }:
        raise ValueError('Unsupported workspace')
    if action == 'service.restart' and params['service'] not in USER_SERVICES:
        raise ValueError('Only Webbie and AI DJ user services may be restarted')


def perform(action, params):
    if action == 'system.health':
        return guardian.health()
    if action == 'vault.snapshot':
        config = json.loads(vault.DEFAULT_CONFIG.read_text())
        path = vault.snapshot(config)
        return {'snapshot': str(path), 'verified': True, 'cloud_upload': False}
    if action == 'service.restart':
        unit = USER_SERVICES[params['service']]
        subprocess.run(['systemctl', '--user', 'restart', unit], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        result = subprocess.run(['systemctl', '--user', 'is-active', '--quiet', unit],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        if result.returncode:
            raise RuntimeError('Restart completed but service did not become active')
        return {'service': params['service'], 'active': True}
    if action == 'workspace.open':
        workspace = params['workspace']
        if workspace == 'author':
            apps.launch_author()
        else:
            if workspace == 'studio':
                command = apps.studio_command(ROOT)
            elif workspace == 'media':
                command = apps.media_command()
            elif workspace in {'study', 'school'}:
                command = ['python3', str(ROOT / 'study/study.py')]
            elif workspace == 'forage':
                command = ['python3', str(ROOT / 'forage/forage.py')]
            elif workspace == 'deep-forage':
                command = ['python3', str(ROOT / 'forage/deep-forage/deep_forage.py')]
            elif workspace == 'kali-bay':
                command = [str(ROOT / 'kali-bay/bin/kali-bay')]
            else:
                report = guardian.health()
                apps.select_workspace(workspace)
                return {'workspace': workspace, 'report': report}
            if command[0] == 'python3' and not Path(command[1]).is_file():
                raise RuntimeError('Workspace module is not installed')
            subprocess.Popen(command, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            apps.select_workspace('study' if workspace == 'school' else workspace)
        # Starting a process is not proof its window reached a working state.
        return {'workspace': workspace, 'launch_requested': True}
    raise ValueError('Unsupported action')


class Gateway:
    """Trusted same-user local API. Voice adapters must independently authorize speakers."""
    def __init__(self, directory=DEFAULT_STATE, executor=perform, clock=time.time):
        self.directory = Path(directory).expanduser()
        if self.directory.is_symlink():
            raise ValueError('Action state must not be a symlink')
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        info = self.directory.stat()
        if info.st_uid != os.getuid():
            raise ValueError('Action state belongs to another user')
        self.directory.chmod(0o700)
        self.path = self.directory / 'requests.sqlite'
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                raise ValueError('Invalid action state database')
            os.fchmod(fd, 0o600)
        finally:
            os.close(fd)
        self.executor = executor
        self.clock = clock
        with closing(self.connect()) as db:
            db.execute('''CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY, action TEXT NOT NULL, params TEXT NOT NULL,
                mode TEXT NOT NULL, level INTEGER NOT NULL, created REAL NOT NULL,
                expires REAL NOT NULL, status TEXT NOT NULL, owner INTEGER NOT NULL
            )''')
            db.commit()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def request(self, action, params=None, source='local'):
        # No identity assertions from a model, JSON payload or voice transcription are accepted.
        if source != 'local':
            raise PermissionError('Voice/network adapters are not connected to this gateway')
        params = {} if params is None else params
        validate(action, params)
        identifier = uuid.uuid4().hex
        now = self.clock()
        level = LEVELS[action]
        mode = mode_for(params.get('workspace'))
        status = 'running' if level == 1 else 'pending'
        encoded = json.dumps(params, sort_keys=True, separators=(',', ':'))
        with closing(self.connect()) as db:
            db.execute('INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?)',
                       (identifier, action, encoded, mode, level, now, now + 300, status, os.getuid()))
            db.commit()
        if level == 1:
            return self.run(identifier, action, params, mode)
        return {'id': identifier, 'status': 'approval_required', 'level': level,
                'action': action, 'params': params, 'mode': mode, 'expires_in_seconds': 300}

    def approve(self, identifier, confirmed_action):
        # Approval must come from the local user-facing control, never the language model.
        with closing(self.connect()) as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM requests WHERE id=?', (identifier,)).fetchone()
            if row is None or row['owner'] != os.getuid() or row['status'] != 'pending':
                raise ValueError('Request is missing, already used or owned by another user')
            if self.clock() >= row['expires']:
                db.execute("UPDATE requests SET status='expired' WHERE id=?", (identifier,))
                db.commit()
                raise ValueError('Approval request expired; create a new request')
            if confirmed_action != row['action']:
                raise ValueError('Confirmation does not match the pending action')
            action = row['action']
            params = json.loads(row['params'])
            validate(action, params)
            if LEVELS[action] != row['level'] or row['level'] not in {2, 3}:
                raise ValueError('Request policy mismatch')
            db.execute("UPDATE requests SET status='running' WHERE id=?", (identifier,))
            db.commit()
        return self.run(identifier, action, params, row['mode'])

    def run(self, identifier, action, params, mode):
        try:
            result = self.executor(action, params)
        except Exception:
            self.finish(identifier, 'failed')
            # No private paths, config values, stdout or tokens in audit/error messages.
            return {'id': identifier, 'status': 'failed', 'action': action,
                    'mode': mode, 'error': 'Action failed; inspect the module locally. Do not assume it succeeded.'}
        self.finish(identifier, 'completed')
        return {'id': identifier, 'status': 'completed', 'action': action, 'mode': mode, 'result': result}

    def finish(self, identifier, status):
        with closing(self.connect()) as db:
            db.execute('UPDATE requests SET status=? WHERE id=?', (status, identifier))
            db.commit()

    def pending(self):
        with closing(self.connect()) as db:
            db.execute("UPDATE requests SET status='expired' WHERE status='pending' AND expires<=?", (self.clock(),))
            db.commit()
            rows = db.execute("SELECT id,action,params,mode,level,expires FROM requests WHERE status='pending' AND owner=? ORDER BY created", (os.getuid(),)).fetchall()
        return [{**dict(row), 'params': json.loads(row['params'])} for row in rows]

    def deny(self, identifier):
        with closing(self.connect()) as db:
            cursor = db.execute("UPDATE requests SET status='denied' WHERE id=? AND status='pending' AND owner=?", (identifier, os.getuid()))
            db.commit()
            if cursor.rowcount != 1:
                raise ValueError('No pending request to deny')
        return {'id': identifier, 'status': 'denied'}


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', type=Path, default=DEFAULT_STATE)
    commands = parser.add_subparsers(dest='command', required=True)
    request = commands.add_parser('request')
    request.add_argument('action', choices=LEVELS)
    request.add_argument('--params', default='{}', help='JSON action parameters; no shell commands')
    approve = commands.add_parser('approve')
    approve.add_argument('id')
    approve.add_argument('--confirm-action', required=True, choices=LEVELS)
    deny = commands.add_parser('deny'); deny.add_argument('id')
    commands.add_parser('pending')
    commands.add_parser('mode')
    args = parser.parse_args()
    try:
        if args.command == 'mode':
            mode = mode_for()
            print(json.dumps({'mode': mode, 'guidance': MODE_GUIDANCE[mode]})); return
        gateway = Gateway(args.state_dir)
        if args.command == 'request':
            result = gateway.request(args.action, json.loads(args.params))
        elif args.command == 'approve':
            result = gateway.approve(args.id, args.confirm_action)
        elif args.command == 'deny':
            result = gateway.deny(args.id)
        else:
            result = gateway.pending()
        print(json.dumps(result, indent=2))
        if isinstance(result, dict) and result.get('status') == 'failed':
            raise SystemExit(1)
    except (OSError, ValueError, TypeError, sqlite3.Error, PermissionError):
        parser.exit(1, 'Gateway: invalid request or unavailable local state. No action was approved.\n')


if __name__ == '__main__':
    main()
