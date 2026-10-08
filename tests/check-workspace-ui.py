"""Companion native UI smoke check, with optional applications left absent."""
import importlib.util
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication

root = Path(__file__).resolve().parents[1]
app = QApplication([])


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shell = load('companion_shell', root / 'the-web/shell/main.py')
window = shell.TheWeb()
with patch.object(shell, 'media_command', side_effect=shell.AppUnavailable('missing media')):
    window.launch_media()
    assert window.status.text() == 'missing media'
with patch.object(shell.subprocess, 'Popen') as process:
    window.launch_studio()
    assert process.call_args.args[0] == ['python3', str(root / 'studio/main.py')]
with patch.object(shell, 'launch_author_native') as launch:
    window.launch_author()
    launch.assert_called_once_with()
studio = load('companion_studio', root / 'studio/main.py')
with tempfile.TemporaryDirectory() as folder:
    with patch.object(studio, 'STUDIO_HOME', Path(folder)):
        panel = studio.SpiderStudio()
        assert not (Path(folder) / 'Author').exists()
        with patch.object(studio.shutil, 'which', return_value=None):
            panel.launch_music()
            assert 'No supported DAW' in panel.status.text()
        panel.close()
author = load('companion_author', root / 'author/main.py')
with tempfile.TemporaryDirectory() as folder:
    panel = author.AuthorWindow(folder)
    book = panel.store.create_book('Test book')
    chapter = panel.store.create_chapter(book, 'One', 'Original')
    panel.load_books(); panel.books.setCurrentRow(0); panel.chapters.setCurrentRow(0)
    assert panel.editor.toPlainText() == 'Original'
    panel.editor.setPlainText('Saved chapter'); panel.autosave()
    assert panel.store.chapter(chapter)['content'] == 'Saved chapter'
    panel.close()
window.close()
app.processEvents()
print('Companion Studio/Author/Media launcher GUI smoke test passed.')
