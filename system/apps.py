#!/usr/bin/env python3
"""Native workspace launch contracts; never substitute a folder for an app."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
AUTHOR_HOME = Path.home() / 'Documents' / 'Spider OS' / 'Author'


class AppUnavailable(RuntimeError):
    pass


def executable(path):
    path = Path(path)
    return path.is_file() and os.access(path, os.X_OK)


def media_command(opt=Path('/opt'), which=shutil.which):
    center = opt / 'spider-media-center/spider-media-center'
    legacy = opt / 'spider-media-player/spider-media-player'
    if executable(center):
        return [str(center)]
    # Prefer the compatibility launcher so personal AI DJ/profile environment survives.
    if executable(legacy):
        wrapper = which('spider-media-player')
        return [wrapper] if wrapper else [str(ROOT / 'media/bin/spider-media-player')]
    raise AppUnavailable('Spider Media Center is not installed. Install a verified media package first.')


def author_command(document=None, which=shutil.which):
    if document is None:
        script = ROOT / 'author/main.py'
        if not script.is_file():
            raise AppUnavailable('The native Author module is missing.')
        try:
            __import__('PyQt5.QtWidgets')
        except ImportError:
            raise AppUnavailable('Author requires python3-pyqt5.') from None
        return ['python3', str(script)]
    if document is not None:
        document = Path(document).expanduser().resolve(strict=True)
        if not document.is_file():
            raise AppUnavailable('Select a manuscript file, not a directory.')
    if document and document.suffix.lower() in {'.docx', '.doc', '.odt', '.rtf'}:
        writer = which('libreoffice')
        if not writer:
            raise AppUnavailable('LibreOffice Writer is required to edit this manuscript format.')
        return [writer, '--writer', str(document)]
    if document and document.suffix.lower() not in {'.txt', '.md', '.markdown', '.rst', '.tex'}:
        raise AppUnavailable('Supported manuscripts: DOCX, DOC, ODT, RTF, TXT, Markdown, RST or TeX.')
    kate = which('kate')
    if kate:
        return [kate, '--start', 'Spider-Author', *([str(document)] if document else [])]
    if document:
        raise AppUnavailable('Kate is required for text manuscripts. Install Kate and retry.')
    writer = which('libreoffice')
    if writer:
        return [writer, '--writer']
    raise AppUnavailable('Author needs Kate or LibreOffice Writer. No editor is installed.')


def studio_command(root=ROOT):
    script = root / 'studio/main.py'
    if not script.is_file():
        raise AppUnavailable('Spider Studio native application is missing. Reinstall the Studio module.')
    return ['python3', str(script)]


def select_workspace(name):
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / 'spider-os'
    try:
        runtime.mkdir(parents=True, exist_ok=True)
        (runtime / 'workspace').write_text(name)
    except OSError:
        pass


def launch_author(document=None):
    command = author_command(document)
    AUTHOR_HOME.mkdir(parents=True, exist_ok=True)
    for directory in ('Manuscripts', 'Lore', 'Snapshots'):
        (AUTHOR_HOME / directory).mkdir(exist_ok=True)
    subprocess.Popen(command, cwd=AUTHOR_HOME, start_new_session=True)
    select_workspace('author')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', choices=('studio', 'author', 'media'))
    parser.add_argument('files', nargs='*')
    args = parser.parse_args()
    try:
        if args.app == 'author':
            if len(args.files) > 1:
                raise AppUnavailable('Open one manuscript at a time.')
            launch_author(args.files[0] if args.files else None)
            return
        command = studio_command() if args.app == 'studio' else media_command()
        if args.app == 'studio':
            try:
                __import__('PyQt5.QtWidgets')
            except ImportError:
                raise AppUnavailable('Spider Studio requires python3-pyqt5.') from None
        subprocess.Popen([*command, *args.files], start_new_session=True)
        select_workspace('studio' if args.app == 'studio' else 'media')
    except (AppUnavailable, OSError) as error:
        message = str(error)
        print(message, file=sys.stderr)
        dialog = shutil.which('kdialog')
        if dialog:
            try:
                subprocess.run([dialog, '--error', message], timeout=30, check=False)
            except (OSError, subprocess.TimeoutExpired):
                pass
        raise SystemExit(1)


if __name__ == '__main__':
    main()
