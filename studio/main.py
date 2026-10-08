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
    QFrame, QGridLayout, QScrollArea, QTabWidget,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

SPIDER_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIDER_ROOT / 'system'))
from apps import AppUnavailable, media_command
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools import TOOLS, resolve_tool
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
            QWidget { background: #0c0a10; color: #eeeaf3; }
            QTabBar::tab { background:#21172d; color:#e9d5ff; padding:8px; }
            QTabBar::tab:selected { background:#4c1d95; }
            QTabWidget::pane, QScrollArea { border:1px solid #4c1d95; }
            QPushButton:disabled { background:#17121d; color:#93869e; border-color:#352543; }
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
        for name in ('Music', 'Media', 'Artwork'):
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
        logo.setFont(QFont('Sans Serif', 18, QFont.Bold))
        logo.setStyleSheet('color: #a78bfa;')
        side.addWidget(logo)

        subtitle = QLabel('CREATE. BUILD. PLAY.')
        subtitle.setStyleSheet('color: #8f859a;')
        side.addWidget(subtitle)
        side.addSpacing(24)

        side.addWidget(StudioButton('Music Studio', self.launch_music))
        side.addWidget(StudioButton('Spider Media Center', self.launch_media))
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
        content.setContentsMargins(24, 24, 24, 24)

        title = QLabel('Spider Studio')
        title.setFont(QFont('Sans Serif', 32, QFont.Bold))
        content.addWidget(title)

        description = QLabel(
            'The creative workspace for Spider OS.\n'
            'Music • Media • Artwork • Webbie'
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

        self.tool_tabs = QTabWidget()
        content.addWidget(self.tool_tabs, 1)
        self.tool_buttons = []
        for category, tools in TOOLS.items():
            page = QWidget(); grid = QGridLayout(page)
            for index, tool in enumerate(tools):
                frame = QFrame(); box = QVBoxLayout(frame)
                heading = QLabel(tool[0]); heading.setStyleSheet('font-size:18px; color:#c4b5fd;')
                box.addWidget(heading)
                description = QLabel(tool[1]); description.setWordWrap(True); box.addWidget(description)
                button = QPushButton('Open')
                button.clicked.connect(lambda checked=False, selected=tool: self.launch_tool(selected))
                box.addWidget(button); grid.addWidget(frame, index // 2, index % 2)
                self.tool_buttons.append((tool, button))
            scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(page)
            self.tool_tabs.addTab(scroll, category.replace('&', '&&'))
        refresh = QPushButton('Refresh installed tools'); refresh.clicked.connect(self.refresh_tools)
        content.addWidget(refresh)
        self.refresh_tools()

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
            self.status.setText('Application opened.')
            return True
        except Exception as exc:
            self.status.setText(str(exc))
            return False

    def refresh_tools(self):
        installed = 0
        for tool, button in self.tool_buttons:
            available = resolve_tool(tool) is not None
            button.setEnabled(available)
            button.setText('Open' if available else 'Unavailable on this machine')
            installed += int(available)
        self.status.setText(f'{installed} creative tools available.')

    def launch_tool(self, tool):
        command = resolve_tool(tool)
        if command is None:
            self.refresh_tools()
            self.status.setText(f'{tool[0]} is not available on this machine.')
            return
        if self.launch(command):
            self.status.setText(f'Opened {tool[0]}.')

    def launch_music(self):
        for tool in TOOLS['Recording & mixing']:
            command = resolve_tool(tool)
            if command:
                self.launch(command)
                return
        self.status.setText('No supported DAW or audio editor was detected. Refresh installed tools after checking the Ubuntu Studio menu.')

    def media_command(self):
        try:
            return media_command()
        except AppUnavailable:
            return None

    def launch_media(self):
        command = self.media_command()
        if command:
            self.launch(command)
        else:
            self.status.setText('Spider Media Center is not installed. Install a verified media package first.')

    def open_artwork(self):
        self.launch(['xdg-open', str(STUDIO_HOME / 'Artwork')])

    def open_studio_home(self):
        self.launch(['xdg-open', str(STUDIO_HOME)])

    def user_service_active(self, service):
        try:
            result = subprocess.run(
                ['systemctl', '--user', 'is-active', service],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2,
            )
            return result.stdout.strip() == 'active'
        except (OSError, subprocess.TimeoutExpired):
            return False

    def update_status(self):
        media = self.media_command()
        webbie = self.user_service_active('webbie.service')

        self.media_status.setText(
            '● Spider Media Center: INSTALLED'
            if media
            else '○ Spider Media Center: NOT INSTALLED'
        )
        self.webbie_status.setText(
            '● Webbie: ACTIVE' if webbie else '○ Webbie: OFFLINE'
        )

        self.ollama_status.setText(
            '● Ollama: INSTALLED' if shutil.which('ollama') else '○ Ollama: NOT FOUND'
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Spider Studio')
    app.setOrganizationName('Spider OS')
    window = SpiderStudio()
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
