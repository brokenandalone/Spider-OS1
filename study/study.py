#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QFont,
    QPalette,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


SCRIPT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
)

SPIDER_ROOT = Path(
    "/usr/local/lib/spider-os"
)

if not SPIDER_ROOT.exists():
    SPIDER_ROOT = (
        SCRIPT_ROOT.parent
    )


sys.path.insert(
    0,
    str(SCRIPT_ROOT),
)

from store import StudyStore


WALLPAPER = (
    SPIDER_ROOT
    / "branding"
    / "workspaces"
    / "study.png"
)


class StudyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.store = StudyStore()

        self.store.ensure_default_course()

        self.current_course_id = None
        self.wallpaper = None

        self.setWindowTitle(
            "Study | Spider OS"
        )

        self.resize(
            1200,
            800,
        )

        self.setMinimumSize(
            950,
            650,
        )

        self.set_workspace_context()

        self.build_ui()
        self.load_wallpaper()
        self.load_courses()

    # --------------------------------------------------------
    # SPIDER OS CONTEXT
    # --------------------------------------------------------

    def set_workspace_context(self):
        runtime = Path(
            os.environ.get(
                "XDG_RUNTIME_DIR",
                f"/run/user/{os.getuid()}",
            )
        ) / "spider-os"

        try:
            runtime.mkdir(
                parents=True,
                exist_ok=True,
            )

            (
                runtime
                / "workspace"
            ).write_text(
                "study",
                encoding="utf-8",
            )

        except Exception:
            pass

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def build_ui(self):
        self.setStyleSheet(
            """
            QWidget#root {
                background:
                    rgba(9, 7, 12, 230);
            }

            QLabel {
                color:#f2edf5;
            }

            QListWidget,
            QTableWidget,
            QTextEdit {
                background:
                    rgba(20, 15, 27, 235);

                border:
                    1px solid #4c1d95;

                border-radius:
                    8px;

                color:
                    #f1eaf6;
            }

            QListWidget::item {
                padding:9px;
            }

            QListWidget::item:selected {
                background:#581c87;
            }

            QPushButton {
                background:
                    rgba(88, 28, 135, 225);

                border:
                    1px solid #7e22ce;

                border-radius:
                    8px;

                padding:
                    10px;

                color:
                    white;

                font-weight:
                    bold;
            }

            QPushButton:hover {
                background:#6b21a8;
                border-color:#c084fc;
            }

            QTabWidget::pane {
                border:
                    1px solid #3b2747;

                border-radius:
                    8px;

                background:
                    rgba(10, 8, 13, 220);
            }

            QTabBar::tab {
                background:#17101e;
                color:#c9bdcf;
                padding:10px 18px;
            }

            QTabBar::tab:selected {
                background:#581c87;
                color:white;
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
            26,
            24,
            26,
            24,
        )

        title = QLabel(
            "STUDY"
        )

        title.setFont(
            QFont(
                "Sans Serif",
                34,
                QFont.Bold,
            )
        )

        title.setStyleSheet(
            "color:#c084fc;"
        )

        outer.addWidget(
            title
        )

        subtitle = QLabel(
            "LEARN  •  READ  •  RESEARCH  •  ANALYZE  •  WRITE  •  ACHIEVE"
        )

        subtitle.setStyleSheet(
            """
            color:#b4a7bd;
            font-size:14px;
            padding-bottom:4px;
            """
        )

        outer.addWidget(
            subtitle
        )

        actions = QHBoxLayout()

        self.add_action(
            actions,
            "LEARN",
            self.open_webbie,
        )

        self.add_action(
            actions,
            "READ",
            self.read_document,
        )

        self.add_action(
            actions,
            "RESEARCH",
            self.open_forage,
        )

        self.add_action(
            actions,
            "ANALYZE",
            self.open_deep_forage,
        )

        self.add_action(
            actions,
            "WRITE",
            self.open_writer,
        )

        self.add_action(
            actions,
            "ACHIEVE",
            self.focus_assignments,
        )

        outer.addLayout(
            actions
        )

        splitter = QSplitter(
            Qt.Horizontal
        )

        # ----------------------------------------------------
        # COURSES
        # ----------------------------------------------------

        course_panel = QWidget()

        course_layout = QVBoxLayout(
            course_panel
        )

        course_title = QLabel(
            "COURSES"
        )

        course_title.setStyleSheet(
            """
            font-size:18px;
            font-weight:bold;
            color:#d8b4fe;
            """
        )

        course_layout.addWidget(
            course_title
        )

        self.courses = QListWidget()

        self.courses.currentItemChanged.connect(
            self.course_changed
        )

        course_layout.addWidget(
            self.courses,
            1,
        )

        add_course = QPushButton(
            "+ ADD COURSE"
        )

        add_course.clicked.connect(
            self.add_course
        )

        course_layout.addWidget(
            add_course
        )

        open_folder = QPushButton(
            "OPEN COURSE FOLDER"
        )

        open_folder.clicked.connect(
            self.open_course_folder
        )

        course_layout.addWidget(
            open_folder
        )

        remove_course = QPushButton(
            "REMOVE COURSE"
        )

        remove_course.clicked.connect(
            self.remove_course
        )

        course_layout.addWidget(
            remove_course
        )

        splitter.addWidget(
            course_panel
        )

        # ----------------------------------------------------
        # MAIN STUDY AREA
        # ----------------------------------------------------

        main_panel = QWidget()

        main_layout = QVBoxLayout(
            main_panel
        )

        self.course_heading = QLabel(
            "Study"
        )

        self.course_heading.setStyleSheet(
            """
            font-size:24px;
            font-weight:bold;
            color:#e9d5ff;
            """
        )

        main_layout.addWidget(
            self.course_heading
        )

        self.tabs = QTabWidget()

        # Assignments tab
        assignments_tab = QWidget()

        assignments_layout = QVBoxLayout(
            assignments_tab
        )

        self.assignment_table = QTableWidget(
            0,
            3,
        )

        self.assignment_table.setHorizontalHeaderLabels(
            [
                "Assignment",
                "Due",
                "Status",
            ]
        )

        self.assignment_table.horizontalHeader().setStretchLastSection(
            True
        )

        assignments_layout.addWidget(
            self.assignment_table
        )

        assignment_buttons = QHBoxLayout()

        add_assignment = QPushButton(
            "+ ADD ASSIGNMENT"
        )

        add_assignment.clicked.connect(
            self.add_assignment
        )

        assignment_buttons.addWidget(
            add_assignment
        )

        complete_assignment = QPushButton(
            "MARK COMPLETE"
        )

        complete_assignment.clicked.connect(
            self.complete_assignment
        )

        assignment_buttons.addWidget(
            complete_assignment
        )

        reopen_assignment = QPushButton(
            "REOPEN"
        )

        reopen_assignment.clicked.connect(
            self.reopen_assignment
        )

        assignment_buttons.addWidget(
            reopen_assignment
        )

        delete_assignment = QPushButton(
            "DELETE"
        )

        delete_assignment.clicked.connect(
            self.delete_assignment
        )

        assignment_buttons.addWidget(
            delete_assignment
        )

        assignments_layout.addLayout(
            assignment_buttons
        )

        self.tabs.addTab(
            assignments_tab,
            "Assignments",
        )

        # Notes tab
        notes_tab = QWidget()

        notes_layout = QVBoxLayout(
            notes_tab
        )

        self.notes = QTextEdit()

        self.notes.setPlaceholderText(
            "Course notes, ideas, study material, "
            "questions, reminders..."
        )

        notes_layout.addWidget(
            self.notes
        )

        save_notes = QPushButton(
            "SAVE NOTES"
        )

        save_notes.clicked.connect(
            self.save_notes
        )

        notes_layout.addWidget(
            save_notes
        )

        self.tabs.addTab(
            notes_tab,
            "Notes",
        )

        main_layout.addWidget(
            self.tabs,
            1,
        )

        self.status = QLabel(
            "Study ready."
        )

        self.status.setStyleSheet(
            "color:#9e92a6;"
        )

        main_layout.addWidget(
            self.status
        )

        splitter.addWidget(
            main_panel
        )

        splitter.setSizes(
            [
                280,
                850,
            ]
        )

        outer.addWidget(
            splitter,
            1,
        )

        footer = QLabel(
            "STUDY · SPIDER OS · YOUR LIFE. ONE WEB."
        )

        footer.setAlignment(
            Qt.AlignCenter
        )

        footer.setStyleSheet(
            """
            color:#665a6e;
            font-weight:bold;
            """
        )

        outer.addWidget(
            footer
        )

    def add_action(
        self,
        layout,
        title,
        callback,
    ):
        button = QPushButton(
            title
        )

        button.clicked.connect(
            callback
        )

        layout.addWidget(
            button
        )

    # --------------------------------------------------------
    # WALLPAPER
    # --------------------------------------------------------

    def load_wallpaper(self):
        if not WALLPAPER.exists():
            return

        self.wallpaper = QPixmap(
            str(WALLPAPER)
        )

        self.apply_wallpaper()

    def apply_wallpaper(self):
        if (
            self.wallpaper is None
            or self.wallpaper.isNull()
        ):
            return

        scaled = self.wallpaper.scaled(
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

    # --------------------------------------------------------
    # COURSES
    # --------------------------------------------------------

    def load_courses(self):
        selected = self.current_course_id

        self.courses.clear()

        first_item = None
        selected_item = None

        for course in self.store.courses():
            item = QListWidgetItem(
                course["name"]
            )

            item.setData(
                Qt.UserRole,
                course["id"],
            )

            self.courses.addItem(
                item
            )

            if first_item is None:
                first_item = item

            if (
                selected
                == course["id"]
            ):
                selected_item = item

        target = (
            selected_item
            or first_item
        )

        if target:
            self.courses.setCurrentItem(
                target
            )

    def course_changed(
        self,
        current,
        previous,
    ):
        if not current:
            return

        if (
            previous
            and self.current_course_id
        ):
            self.save_notes(
                quiet=True
            )

        self.current_course_id = (
            current.data(
                Qt.UserRole
            )
        )

        self.course_heading.setText(
            current.text()
        )

        self.load_assignments()

        self.notes.setPlainText(
            self.store.get_notes(
                self.current_course_id
            )
        )

        folder = self.store.course_folder(
            self.current_course_id
        )

        self.status.setText(
            f"Course workspace: {folder}"
        )

    def add_course(self):
        name, ok = QInputDialog.getText(
            self,
            "Add Course",
            "Course name:",
        )

        if (
            not ok
            or not name.strip()
        ):
            return

        self.current_course_id = (
            self.store.add_course(
                name
            )
        )

        self.load_courses()

    def remove_course(self):
        if not self.current_course_id:
            return

        course = self.store.course(
            self.current_course_id
        )

        if not course:
            return

        answer = QMessageBox.question(
            self,
            "Remove Course",
            (
                f"Remove '{course['name']}' "
                "from Study?\n\n"
                "The course folder in Documents "
                "will NOT be deleted."
            ),
        )

        if (
            answer
            != QMessageBox.Yes
        ):
            return

        self.store.remove_course(
            self.current_course_id
        )

        self.current_course_id = None

        self.store.ensure_default_course()

        self.load_courses()

    def open_course_folder(self):
        if not self.current_course_id:
            return

        folder = self.store.course_folder(
            self.current_course_id
        )

        subprocess.Popen(
            [
                "xdg-open",
                str(folder),
            ],
            start_new_session=True,
        )

    # --------------------------------------------------------
    # ASSIGNMENTS
    # --------------------------------------------------------

    def load_assignments(self):
        self.assignment_table.setRowCount(
            0
        )

        if not self.current_course_id:
            return

        for assignment in (
            self.store.assignments(
                self.current_course_id
            )
        ):
            row = (
                self.assignment_table
                .rowCount()
            )

            self.assignment_table.insertRow(
                row
            )

            title = QTableWidgetItem(
                assignment["title"]
            )

            title.setData(
                Qt.UserRole,
                assignment["id"],
            )

            self.assignment_table.setItem(
                row,
                0,
                title,
            )

            self.assignment_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    assignment["due"]
                ),
            )

            self.assignment_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    assignment["status"]
                ),
            )

        self.assignment_table.resizeColumnsToContents()

    def selected_assignment_id(self):
        row = (
            self.assignment_table
            .currentRow()
        )

        if row < 0:
            return None

        item = self.assignment_table.item(
            row,
            0,
        )

        if not item:
            return None

        return item.data(
            Qt.UserRole
        )

    def add_assignment(self):
        if not self.current_course_id:
            return

        title, ok = QInputDialog.getText(
            self,
            "Add Assignment",
            "Assignment:",
        )

        if (
            not ok
            or not title.strip()
        ):
            return

        due, due_ok = QInputDialog.getText(
            self,
            "Due Date",
            (
                "Due date or date/time "
                "(optional):"
            ),
        )

        if not due_ok:
            due = ""

        self.store.add_assignment(
            self.current_course_id,
            title,
            due,
        )

        self.load_assignments()

    def complete_assignment(self):
        assignment_id = (
            self.selected_assignment_id()
        )

        if not assignment_id:
            return

        self.store.set_assignment_status(
            assignment_id,
            "Complete",
        )

        self.load_assignments()

    def reopen_assignment(self):
        assignment_id = (
            self.selected_assignment_id()
        )

        if not assignment_id:
            return

        self.store.set_assignment_status(
            assignment_id,
            "Open",
        )

        self.load_assignments()

    def delete_assignment(self):
        assignment_id = (
            self.selected_assignment_id()
        )

        if not assignment_id:
            return

        self.store.delete_assignment(
            assignment_id
        )

        self.load_assignments()

    # --------------------------------------------------------
    # NOTES
    # --------------------------------------------------------

    def save_notes(
        self,
        quiet=False,
    ):
        if not self.current_course_id:
            return

        self.store.save_notes(
            self.current_course_id,
            self.notes.toPlainText(),
        )

        if not quiet:
            self.status.setText(
                "Notes saved."
            )

    # --------------------------------------------------------
    # STUDY ACTIONS
    # --------------------------------------------------------

    def launch(
        self,
        command,
    ):
        try:
            subprocess.Popen(
                [
                    str(part)
                    for part in command
                ],
                start_new_session=True,
            )

            return True

        except Exception as error:
            self.status.setText(
                str(error)
            )

            return False

    def open_webbie(self):
        path = (
            SPIDER_ROOT
            / "webbie"
            / "ui"
            / "webbie-ui.py"
        )

        if path.exists():
            self.launch(
                [
                    "python3",
                    path,
                ]
            )

            self.status.setText(
                "Webbie opened in Study context."
            )

        else:
            self.status.setText(
                "Webbie is unavailable."
            )

    def read_document(self):
        start = (
            self.store.course_folder(
                self.current_course_id
            )
            if self.current_course_id
            else Path.home()
        )

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Study Material",
            str(start),
            (
                "Documents (*.pdf *.epub *.txt "
                "*.odt *.doc *.docx *.ppt *.pptx);;"
                "All Files (*)"
            ),
        )

        if not filename:
            return

        self.launch(
            [
                "xdg-open",
                filename,
            ]
        )

    def open_forage(self):
        path = (
            SPIDER_ROOT
            / "forage"
            / "forage.py"
        )

        if path.exists():
            self.launch(
                [
                    "python3",
                    path,
                ]
            )

            self.status.setText(
                "Forage opened."
            )

        else:
            self.status.setText(
                "Forage has not been installed yet."
            )

    def open_deep_forage(self):
        path = (
            SPIDER_ROOT
            / "forage"
            / "deep-forage"
            / "deep_forage.py"
        )

        if path.exists():
            self.launch(
                [
                    "python3",
                    path,
                ]
            )

            self.status.setText(
                "Deep Forage opened."
            )

        else:
            self.status.setText(
                "Deep Forage has not been installed yet."
            )

    def open_writer(self):
        if self.current_course_id:
            folder = (
                self.store.course_folder(
                    self.current_course_id
                )
                / "Assignments"
            )
        else:
            folder = Path.home()

        self.launch(
            [
                "libreoffice",
                "--writer",
            ]
        )

        self.status.setText(
            f"Writer opened. Course files: {folder}"
        )

    def focus_assignments(self):
        self.tabs.setCurrentIndex(
            0
        )

        self.assignment_table.setFocus()

        self.status.setText(
            "Assignments in focus."
        )

    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    def closeEvent(
        self,
        event,
    ):
        self.save_notes(
            quiet=True
        )

        self.store.close()

        event.accept()


def main():
    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Study"
    )

    window = StudyWindow()

    window.show()

    sys.exit(
        app.exec_()
    )


if __name__ == "__main__":
    main()
