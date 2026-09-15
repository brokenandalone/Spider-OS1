#!/usr/bin/env python3

import os
import subprocess
import sys

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


SPIDER_ROOT = "/usr/local/lib/spider-os"


class SpiderButton(QPushButton):
    def __init__(self, text, action=None):
        super().__init__(text)
        self.setMinimumHeight(48)

        if action:
            self.clicked.connect(action)


class TheWeb(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("The Web | Spider OS")
        self.resize(1200, 760)

        self.setStyleSheet("""
            QMainWindow {
                background: #0c0a10;
                color: #eeeaf3;
            }

            QFrame#sidebar {
                background: #16121d;
                border-right: 1px solid #6d28d9;
            }

            QLabel {
                color: #eeeaf3;
            }

            QPushButton {
                background: #21172d;
                color: #f5f0fa;
                border: 1px solid #5b21b6;
                border-radius: 8px;
                padding: 10px;
                text-align: left;
                font-size: 15px;
            }

            QPushButton:hover {
                background: #36204d;
                border: 1px solid #8b5cf6;
            }

            QPushButton:pressed {
                background: #4c1d95;
            }
        """)

        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)

        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 24, 20, 24)
        side.setSpacing(12)

        logo = QLabel("SPIDER OS")
        logo.setFont(QFont("Sans Serif", 24, QFont.Bold))
        logo.setStyleSheet("color: #a78bfa;")
        side.addWidget(logo)

        tagline = QLabel("YOUR LIFE. ONE WEB.")
        tagline.setStyleSheet("color: #9ca3af;")
        side.addWidget(tagline)

        side.addSpacing(25)

        side.addWidget(SpiderButton("Webbie", self.show_webbie))
        side.addWidget(SpiderButton("Forage", self.launch_forage))
        side.addWidget(SpiderButton("Deep Forage", self.launch_deep_forage))
        side.addWidget(SpiderButton("Kali Bay", self.launch_kali_bay))
        side.addWidget(SpiderButton("Terminal", self.launch_terminal))
        side.addWidget(SpiderButton("System Settings", self.launch_settings))

        side.addStretch()

        self.status = QLabel("Spider OS initializing...")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: #a3a3a3;")
        side.addWidget(self.status)

        layout.addWidget(sidebar)

        workspace = QWidget()
        center = QVBoxLayout(workspace)
        center.setContentsMargins(48, 48, 48, 48)

        welcome = QLabel("Welcome to The Web")
        welcome.setFont(QFont("Sans Serif", 30, QFont.Bold))
        center.addWidget(welcome)

        subtitle = QLabel(
            "Spider OS native command center\n"
            "Webbie • Forage • Kali Bay"
        )
        subtitle.setFont(QFont("Sans Serif", 16))
        subtitle.setStyleSheet("color: #b6a9c7;")
        center.addWidget(subtitle)

        center.addSpacing(30)

        self.webbie_status = QLabel()
        self.webbie_status.setFont(QFont("Sans Serif", 15))
        center.addWidget(self.webbie_status)

        self.core_status = QLabel()
        self.core_status.setFont(QFont("Sans Serif", 15))
        center.addWidget(self.core_status)

        center.addStretch()

        footer = QLabel("SPIDER OS  •  YOUR LIFE. ONE WEB.")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #6b6572;")
        center.addWidget(footer)

        layout.addWidget(workspace, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)

        self.update_status()

    def service_active(self, service, user=False):
        command = ["systemctl"]

        if user:
            command.append("--user")

        command += ["is-active", service]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        return result.stdout.strip() == "active"

    def update_status(self):
        webbie = self.service_active("webbie.service", user=True)
        core = self.service_active("spider-os.service")

        self.webbie_status.setText(
            "● Webbie: ACTIVE" if webbie else "○ Webbie: OFFLINE"
        )

        self.core_status.setText(
            "● Spider Core: ACTIVE" if core else "○ Spider Core: OFFLINE"
        )

        if webbie and core:
            self.status.setText("The Web is connected.")
        else:
            self.status.setText("Spider OS services need attention.")

    def launch(self, command):
        try:
            subprocess.Popen(command)
        except Exception as error:
            self.status.setText(str(error))

    def show_webbie(self):
        self.status.setText(
            "Webbie is resident and connected to The Web."
        )

    def launch_forage(self):
        path = os.path.join(SPIDER_ROOT, "forage", "forage.py")

        if os.path.exists(path):
            self.launch(["python3", path])
        else:
            self.status.setText("Forage executable not found.")

    def launch_deep_forage(self):
        path = os.path.join(
            SPIDER_ROOT,
            "forage",
            "deep-forage",
        )

        if os.path.exists(path):
            self.launch(["xdg-open", path])
        else:
            self.status.setText("Deep Forage is not installed yet.")

    def launch_kali_bay(self):
        path = os.path.join(SPIDER_ROOT, "kali-bay")

        if os.path.exists(path):
            self.launch(["xdg-open", path])
        else:
            self.status.setText("Kali Bay is not installed.")

    def launch_terminal(self):
        self.launch(["konsole"])

    def launch_settings(self):
        self.launch(["systemsettings"])


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("The Web")
    app.setOrganizationName("Spider OS")

    window = TheWeb()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
