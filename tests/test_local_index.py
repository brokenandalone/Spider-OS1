import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('forage_local_index', ROOT / 'forage/local_index.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class LocalIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'project'; self.source.mkdir()
        self.file = self.source / 'notes.md'; self.file.write_text('river memory café')
        self.index = module.LocalIndex(self.base / 'index/search.sqlite')

    def test_selected_text_search_with_source_provenance_and_unicode(self):
        self.index.rebuild([self.source])
        result = self.index.search('café')[0]
        self.assertEqual(result['path'], str(self.file))
        self.assertEqual(result['url'], self.file.as_uri())
        self.assertEqual(result['root'], str(self.source))
        self.assertEqual(len(result['sha256']), 64)
        self.assertFalse(result['stale'])
        self.assertEqual(self.index.path.stat().st_mode & 0o777, 0o600)

    def test_changed_and_deleted_sources_not_silently_current(self):
        self.index.rebuild([self.source])
        self.file.write_text('changed river story')
        self.assertTrue(self.index.search('river')[0]['stale'])
        self.index.rebuild([self.source])
        self.assertEqual(self.index.search('memory'), [])
        self.file.unlink()
        self.assertEqual(self.index.search('river'), [])
        self.index.rebuild([self.source])
        self.assertEqual(self.index.search('river'), [])

    def test_hidden_credentials_binary_large_and_symlink_files_excluded(self):
        for name in ['.env', 'credentials.json', 'token.json', 'rclone.conf']:
            (self.source / name).write_text('secretneedle')
        hidden = self.source / '.git'; hidden.mkdir(); (hidden / 'secret.txt').write_text('secretneedle')
        (self.source / 'binary.txt').write_bytes(b'secretneedle\x00')
        (self.source / 'large.txt').write_bytes(b'x' * (module.LIMIT + 1))
        external = self.base / 'private.txt'; external.write_text('secretneedle')
        (self.source / 'link.txt').symlink_to(external)
        self.index.rebuild([self.source])
        self.assertEqual(self.index.search('secretneedle'), [])
        self.assertEqual(len(self.index.search('river')), 1)

    def test_failed_refresh_preserves_previous_index(self):
        self.index.rebuild([self.source]); before = self.index.path.read_bytes()
        def interrupted(path):
            raise RuntimeError('interrupted')
        with self.assertRaises(RuntimeError):
            self.index.rebuild([self.source], interrupted)
        self.assertEqual(self.index.path.read_bytes(), before)
        self.assertEqual(len(self.index.search('memory')), 1)
        self.assertEqual(list(self.index.path.parent.glob('.forage-pending-*')), [])

    def test_configured_consent_revocation_applies_before_reindex(self):
        config = self.base / 'selection.json'
        config.write_text(json.dumps({'roots': [str(self.source)]}))
        with patch.object(module, 'CONFIG', config):
            self.index.rebuild()
            self.assertEqual(len(self.index.search('river')), 1)
            config.write_text('{"roots": []}')
            self.assertEqual(self.index.search('river'), [])
            with self.assertRaises(ValueError):
                self.index.rebuild()
            config.unlink()
            self.assertEqual(self.index.search('river'), [])

    def test_no_default_broad_scan_and_explicit_empty_selection_clears_index(self):
        with patch.object(module, 'CONFIG', self.base / 'missing.json'):
            with self.assertRaises(ValueError):
                self.index.rebuild()
        self.index.rebuild([self.source]); self.index.rebuild([])
        self.assertEqual(self.index.search('river'), [])

    def test_root_boundaries_and_symlink_retargeting(self):
        for roots in [[self.base], [self.source, self.source], [self.base, self.source], [Path.home()]]:
            with self.assertRaises(ValueError):
                self.index.rebuild(roots)
        self.index.rebuild([self.source])
        self.file.unlink(); self.file.symlink_to(self.base / 'private.txt')
        (self.base / 'private.txt').write_text('river memory')
        self.assertEqual(self.index.search('river'), [])

    def test_query_syntax_is_text_not_sql_or_fts_operators(self):
        self.index.rebuild([self.source])
        self.assertEqual(self.index.search('"river"')[0]['path'], str(self.file))
        self.assertEqual(self.index.search('" OR 1=1 --'), [])
        self.assertEqual(self.index.search('***'), [])
        with self.assertRaises(ValueError):
            self.index.search('river', 100000)

    def test_index_can_be_rebuilt_after_loss_without_touching_source(self):
        before = self.file.read_bytes()
        self.index.rebuild([self.source]); self.index.path.unlink()
        self.assertEqual(self.index.search('river'), [])
        self.index.rebuild([self.source])
        self.assertEqual(len(self.index.search('river')), 1)
        self.assertEqual(self.file.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
