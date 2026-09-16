#!/usr/bin/env python3

import re
import sqlite3
from pathlib import Path


DATA_DIR = (
    Path.home()
    / ".local"
    / "share"
    / "spider-os"
    / "study"
)

DB_PATH = DATA_DIR / "study.db"

DOCUMENTS_ROOT = (
    Path.home()
    / "Documents"
    / "Spider OS"
    / "Study"
)


class StudyStore:
    def __init__(self):
        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        DOCUMENTS_ROOT.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.db = sqlite3.connect(
            DB_PATH
        )

        self.db.row_factory = (
            sqlite3.Row
        )

        self.db.execute(
            "PRAGMA foreign_keys = ON"
        )

        self.create_schema()

    def create_schema(self):
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY,
                course_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                due TEXT DEFAULT '',
                status TEXT DEFAULT 'Open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(course_id)
                    REFERENCES courses(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS notes (
                course_id INTEGER PRIMARY KEY,
                content TEXT DEFAULT '',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(course_id)
                    REFERENCES courses(id)
                    ON DELETE CASCADE
            );
            """
        )

        self.db.commit()

    def ensure_default_course(self):
        count = self.db.execute(
            "SELECT COUNT(*) FROM courses"
        ).fetchone()[0]

        if count == 0:
            self.add_course(
                "General Study"
            )

    def courses(self):
        return self.db.execute(
            """
            SELECT id, name
            FROM courses
            ORDER BY name COLLATE NOCASE
            """
        ).fetchall()

    def add_course(self, name):
        name = name.strip()

        if not name:
            return None

        cursor = self.db.execute(
            """
            INSERT INTO courses(name)
            VALUES(?)
            """,
            (name,),
        )

        self.db.commit()

        self.course_folder(
            cursor.lastrowid
        )

        return cursor.lastrowid

    def remove_course(self, course_id):
        self.db.execute(
            """
            DELETE FROM courses
            WHERE id = ?
            """,
            (course_id,),
        )

        self.db.commit()

    def course(self, course_id):
        return self.db.execute(
            """
            SELECT id, name
            FROM courses
            WHERE id = ?
            """,
            (course_id,),
        ).fetchone()

    def course_folder(self, course_id):
        course = self.course(
            course_id
        )

        if not course:
            return DOCUMENTS_ROOT

        safe = re.sub(
            r"[^A-Za-z0-9._-]+",
            "_",
            course["name"],
        ).strip("_")

        if not safe:
            safe = (
                f"Course_{course_id}"
            )

        folder = (
            DOCUMENTS_ROOT
            / safe
        )

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        (folder / "Assignments").mkdir(
            exist_ok=True
        )

        (folder / "Notes").mkdir(
            exist_ok=True
        )

        (folder / "Resources").mkdir(
            exist_ok=True
        )

        (folder / "Research").mkdir(
            exist_ok=True
        )

        return folder

    def assignments(self, course_id):
        return self.db.execute(
            """
            SELECT
                id,
                title,
                due,
                status
            FROM assignments
            WHERE course_id = ?
            ORDER BY
                CASE
                    WHEN status = 'Complete'
                    THEN 1
                    ELSE 0
                END,
                due,
                title
            """,
            (course_id,),
        ).fetchall()

    def add_assignment(
        self,
        course_id,
        title,
        due="",
    ):
        title = title.strip()
        due = due.strip()

        if not title:
            return

        self.db.execute(
            """
            INSERT INTO assignments(
                course_id,
                title,
                due
            )
            VALUES(?, ?, ?)
            """,
            (
                course_id,
                title,
                due,
            ),
        )

        self.db.commit()

    def set_assignment_status(
        self,
        assignment_id,
        status,
    ):
        self.db.execute(
            """
            UPDATE assignments
            SET status = ?
            WHERE id = ?
            """,
            (
                status,
                assignment_id,
            ),
        )

        self.db.commit()

    def delete_assignment(
        self,
        assignment_id,
    ):
        self.db.execute(
            """
            DELETE FROM assignments
            WHERE id = ?
            """,
            (assignment_id,),
        )

        self.db.commit()

    def get_notes(
        self,
        course_id,
    ):
        row = self.db.execute(
            """
            SELECT content
            FROM notes
            WHERE course_id = ?
            """,
            (course_id,),
        ).fetchone()

        if not row:
            return ""

        return row["content"]

    def save_notes(
        self,
        course_id,
        content,
    ):
        self.db.execute(
            """
            INSERT INTO notes(
                course_id,
                content,
                updated_at
            )
            VALUES(
                ?,
                ?,
                CURRENT_TIMESTAMP
            )

            ON CONFLICT(course_id)
            DO UPDATE SET
                content = excluded.content,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                course_id,
                content,
            ),
        )

        self.db.commit()

    def close(self):
        self.db.close()
