#!/usr/bin/env python3

import html
import os
import sys
import subprocess

from PyQt5.QtCore import (
    QThread,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(
            __file__
        )
    )
)

sys.path.insert(
    0,
    ROOT,
)

from engine import (
    deep_research,
)


class ResearchWorker(
    QThread
):
    progress = pyqtSignal(
        str
    )

    completed = pyqtSignal(
        object
    )

    failed = pyqtSignal(
        str
    )

    def __init__(
        self,
        topic,
    ):
        super().__init__()

        self.topic = topic

    def run(self):
        try:
            result = deep_research(
                self.topic,
                progress=(
                    self.progress.emit
                ),
            )

            self.completed.emit(
                result
            )

        except Exception as error:
            self.failed.emit(
                str(error)
            )


class DeepForageWindow(
    QMainWindow
):
    def __init__(
        self,
        initial_topic="",
    ):
        super().__init__()

        self.worker = None
        self.last_report = None

        self.setWindowTitle(
            "Deep Forage | Spider OS"
        )

        self.resize(
            1050,
            760,
        )

        self.setStyleSheet(
            """
            QMainWindow,
            QWidget {
                background: #09070c;
                color: #f5eff8;
            }

            QLineEdit,
            QTextBrowser {
                background: #150f1d;
                border: 1px solid #6b21a8;
                border-radius: 8px;
                padding: 10px;
                color: #f5eff8;
            }

            QPushButton {
                background: #6b21a8;
                border: 1px solid #9333ea;
                border-radius: 8px;
                padding: 11px;
                color: white;
                font-weight: bold;
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
            25,
            25,
            25,
            25,
        )

        title = QLabel(
            "DEEP FORAGE"
        )

        title.setStyleSheet(
            """
            font-size: 32px;
            font-weight: bold;
            color: #d8b4fe;
            """
        )

        layout.addWidget(
            title
        )

        description = QLabel(
            "Autonomous multi-source research\n"
            "SEARCH · READ · COMPARE · SYNTHESIZE"
        )

        description.setStyleSheet(
            "color:#a99daf;"
        )

        layout.addWidget(
            description
        )

        self.topic = QLineEdit()

        self.topic.setPlaceholderText(
            "What should Deep Forage investigate?"
        )

        self.topic.setText(
            initial_topic
        )

        self.topic.returnPressed.connect(
            self.research
        )

        layout.addWidget(
            self.topic
        )

        self.run_button = QPushButton(
            "BEGIN DEEP FORAGE"
        )

        self.run_button.clicked.connect(
            self.research
        )

        layout.addWidget(
            self.run_button
        )

        self.status = QLabel(
            "Ready."
        )

        self.status.setStyleSheet(
            "color:#9e93a5;"
        )

        layout.addWidget(
            self.status
        )

        self.output = QTextBrowser()

        self.output.setOpenExternalLinks(
            True
        )

        layout.addWidget(
            self.output,
            1,
        )

        self.open_report = QPushButton(
            "OPEN SAVED REPORT"
        )

        self.open_report.setEnabled(
            False
        )

        self.open_report.clicked.connect(
            self.open_saved_report
        )

        layout.addWidget(
            self.open_report
        )

    def research(self):
        topic = (
            self.topic.text()
            .strip()
        )

        if not topic:
            return

        self.run_button.setEnabled(
            False
        )

        self.output.clear()

        self.status.setText(
            "Deep Forage started..."
        )

        self.worker = ResearchWorker(
            topic
        )

        self.worker.progress.connect(
            self.status.setText
        )

        self.worker.failed.connect(
            self.failed
        )

        self.worker.completed.connect(
            self.completed
        )

        self.worker.start()

    def failed(
        self,
        message,
    ):
        self.run_button.setEnabled(
            True
        )

        self.status.setText(
            "Deep Forage failed."
        )

        self.output.setPlainText(
            message
        )

    def completed(
        self,
        result,
    ):
        self.run_button.setEnabled(
            True
        )

        self.last_report = (
            result["report_path"]
        )

        self.open_report.setEnabled(
            True
        )

        self.status.setText(
            "Research complete."
        )

        report = html.escape(
            result["report"]
        ).replace(
            "\n",
            "<br>",
        )

        sources = []

        for index, source in enumerate(
            result["sources"],
            start=1,
        ):
            title = html.escape(
                source["title"]
            )

            url = html.escape(
                source["url"],
                quote=True,
            )

            sources.append(
                f'{index}. '
                f'<a href="{url}">'
                f'{title}</a>'
            )

        self.output.setHtml(
            "<h2>Deep Forage Report</h2>"
            f"<p>{report}</p>"
            "<hr>"
            "<h3>Sources</h3>"
            + "<br>".join(
                sources
            )
            + "<hr>"
            + "<p><b>Saved:</b> "
            + html.escape(
                self.last_report
            )
            + "</p>"
        )

    def open_saved_report(
        self,
    ):
        if not self.last_report:
            return

        subprocess.Popen(
            [
                "xdg-open",
                self.last_report,
            ],
            start_new_session=True,
        )


def main():
    initial = (
        " ".join(
            sys.argv[1:]
        )
        if len(sys.argv) > 1
        else ""
    )

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Deep Forage"
    )

    window = DeepForageWindow(
        initial
    )

    window.show()

    sys.exit(
        app.exec_()
    )


if __name__ == "__main__":
    main()
