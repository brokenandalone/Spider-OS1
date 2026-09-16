#!/usr/bin/env python3

import html
import os
import sys
import webbrowser

from PyQt5.QtCore import (
    QThread,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

sys.path.insert(
    0,
    ROOT,
)

from engine import (
    index_local_files,
    local_search,
    web_search,
)


class Worker(QThread):
    finished_data = pyqtSignal(
        object
    )

    failed = pyqtSignal(
        str
    )

    status = pyqtSignal(
        str
    )

    def __init__(
        self,
        mode,
        query=None,
    ):
        super().__init__()

        self.mode = mode
        self.query = query

    def run(self):
        try:
            if self.mode == "index":
                data = index_local_files(
                    progress=self.status.emit
                )

            elif self.mode == "local":
                data = local_search(
                    self.query
                )

            elif self.mode == "web":
                data = web_search(
                    self.query
                )

            else:
                raise RuntimeError(
                    "Unknown Forage mode."
                )

            self.finished_data.emit(
                data
            )

        except Exception as error:
            self.failed.emit(
                str(error)
            )


class ForageWindow(
    QMainWindow
):
    def __init__(self):
        super().__init__()

        self.worker = None

        self.setWindowTitle(
            "Forage | Spider OS"
        )

        self.resize(
            1000,
            720,
        )

        self.setStyleSheet(
            """
            QMainWindow,
            QWidget {
                background: #0a080d;
                color: #f0eaf5;
            }

            QLineEdit,
            QComboBox,
            QTextBrowser {
                background: #15101b;
                border: 1px solid #4c1d95;
                border-radius: 8px;
                padding: 9px;
                color: #f0eaf5;
            }

            QPushButton {
                background: #581c87;
                border: 1px solid #7e22ce;
                border-radius: 8px;
                padding: 10px 15px;
                color: white;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #6b21a8;
            }
            """
        )

        root = QWidget()
        self.setCentralWidget(
            root
        )

        layout = QVBoxLayout(
            root
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        title = QLabel(
            "FORAGE"
        )

        title.setStyleSheet(
            """
            font-size: 32px;
            font-weight: bold;
            color: #c084fc;
            """
        )

        layout.addWidget(
            title
        )

        subtitle = QLabel(
            "SEARCH  •  CONNECT  •  DISCOVER\n"
            "Hunt information. Find meaning."
        )

        subtitle.setStyleSheet(
            "color: #aaa0b4;"
        )

        layout.addWidget(
            subtitle
        )

        row = QHBoxLayout()

        self.mode = QComboBox()

        self.mode.addItems(
            [
                "Web",
                "Local Files",
            ]
        )

        row.addWidget(
            self.mode
        )

        self.query = QLineEdit()

        self.query.setPlaceholderText(
            "Search Forage..."
        )

        self.query.returnPressed.connect(
            self.search
        )

        row.addWidget(
            self.query,
            1,
        )

        button = QPushButton(
            "SEARCH"
        )

        button.clicked.connect(
            self.search
        )

        row.addWidget(
            button
        )

        deep = QPushButton(
            "DEEP FORAGE"
        )

        deep.clicked.connect(
            self.deep_forage
        )

        row.addWidget(
            deep
        )

        layout.addLayout(
            row
        )

        index_button = QPushButton(
            "INDEX MY LOCAL FILES"
        )

        index_button.clicked.connect(
            self.index_files
        )

        layout.addWidget(
            index_button
        )

        self.status = QLabel(
            "Ready."
        )

        self.status.setStyleSheet(
            "color: #9b90a6;"
        )

        layout.addWidget(
            self.status
        )

        self.results = QTextBrowser()

        self.results.setOpenExternalLinks(
            True
        )

        layout.addWidget(
            self.results,
            1,
        )

        footer = QLabel(
            "FORAGE · SPIDER OS · YOUR LIFE. ONE WEB."
        )

        footer.setStyleSheet(
            "color: #5c5265;"
        )

        layout.addWidget(
            footer
        )

    def set_worker(
        self,
        worker,
    ):
        self.worker = worker

        worker.status.connect(
            self.status.setText
        )

        worker.failed.connect(
            self.failure
        )

        worker.start()

    def failure(
        self,
        message,
    ):
        self.status.setText(
            "Forage error."
        )

        self.results.setPlainText(
            message
        )

    def index_files(self):
        self.status.setText(
            "Indexing local files..."
        )

        worker = Worker(
            "index"
        )

        worker.finished_data.connect(
            self.index_complete
        )

        self.set_worker(
            worker
        )

    def index_complete(
        self,
        data,
    ):
        self.status.setText(
            "Local index updated."
        )

        self.results.setHtml(
            "<h2>Local Knowledge Index</h2>"
            f"<p>Updated files: "
            f"{data['indexed']}</p>"
            f"<p>Skipped entries: "
            f"{data['skipped']}</p>"
            "<p>Your indexed file content "
            "remains on this computer.</p>"
        )

    def search(self):
        query = (
            self.query.text()
            .strip()
        )

        if not query:
            return

        mode = (
            "web"
            if self.mode.currentText()
            == "Web"
            else "local"
        )

        self.status.setText(
            f"Searching {mode}..."
        )

        worker = Worker(
            mode,
            query,
        )

        worker.finished_data.connect(
            lambda data:
            self.show_results(
                mode,
                query,
                data,
            )
        )

        self.set_worker(
            worker
        )

    def show_results(
        self,
        mode,
        query,
        data,
    ):
        self.status.setText(
            f"{len(data)} results."
        )

        chunks = [
            f"<h2>{html.escape(query)}</h2>"
        ]

        if not data:
            chunks.append(
                "<p>No results found.</p>"
            )

        for item in data:

            if mode == "web":
                title = html.escape(
                    item.get(
                        "title",
                        "",
                    )
                )

                url = html.escape(
                    item.get(
                        "url",
                        "",
                    ),
                    quote=True,
                )

                snippet = html.escape(
                    item.get(
                        "snippet",
                        "",
                    )
                )

                chunks.append(
                    f"""
                    <div style="
                        margin-bottom:20px;
                        padding:14px;
                        border:1px solid #35263f;
                        border-radius:8px;
                    ">
                    <a href="{url}">
                    <b>{title}</b>
                    </a>
                    <p>{snippet}</p>
                    <small>{url}</small>
                    </div>
                    """
                )

            else:
                path = html.escape(
                    item.get(
                        "path",
                        "",
                    )
                )

                title = html.escape(
                    item.get(
                        "title",
                        "",
                    )
                )

                snippet = html.escape(
                    item.get(
                        "snippet",
                        "",
                    )
                )

                chunks.append(
                    f"""
                    <div style="
                        margin-bottom:20px;
                        padding:14px;
                        border:1px solid #35263f;
                        border-radius:8px;
                    ">
                    <b>{title}</b>
                    <p>{snippet}</p>
                    <small>{path}</small>
                    </div>
                    """
                )

        self.results.setHtml(
            "\n".join(
                chunks
            )
        )

    def deep_forage(self):
        query = (
            self.query.text()
            .strip()
        )

        script = os.path.join(
            ROOT,
            "deep-forage",
            "deep_forage.py",
        )

        args = [
            sys.executable,
            script,
        ]

        if query:
            args.append(
                query
            )

        import subprocess

        subprocess.Popen(
            args,
            start_new_session=True,
        )


def main():
    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Forage"
    )

    window = ForageWindow()

    window.show()

    sys.exit(
        app.exec_()
    )


if __name__ == "__main__":
    main()
