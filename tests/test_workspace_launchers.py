import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workspace_apps', ROOT / 'system/apps.py')
apps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apps)


class WorkspaceLauncherTests(unittest.TestCase):
    def test_missing_media_payload_is_not_installed_just_because_wrapper_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(apps.AppUnavailable):
                apps.media_command(Path(directory), lambda name: '/usr/local/bin/' + name)

    def test_new_media_center_preferred_and_legacy_environment_wrapper_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            opt = Path(directory)
            legacy = opt / 'spider-media-player/spider-media-player'
            legacy.parent.mkdir()
            legacy.write_text('#!/bin/sh\n'); legacy.chmod(0o755)
            self.assertEqual(apps.media_command(opt, lambda name: '/usr/local/bin/' + name),
                             ['/usr/local/bin/spider-media-player'])
            center = opt / 'spider-media-center/spider-media-center'
            center.parent.mkdir()
            center.write_text('#!/bin/sh\n'); center.chmod(0o755)
            self.assertEqual(apps.media_command(opt), [str(center)])
            center.chmod(0o644)
            self.assertEqual(apps.media_command(opt, lambda name: '/legacy-wrapper'), ['/legacy-wrapper'])

    def test_author_uses_separate_editor_session_and_never_folder_fallback(self):
        self.assertEqual(apps.author_command(which=lambda name: '/usr/bin/kate' if name == 'kate' else None),
                         ['/usr/bin/kate', '--start', 'Spider-Author'])
        with self.assertRaises(apps.AppUnavailable):
            apps.author_command(which=lambda name: None)

    def test_docx_opens_writer_and_text_requires_text_editor(self):
        with tempfile.TemporaryDirectory() as directory:
            docx = Path(directory) / 'book.docx'; docx.write_bytes(b'placeholder')
            self.assertEqual(apps.author_command(docx, lambda name: '/usr/bin/libreoffice'),
                             ['/usr/bin/libreoffice', '--writer', str(docx)])
            text = Path(directory) / 'chapter.txt'; text.write_text('chapter')
            with self.assertRaises(apps.AppUnavailable):
                apps.author_command(text, lambda name: None)
            pdf = Path(directory) / 'book.pdf'; pdf.write_bytes(b'%PDF')
            with self.assertRaises(apps.AppUnavailable):
                apps.author_command(pdf, lambda name: '/usr/bin/kate')
            with self.assertRaises(apps.AppUnavailable):
                apps.author_command(Path(directory), lambda name: '/usr/bin/kate')

    def test_author_launch_creates_separate_home_and_preserves_old_project(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'Author'
            old = Path(directory) / 'Studio/Author/book.txt'
            old.parent.mkdir(parents=True); old.write_text('untouched')
            with patch.object(apps, 'AUTHOR_HOME', home), \
                 patch.object(apps, 'author_command', return_value=['kate', '--start', 'Spider-Author']), \
                 patch.object(apps.subprocess, 'Popen') as process, \
                 patch.object(apps, 'select_workspace') as workspace:
                apps.launch_author()
                self.assertEqual(process.call_args.kwargs['cwd'], home)
                workspace.assert_called_once_with('author')
                self.assertTrue((home / 'Manuscripts').is_dir())
                self.assertEqual(old.read_text(), 'untouched')

    def test_studio_always_launches_python_ui_not_a_file_manager(self):
        self.assertEqual(apps.studio_command(ROOT), ['python3', str(ROOT / 'studio/main.py')])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(apps.AppUnavailable):
                apps.studio_command(Path(directory))

    def test_failed_author_dependency_does_not_create_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'Author'
            with patch.object(apps, 'AUTHOR_HOME', home), \
                 patch.object(apps, 'author_command', side_effect=apps.AppUnavailable('missing')):
                with self.assertRaises(apps.AppUnavailable):
                    apps.launch_author()
                self.assertFalse(home.exists())


if __name__ == '__main__':
    unittest.main()
