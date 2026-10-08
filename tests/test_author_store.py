import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('author_store', Path(__file__).resolve().parents[1] / 'author/store.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class AuthorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = module.AuthorStore(self.temp.name)
        self.book = self.store.create_book('Book')
        self.chapter = self.store.create_chapter(self.book, 'One', 'Original')

    def tearDown(self):
        self.store.close(); self.temp.cleanup()

    def test_snapshots_restore_and_reopen(self):
        self.store.save(self.chapter, 'New')
        self.store.save(self.chapter, 'New')
        versions = self.store.snapshots(self.chapter)
        self.assertEqual(len(versions), 1)
        self.store.restore(self.chapter, versions[0]['id'])
        self.store.close(); self.store = module.AuthorStore(self.temp.name)
        self.assertEqual(self.store.chapter(self.chapter)['content'], 'Original')
        self.assertEqual(self.store.snapshots(self.chapter)[0]['content'], 'New')

    def test_restore_rejects_another_chapters_snapshot(self):
        self.store.save(self.chapter, 'New')
        other = self.store.create_chapter(self.book, 'Other', 'Keep')
        with self.assertRaises(ValueError):
            self.store.restore(other, self.store.snapshots(self.chapter)[0]['id'])
        self.assertEqual(self.store.chapter(other)['content'], 'Keep')

    def test_backup_contains_latest_text_and_canon(self):
        self.store.save(self.chapter, 'Latest'); self.store.save_canon(self.book, 'Rule')
        target = Path(self.temp.name) / 'backup.sqlite3'; self.store.backup(target)
        import sqlite3
        with sqlite3.connect(target) as backup:
            self.assertEqual(backup.execute('SELECT content FROM chapters').fetchone()[0], 'Latest')
            self.assertEqual(backup.execute('SELECT canon FROM books').fetchone()[0], 'Rule')
        with self.assertRaises(ValueError):
            self.store.backup(Path(self.temp.name) / 'library.sqlite3')

    def test_import_is_non_destructive_and_idempotent(self):
        path = Path(self.temp.name) / 'bundle.json'
        path.write_text(json.dumps({'format':'spider-author-1', 'books':[
            {'title':'Imported', 'chapters':[{'title':'One', 'content':'Text'}]}]}))
        self.assertEqual(self.store.import_bundle(path), 1)
        self.assertEqual(self.store.import_bundle(path), 0)
        self.assertEqual(self.store.chapter(self.chapter)['content'], 'Original')
        self.assertEqual(len(self.store.books()), 2)

    def test_bad_import_rolls_back_the_entire_batch(self):
        path = Path(self.temp.name) / 'bundle.json'
        path.write_text(json.dumps({'format':'spider-author-1', 'books':[
            {'title':'Good', 'chapters':[]}, {'title':'Bad', 'chapters':[{'title':'One'}]}]}))
        with self.assertRaises(ValueError):
            self.store.import_bundle(path)
        self.assertEqual(len(self.store.books()), 1)

    def test_import_keeps_original_file_and_text(self):
        path = Path(self.temp.name) / 'scene.md'; path.write_text('Scene')
        chapter = self.store.import_text(self.book, path)
        self.assertEqual(path.read_text(), 'Scene')
        self.assertEqual(self.store.chapter(chapter)['content'], 'Scene')
