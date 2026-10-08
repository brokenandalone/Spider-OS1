import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('action_gateway', ROOT / 'webbie/actions/gateway.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.now = 1000
        self.executor = Mock(return_value={'performed': True})
        self.gateway = module.Gateway(Path(self.temp.name) / 'state', self.executor, lambda: self.now)

    def test_health_safe_and_mode_specific_open(self):
        self.assertEqual(self.gateway.request('system.health')['status'], 'completed')
        result = self.gateway.request('workspace.open', {'workspace': 'author'})
        self.assertEqual(result['mode'], 'Author Editor')
        self.executor.assert_called_with('workspace.open', {'workspace': 'author'})

    def test_snapshot_and_restart_wait_for_request_bound_approval(self):
        pending = self.gateway.request('vault.snapshot')
        self.assertEqual(pending['level'], 2)
        self.executor.assert_not_called()
        restart = self.gateway.request('service.restart', {'service': 'webbie'})
        self.assertEqual(restart['level'], 3)
        self.executor.assert_not_called()
        with self.assertRaises(ValueError):
            self.gateway.approve(restart['id'], 'vault.snapshot')
        self.executor.assert_not_called()
        result = self.gateway.approve(restart['id'], 'service.restart')
        self.assertEqual(result['status'], 'completed')
        self.executor.assert_called_once_with('service.restart', {'service': 'webbie'})
        with self.assertRaises(ValueError):
            self.gateway.approve(restart['id'], 'service.restart')

    def test_expiration_and_denial_prevent_execution(self):
        pending = self.gateway.request('vault.snapshot')
        self.now += 300
        with self.assertRaises(ValueError):
            self.gateway.approve(pending['id'], 'vault.snapshot')
        self.assertEqual(self.gateway.pending(), [])
        pending = self.gateway.request('vault.snapshot')
        self.gateway.deny(pending['id'])
        with self.assertRaises(ValueError):
            self.gateway.approve(pending['id'], 'vault.snapshot')
        self.executor.assert_not_called()

    def test_forged_voice_and_unknown_actions_rejected(self):
        for source in ('voice', 'network', 'Cory', 'Shayna'):
            with self.assertRaises(PermissionError):
                self.gateway.request('system.health', source=source)
        for action, params in [('shell.run', {'command': 'id'}),
                               ('service.restart', {'service': 'ollama'}),
                               ('workspace.open', {'workspace': 'studio', 'command': 'id'}),
                               ('system.health', {'approved': True})]:
            with self.assertRaises(ValueError):
                self.gateway.request(action, params)
        self.executor.assert_not_called()

    def test_approval_survives_process_restart_but_cannot_replay(self):
        pending = self.gateway.request('vault.snapshot')
        reopened = module.Gateway(self.gateway.directory, self.executor, lambda: self.now)
        self.assertEqual(reopened.pending()[0]['id'], pending['id'])
        reopened.approve(pending['id'], 'vault.snapshot')
        with self.assertRaises(ValueError):
            self.gateway.approve(pending['id'], 'vault.snapshot')
        self.executor.assert_called_once()
        self.assertEqual(self.gateway.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.gateway.directory.stat().st_mode & 0o777, 0o700)

    def test_failed_execution_not_success_or_reusable_approval(self):
        self.executor.side_effect = RuntimeError('private-token=do-not-print')
        pending = self.gateway.request('vault.snapshot')
        result = self.gateway.approve(pending['id'], 'vault.snapshot')
        self.assertEqual(result['status'], 'failed')
        self.assertNotIn('private-token', json.dumps(result))
        with self.assertRaises(ValueError):
            self.gateway.approve(pending['id'], 'vault.snapshot')

    def test_sql_parameters_bound_and_owner_checked(self):
        pending = self.gateway.request('vault.snapshot')
        with self.assertRaises(ValueError):
            self.gateway.approve("' OR 1=1 --", 'vault.snapshot')
        with sqlite3.connect(self.gateway.path) as db:
            db.execute('UPDATE requests SET owner=? WHERE id=?', (os.getuid() + 1, pending['id']))
        with self.assertRaises(ValueError):
            self.gateway.approve(pending['id'], 'vault.snapshot')
        self.executor.assert_not_called()

    def test_database_symlink_rejected(self):
        path = Path(self.temp.name) / 'other'; path.mkdir()
        (path / 'requests.sqlite').symlink_to(self.gateway.path)
        with self.assertRaises(OSError):
            module.Gateway(path)

    def test_local_snapshot_handler_never_uploads(self):
        with patch.object(module.vault.DEFAULT_CONFIG.__class__, 'read_text', return_value='{}'), \
             patch.object(module.vault, 'snapshot', return_value=Path('/local/backup')) as snapshot, \
             patch.object(module.vault, 'upload') as upload:
            result = module.perform('vault.snapshot', {})
            self.assertFalse(result['cloud_upload'])
            snapshot.assert_called_once_with({}); upload.assert_not_called()

    def test_restart_is_fixed_user_service_and_requires_active_result(self):
        from types import SimpleNamespace
        with patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
            self.assertTrue(module.perform('service.restart', {'service': 'webbie'})['active'])
            self.assertEqual(run.call_args_list[0].args[0], ['systemctl', '--user', 'restart', 'webbie.service'])
            self.assertEqual(run.call_args_list[1].args[0], ['systemctl', '--user', 'is-active', '--quiet', 'webbie.service'])
            self.assertTrue(all('shell' not in call.kwargs for call in run.call_args_list))
        with patch.object(module.subprocess, 'run', side_effect=[SimpleNamespace(returncode=0), SimpleNamespace(returncode=3)]):
            with self.assertRaises(RuntimeError):
                module.perform('service.restart', {'service': 'ai-dj'})

    def test_mode_uses_workspace_and_falls_back_safely(self):
        self.assertEqual(module.mode_for('study'), 'School Tutor')
        self.assertEqual(module.mode_for('studio'), 'Studio Producer')
        self.assertEqual(module.mode_for('kali-bay'), 'Security Assistant')
        self.assertEqual(module.mode_for('unknown'), 'Normal')


if __name__ == '__main__':
    unittest.main()
