# Native Author library

The Author home launcher now opens a dedicated local Qt application. Passing an existing office manuscript still opens LibreOffice Writer, and passing text to the command-line launcher preserves the Kate session contract.

The app keeps books, chapter text and canon notes in `~/Documents/Spider OS/Author/library.sqlite3`. It saves every two seconds and before switching books/chapters or closing. Chapter changes preserve the previous text in the same database transaction. Restoring a snapshot also preserves the text being replaced. A failed save leaves the editor open with its text intact. The library backup uses SQLite's consistent backup API.

Use **Import text** for a new TXT/Markdown chapter. Use **Import library** for a JSON package with `format: spider-author-1` and a `books` list. Each book contains `title`, optional `canon`, and `chapters` entries with `title` and `content`. Imports merge transactionally; repeated identical book content is skipped, and existing books are never overwritten. Different versions remain separate books. Office formatting and embedded artwork remain in the original documents rather than the plain-text editor.

Private manuscripts, reference bundles and the live database must never be committed to the public repository. Prepared content packages are delivered privately and imported on the user's machine.

## Verified in the source test environment

- [x] Book library and chapter navigation.
- [x] Autosave and persistence after reopening.
- [x] Previous-version snapshots and non-destructive restore.
- [x] Save failure retains unsaved editor contents.
- [x] Per-book canon notebook.
- [x] Consistent library backups.
- [x] Idempotent, transactional library imports.
- [x] The Web and command-line launcher integration.

## Remaining qualification and features

- [ ] Install and test on the user's Spider OS desktop.
- [ ] Import the private Broken World package on that desktop.
- [ ] Rich DOCX editing and manuscript/publishing exports.
- [ ] Continuity analysis, character graphs, timeline views and chapter read-aloud.

Canon notes are a notebook, not an automatic continuity checker. No boot, OS migration, installed Webbie voice code or media payload is replaced by this batch.
