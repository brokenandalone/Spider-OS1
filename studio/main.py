#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

AUTHOR_STUDIO_URL = 'https://webbie-author-studio-guwtrp.v2.appdeploy.ai/'
STUDIO_HOME = Path.home() / 'Documents' / 'Spider Studio'


class StudioButton(QPushButton):
    def __init__(self, text, action):
        super().__init__(text)
        self.setMinimumHeight(52)
        self.clicked.connect(action)


class SpiderStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Spider Studio | Spider OS')
        self.resize(1180, 760)

        self.setStyleSheet("""
            QMainWindow { background: #0c0a10; color: #eeeaf3; }
            QFrame#sidebar { background: #15111b; border-right: 1px solid #6d28d9; }
            QLabel { color: #eeeaf3; }
            QPushButton {
                background: #21172d;
                color: #f5f0fa;
                border: 1px solid #4c1d95;
                border-radius: 10px;
                padding: 12px;
                text-align: left;
                font-size: 15px;
            }
            QPushButton:hover { background: #342047; border-color: #8b5cf6; }
            QPushButton:pressed { background: #4c1d95; }
        """)

        STUDIO_HOME.mkdir(parents=True, exist_ok=True)
        for name in ('Author', 'Music', 'Media', 'Artwork'):
            (STUDIO_HOME / name).mkdir(parents=True, exist_ok=True)

        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(270)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 24, 20, 24)
        side.setSpacing(10)

        logo = QLabel('SPIDER STUDIO')
        logo.setFont(QFont('Sans Serif', 22, QFont.Bold))
        logo.setStyleSheet('color: #a78bfa;')
        side.addWidget(logo)

        subtitle = QLabel('CREATE. BUILD. PLAY.')
        subtitle.setStyleSheet('color: #8f859a;')
        side.addWidget(subtitle)
        side.addSpacing(24)

        side.addWidget(StudioButton('Author Studio', self.launch_author))
        side.addWidget(StudioButton('Music Studio', self.launch_music))
        side.addWidget(StudioButton('Spider Media Player', self.launch_media))
        side.addWidget(StudioButton('Artwork', self.open_artwork))
        side.addWidget(StudioButton('Studio Files', self.open_studio_home))
        side.addStretch()

        self.status = QLabel('Checking Spider Studio…')
        self.status.setWordWrap(True)
        self.status.setStyleSheet('color: #a3a3a3;')
        side.addWidget(self.status)

        outer.addWidget(sidebar)

        center = QWidget()
        content = QVBoxLayout(center)
        content.setContentsMargins(50, 48, 50, 48)

        title = QLabel('Spider Studio')
        title.setFont(QFont('Sans Serif', 32, QFont.Bold))
        content.addWidget(title)

        description = QLabel(
            'The creative workspace for Spider OS.\n'
            'Authoring • Music • Media • Artwork • Webbie'
        )
        description.setFont(QFont('Sans Serif', 16))
        description.setStyleSheet('color: #b6a9c7;')
        content.addWidget(description)
        content.addSpacing(30)

        self.media_status = QLabel()
        self.webbie_status = QLabel()
        self.ollama_status = QLabel()
        for label in (self.media_status, self.webbie_status, self.ollama_status):
            label.setFont(QFont('Sans Serif', 14))
            content.addWidget(label)

        content.addSpacing(20)
        note = QLabel(
            'Spider Media Player is the Media module.\n'
            'Webbie remains the resident AI service shared across Spider OS.'
        )
        note.setStyleSheet('color: #82788d;')
        content.addWidget(note)
        content.addStretch()

        footer = QLabel('SPIDER OS  •  YOUR LIFE. ONE WEB.')
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet('color: #625a69;')
        content.addWidget(footer)

        outer.addWidget(center, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)
        self.update_status()

    def launch(self, command):
        try:
            subprocess.Popen(command)
            self.status.setText('Launched: ' + ' '.join(command))
        except Exception as exc:
            self.status.setText(str(exc))

    def launch_author(self):
        self.launch(['xdg-open', AUTHOR_STUDIO_URL])

    def launch_music(self):
        for command in ('ardour8', 'ardour', 'carla'):
            path = shutil.which(command)
            if path:
                self.launch([path])
                return
        self.launch(['xdg-open', str(STUDIO_HOME / 'Music')])

    def media_command(self):
        command = shutil.which('spider-media-player')
        if command:
            return command
        bundled = '/opt/spider-media-player/spider-media-player'
        return bundled if os.path.isfile(bundled) and os.access(bundled, os.X_OK) else None

    def launch_media(self):
        command = self.media_command()
        if command:
            self.launch([command])
        else:
            self.status.setText(
                'Spider Media Player is not installed. Run the Spider Media Player installer.'
            )

    def open_artwork(self):
        self.launch(['xdg-open', str(STUDIO_HOME / 'Artwork')])

    def open_studio_home(self):
        self.launch(['xdg-open', str(STUDIO_HOME)])

    def user_service_active(self, service):
        result = subprocess.run(
            ['systemctl', '--user', 'is-active', service],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return result.stdout.strip() == 'active'

    def update_status(self):
        media = self.media_command()
        webbie = self.user_service_active('webbie.service')

        self.media_status.setText(
            '● Spider Media Player: INSTALLED'
            if media
            else '○ Spider Media Player: NOT INSTALLED'
        )
        self.webbie_status.setText(
            '● Webbie: ACTIVE' if webbie else '○ Webbie: OFFLINE'
        )

        ollama = shutil.which('ollama')
        if ollama:
            result = subprocess.run(
                [ollama, 'list'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            model = 'qwen3:8b' if 'qwen3:8b' in result.stdout.lower() else 'available'
            self.ollama_status.setText(f'● Ollama: {model}')
        else:
            self.ollama_status.setText('○ Ollama: NOT FOUND')


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Spider Studio')
    app.setOrganizationName('Spider OS')
    window = SpiderStudio()
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
