#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QBrush,
    QFont,
    QPalette,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


SPIDER_ROOT = Path(
    "/usr/local/lib/spider-os"
)

if not SPIDER_ROOT.exists():
    SPIDER_ROOT = (
        Path(__file__)
        .resolve()
        .parents[2]
    )


MANAGER = (
    SPIDER_ROOT
    / "kali-bay"
    / "bin"
    / "kali-bay"
)


WALLPAPER = (
    SPIDER_ROOT
    / "branding"
    / "workspaces"
    / "kali-bay.png"
)


CATEGORIES = [
    (
        "INFORMATION GATHERING",
        "OSINT, discovery, enumeration",
        "kali-tools-information-gathering",
    ),
    (
        "VULNERABILITY ANALYSIS",
        "Assessment and vulnerability tools",
        "kali-tools-vulnerability",
    ),
    (
        "WEB APPLICATIONS",
        "Web assessment toolset",
        "kali-tools-web",
    ),
    (
        "PASSWORDS",
        "Password auditing and recovery",
        "kali-tools-passwords",
    ),
    (
        "WIRELESS",
        "802.11, Bluetooth, RFID and SDR",
        "kali-tools-wireless",
    ),
    (
        "EXPLOITATION",
        "Exploitation framework tools",
        "kali-tools-exploitation",
    ),
    (
        "SNIFFING & SPOOFING",
        "Traffic inspection and protocol tools",
        "kali-tools-sniffing-spoofing",
    ),
    (
        "POST EXPLOITATION",
        "Post-exploitation tool group",
        "kali-tools-post-exploitation",
    ),
    (
        "FORENSICS",
        "Digital forensics and recovery",
        "kali-tools-forensics",
    ),
    (
        "REVERSE ENGINEERING",
        "Binary analysis and reversing",
        "kali-tools-reverse-engineering",
    ),
    (
        "REPORTING",
        "Assessment reporting tools",
        "kali-tools-reporting",
    ),
    (
        "SOCIAL ENGINEERING",
        "Social-engineering assessment tools",
        "kali-tools-social-engineering",
    ),
]


class KaliBayWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._wallpaper = None

        self.setWindowTitle(
            "Kali Bay | Spider OS"
        )

        self.resize(
            1180,
            820,
        )

        self.setMinimumSize(
            900,
            650,
        )

        self.build_ui()
        self.load_wallpaper()
        self.refresh_status()

    def build_ui(self):
        self.setStyleSheet(
            """
            QWidget#root {
                background: rgba(
                    7,
                    5,
                    10,
                    225
                );
            }

            QLabel {
                color: #f3eef6;
            }

            QPushButton {
                background: rgba(
                    72,
                    27,
                    112,
                    220
                );

                border:
                    1px solid
                    #9333ea;

                border-radius:
                    9px;

                padding:
                    12px;

                color:
                    #ffffff;

                font-weight:
                    bold;
            }

            QPushButton:hover {
                background:
                    rgba(
                        107,
                        33,
                        168,
                        235
                    );

                border:
                    1px solid
                    #c084fc;
            }

            QScrollArea {
                background:
                    transparent;

                border:
                    none;
            }
            """
        )

        root = QWidget()

        root.setObjectName(
            "root"
        )

        self.setCentralWidget(
            root
        )

        outer = QVBoxLayout(
            root
        )

        outer.setContentsMargins(
            28,
            24,
            28,
            24,
        )

        header = QLabel(
            "KALI BAY"
        )

        header.setFont(
            QFont(
                "Sans Serif",
                34,
                QFont.Bold,
            )
        )

        header.setStyleSheet(
            "color:#c084fc;"
        )

        outer.addWidget(
            header
        )

        subtitle = QLabel(
            "SPIDER OS SECURITY WORKSPACE\n"
            "Full Kali toolset · isolated from the Spider OS host"
        )

        subtitle.setStyleSheet(
            """
            color:#c7b9d2;
            font-size:14px;
            """
        )

        outer.addWidget(
            subtitle
        )

        self.status = QLabel()

        self.status.setStyleSheet(
            """
            color:#ddd0e7;
            padding:10px 0;
            font-weight:bold;
            """
        )

        outer.addWidget(
            self.status
        )

        controls = QHBoxLayout()

        setup = QPushButton(
            "INITIALIZE / REPAIR FULL KALI"
        )

        setup.clicked.connect(
            self.setup_kali
        )

        controls.addWidget(
            setup
        )

        terminal = QPushButton(
            "KALI TERMINAL"
        )

        terminal.clicked.connect(
            self.open_terminal
        )

        controls.addWidget(
            terminal
        )

        update = QPushButton(
            "UPDATE KALI"
        )

        update.clicked.connect(
            self.update_kali
        )

        controls.addWidget(
            update
        )

        refresh = QPushButton(
            "REFRESH STATUS"
        )

        refresh.clicked.connect(
            self.refresh_status
        )

        controls.addWidget(
            refresh
        )

        outer.addLayout(
            controls
        )

        heading = QLabel(
            "TOOL CATEGORIES"
        )

        heading.setStyleSheet(
            """
            color:#a78bfa;
            font-size:18px;
            font-weight:bold;
            padding-top:12px;
            """
        )

        outer.addWidget(
            heading
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QScrollArea.NoFrame
        )

        container = QWidget()

        container.setStyleSheet(
            "background:transparent;"
        )

        grid = QGridLayout(
            container
        )

        grid.setSpacing(
            14
        )

        for index, (
            title,
            description,
            package,
        ) in enumerate(
            CATEGORIES
        ):
            button = QPushButton(
                f"{title}\n"
                f"{description}"
            )

            button.setMinimumHeight(
                88
            )

            button.clicked.connect(
                lambda checked=False,
                p=package,
                t=title:
                self.open_category(
                    p,
                    t,
                )
            )

            row = index // 3
            column = index % 3

            grid.addWidget(
                button,
                row,
                column,
            )

        scroll.setWidget(
            container
        )

        outer.addWidget(
            scroll,
            1,
        )

        warning = QLabel(
            "Kali Bay is intended for systems, networks, "
            "applications, and labs you are authorized to assess."
        )

        warning.setAlignment(
            Qt.AlignCenter
        )

        warning.setStyleSheet(
            """
            color:#93869c;
            padding-top:8px;
            """
        )

        outer.addWidget(
            warning
        )

        footer = QLabel(
            "YOUR LIFE. ONE WEB."
        )

        footer.setAlignment(
            Qt.AlignCenter
        )

        footer.setStyleSheet(
            """
            color:#6f6377;
            font-weight:bold;
            """
        )

        outer.addWidget(
            footer
        )

    def load_wallpaper(self):
        if not WALLPAPER.exists():
            return

        self._wallpaper = QPixmap(
            str(WALLPAPER)
        )

        self.apply_wallpaper()

    def apply_wallpaper(self):
        if (
            self._wallpaper is None
            or self._wallpaper.isNull()
        ):
            return

        scaled = self._wallpaper.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )

        palette = QPalette(
            self.palette()
        )

        palette.setBrush(
            QPalette.Window,
            QBrush(scaled),
        )

        self.setPalette(
            palette
        )

        self.setAutoFillBackground(
            True
        )

    def resizeEvent(
        self,
        event,
    ):
        self.apply_wallpaper()

        super().resizeEvent(
            event
        )

    def manager_status(self):
        try:
            result = subprocess.run(
                [
                    str(MANAGER),
                    "status",
                ],
                text=True,
                capture_output=True,
                timeout=25,
                check=False,
            )

            return (
                result.stdout.strip()
                or "missing"
            )

        except Exception:
            return "error"

    def refresh_status(self):
        status = self.manager_status()

        if status == "ready":
            text = (
                "● FULL KALI BAY READY  "
                "· kali-linux-everything installed"
            )

            style = (
                "color:#c4b5fd;"
                "padding:10px 0;"
                "font-weight:bold;"
            )

        elif status == "container":
            text = (
                "● KALI CONTAINER CREATED  "
                "· full toolset still needs provisioning"
            )

            style = (
                "color:#facc15;"
                "padding:10px 0;"
                "font-weight:bold;"
            )

        elif status == "error":
            text = (
                "● KALI BAY STATUS ERROR"
            )

            style = (
                "color:#fb7185;"
                "padding:10px 0;"
                "font-weight:bold;"
            )

        else:
            text = (
                "● KALI BAY NOT INITIALIZED"
            )

            style = (
                "color:#a89caf;"
                "padding:10px 0;"
                "font-weight:bold;"
            )

        self.status.setText(
            text
        )

        self.status.setStyleSheet(
            style
        )

    def launch_terminal_command(
        self,
        args,
    ):
        if not shutil_which(
            "konsole"
        ):
            QMessageBox.warning(
                self,
                "Kali Bay",
                "Konsole is not installed.",
            )

            return

        subprocess.Popen(
            [
                "konsole",
                "--hold",
                "-e",
            ]
            + [
                str(item)
                for item in args
            ],
            start_new_session=True,
        )

    def setup_kali(self):
        self.launch_terminal_command(
            [
                MANAGER,
                "setup",
            ]
        )

    def update_kali(self):
        self.launch_terminal_command(
            [
                MANAGER,
                "update",
            ]
        )

    def open_terminal(self):
        subprocess.Popen(
            [
                str(MANAGER),
                "terminal",
            ],
            start_new_session=True,
        )

    def open_category(
        self,
        package,
        title,
    ):
        if (
            self.manager_status()
            != "ready"
        ):
            QMessageBox.information(
                self,
                "Kali Bay",
                "Initialize the full Kali "
                "toolset first.",
            )

            return

        subprocess.Popen(
            [
                str(MANAGER),
                "category",
                package,
                title,
            ],
            start_new_session=True,
        )


def shutil_which(command):
    from shutil import which

    return which(command)


def main():
    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Kali Bay"
    )

    window = KaliBayWindow()

    window.show()

    sys.exit(
        app.exec_()
    )


if __name__ == "__main__":
    main()
