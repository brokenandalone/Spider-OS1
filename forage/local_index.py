#!/usr/bin/env python3
"""Selected-source, replaceable local text index. Original files are never modified."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import tempfile
import time

CONFIG = Path.home() / '.config/spider-os/forage-index.json'
DEFAULT_DB = Path.home() / '.local/share/spider-os/forage/local-index.sqlite'
EXTENSIONS = {'.txt', '.md', '.markdown', '.rst', '.py', '.js', '.ts', '.tsx', '.jsx',
              '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.csv', '.html', '.htm', '.css', '.sh'}
DENIED = {'node_modules', '__pycache__', 'venv', 'rclone', 'rclone.conf', 'credentials',
          'credentials.json', 'secrets.json', 'token.json', 'tokens.json', 'id_rsa', 'id_ed25519'}
LIMIT = 2 * 1024 * 1024


def configured_roots():
    if not CONFIG.exists():
        return []
    config = json.loads(CONFIG.read_text())
    roots = config.get('roots', [])
    if not isinstance(roots, list) or not all(isinstance(root, str) for root in roots):
        raise ValueError('Index roots must be a list of selected directory paths')
    return roots


def excluded(relative):
    return any(part.startswith('.') or part.lower() in DENIED
               or part.lower().endswith(('.pem', '.key')) for part in relative.parts)


def validate_roots(roots, database):
    selected = []
    for raw in roots:
        candidate = Path(raw).expanduser()
        if candidate.is_symlink():
            raise ValueError('Selected roots must not be symlinks')
        root = candidate.resolve(strict=True)
        if not root.is_dir() or root in {Path('/'), Path.home().resolve()}:
            raise ValueError('Select project directories, not the filesystem or whole home')
        if database.resolve().is_relative_to(root):
            raise ValueError('The index must be outside selected sources')
        if root.name.lower() in DENIED or root.name.startswith('.'):
            raise ValueError('Credential or hidden directories cannot be selected as roots')
        if any(root == other or root.is_relative_to(other) or other.is_relative_to(root) for other in selected):
            raise ValueError('Selected roots must be distinct and non-overlapping')
        selected.append(root)
    return selected


def read_document(path, root):
    if not path.resolve().is_relative_to(root):
        raise ValueError('File escaped selected root')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > LIMIT:
            return None
        data = handle.read(LIMIT + 1)
        after = os.fstat(handle.fileno())
    current = path.stat(follow_symlinks=False)
    if (before.st_ino, before.st_dev, before.st_mtime_ns, before.st_size) != (after.st_ino, after.st_dev, after.st_mtime_ns, after.st_size) or (after.st_ino, after.st_dev) != (current.st_ino, current.st_dev):
        raise ValueError('Selected file changed while indexing; retry when idle')
    if len(data) > LIMIT or b'\x00' in data:
        return None
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return None
    if not text.strip():
        return None
    return text, hashlib.sha256(data).hexdigest(), before.st_mtime_ns, before.st_size


class LocalIndex:
    def __init__(self, path=DEFAULT_DB):
        self.path = Path(path).expanduser()
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise ValueError('Local index must not be a symlink')

    def rebuild(self, roots=None, progress=None):
        source = 'configured' if roots is None else 'explicit'
        roots = configured_roots() if roots is None else roots
        if roots is None or not isinstance(roots, (list, tuple)):
            raise ValueError('Selected roots must be a list')
        if source == 'configured' and not roots:
            raise ValueError('Choose roots in ~/.config/spider-os/forage-index.json before indexing')
        selected = validate_roots(roots, self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, temporary = tempfile.mkstemp(prefix='.forage-pending-', dir=self.path.parent)
        os.close(fd)
        temporary = Path(temporary)
        indexed = skipped = 0
        try:
            with closing(sqlite3.connect(temporary)) as db:
                db.executescript('''
                    CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    CREATE TABLE documents (id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL,
                        root TEXT NOT NULL, sha256 TEXT NOT NULL, modified_ns INTEGER NOT NULL,
                        bytes INTEGER NOT NULL, indexed_at REAL NOT NULL);
                    CREATE VIRTUAL TABLE text USING fts5(title, content);
                ''')
                db.execute('INSERT INTO metadata VALUES (?,?)', ('selection', json.dumps({'source': source, 'roots': [str(root) for root in selected]})))
                db.execute('INSERT INTO metadata VALUES (?,?)', ('schema', '1'))
                def walk_error(error):
                    raise error
                for root in selected:
                    for directory, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
                        base = Path(directory)
                        dirs[:] = sorted(name for name in dirs if not (base / name).is_symlink()
                                         and not excluded((base / name).relative_to(root)))
                        for name in sorted(names):
                            path = base / name
                            if excluded(path.relative_to(root)) or path.is_symlink() or path.suffix.lower() not in EXTENSIONS:
                                skipped += 1; continue
                            document = read_document(path, root)
                            if document is None:
                                skipped += 1; continue
                            content, digest, modified, size = document
                            cursor = db.execute('INSERT INTO documents(path,root,sha256,modified_ns,bytes,indexed_at) VALUES (?,?,?,?,?,?)',
                                                (str(path), str(root), digest, modified, size, time.time()))
                            db.execute('INSERT INTO text(rowid,title,content) VALUES (?,?,?)', (cursor.lastrowid, name, content))
                            indexed += 1
                            if progress:
                                progress(str(path))
                db.commit()
                if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('Index integrity check failed')
            temporary.chmod(0o600)
            # Durable, atomic replacement. A failed scan cannot partially replace an old index.
            with temporary.open('rb') as handle:
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            return {'indexed': indexed, 'skipped': skipped, 'roots': len(selected)}
        finally:
            temporary.unlink(missing_ok=True)
            Path(str(temporary) + '-journal').unlink(missing_ok=True)

    def search(self, query, limit=30):
        if not isinstance(query, str) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError('Search requires text and a result limit from 1 to 100')
        words = re.findall(r'[^\W_]+', query, flags=re.UNICODE)
        match = ' '.join('"' + word + '"' for word in words[:32])
        if not match or not self.path.exists():
            return []
        if self.path.is_symlink():
            raise ValueError('Local index must not be a symlink')
        with closing(sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
            selection = json.loads(db.execute("SELECT value FROM metadata WHERE key='selection'").fetchone()[0])
            if selection['source'] == 'configured':
                current = configured_roots()
                allowed = {str(Path(root).expanduser().resolve()) for root in current}
            else:
                allowed = set(selection['roots'])
            if not allowed:
                return []
            rows = db.execute('''SELECT documents.path,text.title,
                snippet(text,1,'','',' … ',22),documents.root,documents.sha256,
                documents.modified_ns,documents.bytes,documents.indexed_at
                FROM text JOIN documents ON documents.id=text.rowid
                WHERE text MATCH ? ORDER BY rank''', (match,))
            results = []
            for row in rows:
                path, title, snippet, root, digest, modified, size, indexed = row
                if root not in allowed or Path(root).is_symlink() or str(Path(root).resolve()) != root:
                    continue
                original = Path(path)
                try:
                    relative = original.relative_to(root)
                    if excluded(relative) or any((Path(root) / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
                        continue
                    info = original.stat()
                    if not original.is_file() or not os.access(original, os.R_OK):
                        continue
                except (OSError, ValueError):
                    continue
                results.append({'path': path, 'title': title, 'snippet': snippet,
                                'url': original.as_uri(), 'root': root, 'sha256': digest,
                                'indexed_at': indexed, 'stale': info.st_mtime_ns != modified or info.st_size != size})
                if len(results) >= limit:
                    break
            return results


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=DEFAULT_DB)
    commands = parser.add_subparsers(dest='command', required=True)
    rebuild = commands.add_parser('rebuild')
    rebuild.add_argument('--root', action='append', help='Explicit selected directory; repeat for several roots')
    search = commands.add_parser('search'); search.add_argument('query')
    search.add_argument('--limit', type=int, default=30)
    args = parser.parse_args()
    try:
        index = LocalIndex(args.database)
        data = index.rebuild(args.root) if args.command == 'rebuild' else index.search(args.query, args.limit)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except (OSError, ValueError, TypeError, sqlite3.Error, KeyError):
        parser.exit(1, 'Forage: indexing/search failed; review selected roots and local permissions. Original files are unchanged.\n')


if __name__ == '__main__':
    main()
