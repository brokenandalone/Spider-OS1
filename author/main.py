#!/usr/bin/env python3
"""Native Author library, chapter editor, autosave, snapshots and canon notebook."""
import sys
from pathlib import Path
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QInputDialog,
    QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QSplitter, QTabWidget, QTextEdit, QVBoxLayout, QWidget)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from store import AuthorStore


class AuthorWindow(QMainWindow):
    def __init__(self, root=None):
        super().__init__()
        self.store = AuthorStore(root)
        self.book_id = self.chapter_id = None
        self.setWindowTitle('Author | Spider OS')
        self.resize(1200, 800)
        self.setStyleSheet('QWidget { background:#100b18; color:#eee6ff; } '
            'QTextEdit,QListWidget { background:#1b1228; } '
            'QPushButton { background:#4c1d95; padding:8px; border-radius:5px; }')
        root_widget = QWidget(); self.setCentralWidget(root_widget)
        layout = QVBoxLayout(root_widget)
        bar = QHBoxLayout(); layout.addLayout(bar)
        for label, action in [('New book', self.new_book), ('New chapter', self.new_chapter),
                ('Import text', self.import_text), ('Import library', self.import_bundle), ('Save', self.flush),
                ('Restore snapshot', self.restore), ('Backup library', self.backup)]:
            button = QPushButton(label); button.clicked.connect(action); bar.addWidget(button)
        split = QSplitter(); layout.addWidget(split)
        self.books = QListWidget(); split.addWidget(self.books)
        self.chapters = QListWidget(); split.addWidget(self.chapters)
        tabs = QTabWidget(); split.addWidget(tabs)
        self.editor = QTextEdit(); self.editor.setAcceptRichText(False)
        self.canon = QTextEdit(); self.canon.setAcceptRichText(False)
        tabs.addTab(self.editor, 'Chapter'); tabs.addTab(self.canon, 'Canon notes')
        self.editor.setEnabled(False); self.canon.setEnabled(False)
        self.status = QLabel('Choose a book or create one.'); layout.addWidget(self.status)
        self.books.currentItemChanged.connect(self.select_book)
        self.chapters.currentItemChanged.connect(self.select_chapter)
        self.timer = QTimer(self); self.timer.timeout.connect(self.autosave); self.timer.start(2000)
        self.load_books()

    def action(self, function):
        try:
            return function()
        except Exception as error:
            # Keep the editor contents intact when a disk/database operation fails.
            self.status.setText('Save/action failed: ' + str(error))
            QMessageBox.warning(self, 'Author', str(error))
            return False

    def load_books(self):
        self.books.clear()
        for book in self.store.books():
            item = QListWidgetItem(book['title']); item.setData(256, book['id']); self.books.addItem(item)

    def flush(self):
        def save():
            if self.chapter_id is not None:
                self.store.save(self.chapter_id, self.editor.toPlainText())
            if self.book_id is not None:
                self.store.save_canon(self.book_id, self.canon.toPlainText())
            self.status.setText('Saved locally. ' + str(len(self.editor.toPlainText().split())) + ' words.')
            return True
        return self.action(save)

    def autosave(self):
        if self.book_id is not None:
            self.flush()

    def select_book(self, item, previous=None):
        if not self.flush():
            self.books.blockSignals(True); self.books.setCurrentItem(previous); self.books.blockSignals(False)
            return
        self.chapter_id = None; self.editor.clear(); self.editor.setEnabled(False)
        self.book_id = item.data(256) if item else None
        self.canon.setEnabled(item is not None)
        self.canon.setPlainText(self.store.canon(self.book_id) if item else '')
        self.load_chapters()

    def load_chapters(self):
        self.chapters.blockSignals(True); self.chapters.clear()
        if self.book_id is not None:
            for chapter in self.store.chapters(self.book_id):
                item = QListWidgetItem(chapter['title']); item.setData(256, chapter['id']); self.chapters.addItem(item)
        self.chapters.blockSignals(False)

    def select_chapter(self, item, previous=None):
        if not self.flush():
            self.chapters.blockSignals(True); self.chapters.setCurrentItem(previous); self.chapters.blockSignals(False)
            return
        self.chapter_id = item.data(256) if item else None
        self.editor.setEnabled(item is not None)
        self.editor.setPlainText(self.store.chapter(self.chapter_id)['content'] if item else '')

    def new_book(self):
        title, ok = QInputDialog.getText(self, 'New book', 'Title:')
        if ok and title.strip() and self.flush():
            if self.action(lambda: self.store.create_book(title)) is not False:
                self.load_books(); self.books.setCurrentRow(self.books.count() - 1)

    def new_chapter(self):
        if self.book_id is None:
            return
        title, ok = QInputDialog.getText(self, 'New chapter', 'Title:')
        if ok and title.strip() and self.flush():
            if self.action(lambda: self.store.create_chapter(self.book_id, title)) is not False:
                self.load_chapters(); self.chapters.setCurrentRow(self.chapters.count() - 1)

    def import_text(self):
        if self.book_id is None or not self.flush():
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Import as a new chapter', '', 'Text (*.txt *.md *.markdown)')
        if path and self.action(lambda: self.store.import_text(self.book_id, path)) is not False:
            self.load_chapters(); self.chapters.setCurrentRow(self.chapters.count() - 1)

    def import_bundle(self):
        if not self.flush():
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Import Author library', '', 'Author library (*.json)')
        if path:
            added = self.action(lambda: self.store.import_bundle(path))
            if added is not False:
                self.load_books()
                self.status.setText(f'Imported {added} books. Existing writing preserved.')

    def restore(self):
        if self.chapter_id is None or not self.flush():
            return
        versions = self.store.snapshots(self.chapter_id)
        labels = [str(row['id']) + ' • ' + row['created'] for row in versions]
        if not labels:
            self.status.setText('No previous versions yet.'); return
        label, ok = QInputDialog.getItem(self, 'Restore snapshot', 'Previous version:', labels, 0, False)
        if ok and QMessageBox.question(self, 'Restore', 'Restore this version? The current text is kept in history.') == QMessageBox.Yes:
            content = self.action(lambda: self.store.restore(self.chapter_id, versions[labels.index(label)]['id']))
            if content is not False:
                self.editor.setPlainText(content)

    def backup(self):
        if not self.flush():
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Backup library', 'author-backup.sqlite3', 'SQLite (*.sqlite3)')
        if path:
            if self.action(lambda: self.store.backup(path)) is not False:
                self.status.setText('Library backup saved.')

    def closeEvent(self, event):
        if self.flush():
            self.timer.stop(); self.store.close(); event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv); app.setApplicationName('Spider Author')
    window = AuthorWindow(); window.show(); sys.exit(app.exec_())


if __name__ == '__main__':
    main()
