#!/usr/bin/env python3

import os
import socket
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


SOCKET_PATH = (
    Path(
        os.environ.get(
            "XDG_RUNTIME_DIR",
            f"/run/user/{os.getuid()}",
        )
    )
    / "spider-os"
    / "webbie.sock"
)


class WebbieWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Webbie | Spider OS"
        )

        self.resize(
            760,
            620,
        )

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #0c0910;
                color: #f4eff8;
            }

            QTextEdit, QLineEdit {
                background: #17111f;
                border: 1px solid #5b21b6;
                border-radius: 8px;
                padding: 10px;
                color: #f4eff8;
            }

            QPushButton {
                background: #6d28d9;
                border: 1px solid #8b5cf6;
                border-radius: 8px;
                padding: 10px 18px;
                color: white;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #7c3aed;
            }
        """)

        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        title = QLabel("WEBBIE")
        title.setFont(
            QFont(
                "Sans Serif",
                28,
                QFont.Bold,
            )
        )

        title.setStyleSheet(
            "color: #a78bfa;"
        )

        layout.addWidget(title)

        subtitle = QLabel(
            "Resident AI · Spider OS\n"
            "Wake: Hey Webbie · Webbie · Hey Web · Web"
        )

        subtitle.setStyleSheet(
            "color: #aaa0b7;"
        )

        layout.addWidget(subtitle)

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)

        self.chat.append(
            "<b style='color:#a78bfa'>Webbie:</b> "
            "I'm online."
        )

        layout.addWidget(
            self.chat,
            1,
        )

        row = QHBoxLayout()

        self.entry = QLineEdit()

        self.entry.setPlaceholderText(
            "Ask Webbie or tell her what to open..."
        )

        self.entry.returnPressed.connect(
            self.send
        )

        row.addWidget(
            self.entry,
            1,
        )

        button = QPushButton("SEND")

        button.clicked.connect(
            self.send
        )

        row.addWidget(button)

        layout.addLayout(row)

        footer = QLabel(
            "YOUR LIFE. ONE WEB."
        )

        footer.setAlignment(
            Qt.AlignCenter
        )

        footer.setStyleSheet(
            "color: #645b6d;"
        )

        layout.addWidget(footer)

    def request(self, text):
        client = socket.socket(
            socket.AF_UNIX,
            socket.SOCK_STREAM,
        )

        client.settimeout(130)

        try:
            client.connect(
                str(SOCKET_PATH)
            )

            client.sendall(
                text.encode("utf-8")
            )

            data = client.recv(
                65536
            )

            return data.decode(
                "utf-8",
                errors="replace",
            )

        except Exception as error:
            return (
                "Webbie service is unavailable: "
                + str(error)
            )

        finally:
            client.close()

    def send(self):
        text = self.entry.text().strip()

        if not text:
            return

        self.entry.clear()

        self.chat.append(
            "<br><b style='color:#ddd'>You:</b> "
            + text
        )

        QApplication.processEvents()

        reply = self.request(text)

        self.chat.append(
            "<b style='color:#a78bfa'>Webbie:</b> "
            + reply
        )


def main():
    app = QApplication(sys.argv)

    app.setApplicationName(
        "Webbie"
    )

    window = WebbieWindow()
    window.show()

    sys.exit(
        app.exec_()
    )


if __name__ == "__main__":
    main()
