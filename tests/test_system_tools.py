"""Exercise recovery, live WAL snapshots, opt-in cloud policy and bounded diagnostics."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'system' / f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


vault = module('vault')
guardian = module('guardian')


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        self.source.mkdir()
        (self.source / 'notes.txt').write_text('saved locally')
        self.config = {'sources': {'school': str(self.source)}}
        self.root = self.base / 'vault'

    def snapshot(self):
        return vault.snapshot(self.config, self.root)

    def test_committed_wal_included_and_restore_survives_source_loss(self):
        connection = sqlite3.connect(self.source / 'memory')
        self.addCleanup(connection.close)
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('CREATE TABLE memories (text TEXT)')
        connection.execute("INSERT INTO memories VALUES ('remember this')")
        connection.commit()
        self.assertTrue((self.source / 'memory-wal').exists())
        folder = self.snapshot()
        manifest = vault.verify(folder)
        self.assertNotIn('data/school/memory-wal', manifest['files'])
        restored = vault.restore(folder, self.base / 'restored')
        (self.source / 'notes.txt').unlink()
        with sqlite3.connect(restored / 'data/school/memory') as backup:
            self.assertEqual(backup.execute('SELECT text FROM memories').fetchone()[0], 'remember this')
        self.assertEqual((restored / 'data/school/notes.txt').read_text(), 'saved locally')
        self.assertEqual((restored / 'data/school/notes.txt').stat().st_mode & 0o777, 0o600)

    def test_private_credentials_links_and_explicit_exclusions_omitted(self):
        (self.source / '.env.local').write_text('a token')
        (self.source / 'private.key').write_text('key')
        (self.source / 'rclone.conf').write_text('credentials')
        (self.source / 'ignore.log').write_text('private log')
        (self.source / 'link.txt').symlink_to(self.source / 'notes.txt')
        (self.source / '.ssh').mkdir()
        (self.source / '.ssh/config').write_text('private')
        self.config['exclude'] = ['*.log']
        manifest = vault.verify(self.snapshot())
        self.assertEqual(set(manifest['files']), {'data/school/notes.txt'})

    def test_corruption_untracked_files_and_symlinks_block_restore(self):
        folder = self.snapshot()
        (folder / 'data/school/notes.txt').write_text('tampered')
        with self.assertRaises(ValueError):
            vault.restore(folder, self.base / 'restored')
        self.assertFalse((self.base / 'restored').exists())
        folder = self.snapshot()
        (folder / 'extra').write_text('not tracked')
        with self.assertRaises(ValueError):
            vault.verify(folder)
        (folder / 'extra').unlink()
        (folder / 'empty-link').symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            vault.verify(folder)

    def test_traversal_and_existing_restore_target_rejected(self):
        folder = self.snapshot()
        with self.assertRaises(ValueError):
            vault.restore(folder, self.source)
        with self.assertRaises(ValueError):
            vault.restore(folder, folder / 'nested')
        manifest = vault.verify(folder)
        manifest['files']['data/../../escape'] = {'sha256': '', 'bytes': 0}
        (folder / 'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            vault.verify(folder)

    def test_selection_limits_and_no_pending_partial_snapshot(self):
        with self.assertRaises(ValueError):
            vault.snapshot({'sources': {}}, self.root)
        with self.assertRaises(ValueError):
            vault.snapshot(self.config, self.source / 'nested')
        self.config['max_file_bytes'] = 1
        with self.assertRaises(ValueError):
            self.snapshot()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_local_snapshot_never_calls_network_and_is_versioned(self):
        with patch.object(vault, 'rclone', side_effect=AssertionError('network used')):
            first = self.snapshot()
            second = self.snapshot()
            self.assertNotEqual(first, second)
            vault.verify(first)
            vault.verify(second)

    def test_cloud_disabled_and_plaintext_remote_rejected(self):
        folder = self.snapshot()
        with patch.object(vault, 'rclone') as network:
            with self.assertRaisesRegex(ValueError, 'disabled'):
                vault.upload(self.config, folder)
            network.assert_not_called()
        self.config.update(cloud_enabled=True, crypt_remote='plain:SpiderOS')
        with patch.object(vault, 'rclone', return_value=json.dumps({'plain': {'type': 'onedrive'}})) as network:
            with self.assertRaisesRegex(ValueError, 'requires crypt'):
                vault.upload(self.config, folder)
            self.assertEqual(network.call_count, 1)

    def test_encrypted_upload_never_deletes_and_checks_content(self):
        folder = self.snapshot()
        self.config.update(cloud_enabled=True, crypt_remote='secure:SpiderOS')
        remotes = {'secure': {'type': 'crypt', 'remote': 'onedrive:Backups'},
                   'onedrive': {'type': 'onedrive', 'token': 'must never be printed'}}
        with patch.object(vault, 'rclone', side_effect=[json.dumps(remotes), None, None]) as network:
            target = vault.upload(self.config, folder)
            self.assertTrue(target.startswith('secure:SpiderOS/'))
            self.assertEqual(network.call_args_list[1].args[0], ['copy', str(folder), target, '--immutable'])
            self.assertEqual(network.call_args_list[2].args[0], ['check', str(folder), target, '--download'])
        remotes['secure']['filename_encryption'] = 'off'
        with patch.object(vault, 'rclone', return_value=json.dumps(remotes)):
            with self.assertRaises(ValueError):
                vault.upload(self.config, folder)


class GuardianTests(unittest.TestCase):
    def test_unavailable_services_and_tools_do_not_crash_health(self):
        with patch.object(guardian, 'probe', return_value=(None, '')):
            report = guardian.health()
        self.assertTrue(all(state == 'unavailable' for state in report['services'].values()))
        self.assertEqual(report['plasma'], 'unavailable')
        self.assertNotIn('logs', report)
        self.assertNotIn('hostname', report)
        self.assertGreater(report['storage']['total_bytes'], 0)

    def test_probe_bounds_subprocess_and_discards_stderr(self):
        with patch.object(guardian.subprocess, 'run', side_effect=guardian.subprocess.TimeoutExpired('test', 5)) as call:
            self.assertEqual(guardian.probe(['missing']), (None, ''))
            self.assertEqual(call.call_args.kwargs['timeout'], 5)


if __name__ == '__main__':
    unittest.main()
