#!/usr/bin/env python3

import json
import os
import re
import sqlite3
import sys
import urllib.request
from datetime import datetime
from pathlib import Path


APP_DATA = (
    Path.home()
    / ".local"
    / "share"
    / "spider-os"
    / "forage"
)

DB_PATH = APP_DATA / "forage.db"

REPORT_DIR = (
    Path.home()
    / "Documents"
    / "Spider OS"
    / "Forage"
    / "Research"
)

OLLAMA_URL = (
    "http://127.0.0.1:11434/api/chat"
)

OLLAMA_MODEL = "qwen3:1.7b"

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",
    ".log",
    ".html",
    ".htm",
    ".css",
    ".sh",
}

SKIP_DIRS = {
    ".git",
    ".cache",
    ".local",
    ".npm",
    ".cargo",
    ".rustup",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
}

MAX_FILE_SIZE = 2 * 1024 * 1024


def enable_ddgs():
    try:
        from ddgs import DDGS
        return DDGS
    except ImportError:
        pass

    root = Path(
        "/opt/spider-forage/lib"
    )

    if root.exists():
        for site in root.glob(
            "python*/site-packages"
        ):
            sys.path.insert(
                0,
                str(site),
            )

    try:
        from ddgs import DDGS
        return DDGS
    except ImportError:
        return None


def ensure_storage():
    APP_DATA.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def database():
    ensure_storage()

    db = sqlite3.connect(
        DB_PATH
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            modified REAL NOT NULL
        )
        """
    )

    db.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS
        files_fts
        USING fts5(
            title,
            content,
            content='files',
            content_rowid='id'
        )
        """
    )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS
        files_ai
        AFTER INSERT ON files
        BEGIN
            INSERT INTO files_fts(
                rowid,
                title,
                content
            )
            VALUES(
                new.id,
                new.title,
                new.content
            );
        END
        """
    )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS
        files_ad
        AFTER DELETE ON files
        BEGIN
            INSERT INTO files_fts(
                files_fts,
                rowid,
                title,
                content
            )
            VALUES(
                'delete',
                old.id,
                old.title,
                old.content
            );
        END
        """
    )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS
        files_au
        AFTER UPDATE ON files
        BEGIN
            INSERT INTO files_fts(
                files_fts,
                rowid,
                title,
                content
            )
            VALUES(
                'delete',
                old.id,
                old.title,
                old.content
            );

            INSERT INTO files_fts(
                rowid,
                title,
                content
            )
            VALUES(
                new.id,
                new.title,
                new.content
            );
        END
        """
    )

    db.commit()

    return db


def default_index_roots():
    home = Path.home()

    candidates = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Projects",
        home / "Music",
        home / "Pictures",
    ]

    return [
        path
        for path in candidates
        if path.exists()
    ]


def readable_file(path):
    try:
        if not path.is_file():
            return False

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            return False

        if path.stat().st_size > MAX_FILE_SIZE:
            return False

        return True

    except OSError:
        return False


def read_text_file(path):
    try:
        return path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return ""


def should_skip(path):
    for part in path.parts:
        if part in SKIP_DIRS:
            return True

        if (
            part.startswith(".")
            and part
            not in {
                ".",
                "..",
            }
        ):
            return True

    return False


def index_local_files(
    roots=None,
    progress=None,
):
    if roots is None:
        roots = default_index_roots()

    db = database()

    indexed = 0
    skipped = 0

    for root in roots:
        root = Path(root)

        if not root.exists():
            continue

        for path in root.rglob("*"):

            if should_skip(path):
                skipped += 1
                continue

            if not readable_file(path):
                continue

            content = read_text_file(
                path
            )

            if not content.strip():
                continue

            try:
                modified = (
                    path.stat().st_mtime
                )
            except OSError:
                continue

            previous = db.execute(
                """
                SELECT modified
                FROM files
                WHERE path = ?
                """,
                (
                    str(path),
                ),
            ).fetchone()

            if (
                previous
                and previous[0]
                == modified
            ):
                continue

            db.execute(
                """
                INSERT INTO files(
                    path,
                    title,
                    content,
                    modified
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT(path)
                DO UPDATE SET
                    title=excluded.title,
                    content=excluded.content,
                    modified=excluded.modified
                """,
                (
                    str(path),
                    path.name,
                    content,
                    modified,
                ),
            )

            indexed += 1

            if progress:
                progress(
                    str(path)
                )

            if indexed % 50 == 0:
                db.commit()

    db.commit()
    db.close()

    return {
        "indexed": indexed,
        "skipped": skipped,
    }


def fts_query(text):
    words = re.findall(
        r"[A-Za-z0-9_'-]+",
        text,
    )

    return " ".join(
        f'"{word}"'
        for word in words
        if word
    )


def local_search(
    query,
    limit=30,
):
    if not DB_PATH.exists():
        return []

    match = fts_query(query)

    if not match:
        return []

    db = database()

    try:
        rows = db.execute(
            """
            SELECT
                files.path,
                files.title,
                snippet(
                    files_fts,
                    1,
                    '',
                    '',
                    ' … ',
                    22
                )
            FROM files_fts
            JOIN files
                ON files.id
                = files_fts.rowid
            WHERE files_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (
                match,
                limit,
            ),
        ).fetchall()

    except sqlite3.Error:
        rows = []

    finally:
        db.close()

    return [
        {
            "path": row[0],
            "title": row[1],
            "snippet": row[2],
        }
        for row in rows
    ]


def web_search(
    query,
    max_results=12,
    timelimit=None,
):
    DDGS = enable_ddgs()

    if DDGS is None:
        raise RuntimeError(
            "DDGS web search engine "
            "is not installed."
        )

    engine = DDGS(
        timeout=15
    )

    results = engine.text(
        query,
        region="us-en",
        safesearch="moderate",
        timelimit=timelimit,
        max_results=max_results,
        backend="auto",
    )

    cleaned = []

    for result in results or []:
        cleaned.append(
            {
                "title": str(
                    result.get(
                        "title",
                        "",
                    )
                ),
                "url": str(
                    result.get(
                        "href",
                        "",
                    )
                ),
                "snippet": str(
                    result.get(
                        "body",
                        "",
                    )
                ),
            }
        )

    return cleaned


def extract_url(
    url,
    max_chars=7000,
):
    DDGS = enable_ddgs()

    if DDGS is None:
        return ""

    try:
        result = DDGS(
            timeout=20
        ).extract(
            url,
            fmt="text_plain",
        )

        content = str(
            result.get(
                "content",
                "",
            )
        )

        return content[
            :max_chars
        ]

    except Exception:
        return ""


def ollama_chat(
    prompt,
    system=None,
    timeout=180,
):
    messages = []

    if system:
        messages.append(
            {
                "role": "system",
                "content": system,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": messages,
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(
            payload
        ).encode("utf-8"),
        headers={
            "Content-Type":
            "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        return (
            data.get(
                "message",
                {},
            )
            .get(
                "content",
                "",
            )
            .strip()
        )

    except Exception:
        return None


def build_research_queries(
    topic,
):
    prompt = f"""
Generate four useful web-search queries
for researching this topic:

{topic}

Cover:
1. the central question
2. evidence or primary information
3. limitations, disagreements, or criticism
4. recent or updated information

Return ONLY the four search queries,
one per line.
""".strip()

    response = ollama_chat(
        prompt,
        system=(
            "You generate concise "
            "research search queries."
        ),
        timeout=60,
    )

    if response:
        lines = []

        for line in response.splitlines():
            line = re.sub(
                r"^[\s0-9.)*-]+",
                "",
                line,
            ).strip()

            if line:
                lines.append(line)

        if len(lines) >= 3:
            return lines[:4]

    return [
        topic,
        f"{topic} evidence research",
        f"{topic} limitations criticism",
        f"{topic} latest developments",
    ]


def deep_research(
    topic,
    progress=None,
):
    ensure_storage()

    queries = build_research_queries(
        topic
    )

    if progress:
        progress(
            "Building research map..."
        )

    results = []
    seen = set()

    for query in queries:

        if progress:
            progress(
                f"Searching: {query}"
            )

        try:
            found = web_search(
                query,
                max_results=6,
            )

        except Exception as error:
            if progress:
                progress(
                    "Search warning: "
                    + str(error)
                )
            continue

        for item in found:
            url = item.get(
                "url",
                "",
            )

            if (
                not url
                or url in seen
            ):
                continue

            seen.add(url)
            results.append(item)

    results = results[:12]

    sources = []

    for index, item in enumerate(
        results,
        start=1,
    ):
        if progress:
            progress(
                f"Reading source "
                f"{index}/{len(results)}: "
                f"{item['title'][:60]}"
            )

        content = extract_url(
            item["url"],
            max_chars=6000,
        )

        sources.append(
            {
                **item,
                "content": content,
            }
        )

    source_text = []

    for number, source in enumerate(
        sources,
        start=1,
    ):
        content = (
            source["content"]
            or source["snippet"]
        )

        source_text.append(
            f"""
SOURCE {number}
TITLE: {source['title']}
URL: {source['url']}
CONTENT:
{content}
""".strip()
        )

    joined = "\n\n".join(
        source_text
    )

    prompt = f"""
Research topic:

{topic}

Using ONLY the source material below,
write a careful research report.

Requirements:
- Explain the main findings.
- Separate established information
  from uncertainty or disagreement.
- Mention meaningful limitations.
- Do not invent facts.
- Cite sources using [1], [2], etc.
- Finish with a section called
  "What to investigate next."

SOURCE MATERIAL

{joined}
""".strip()

    if progress:
        progress(
            "Synthesizing findings "
            "with local Webbie AI..."
        )

    synthesis = ollama_chat(
        prompt,
        system=(
            "You are Deep Forage, "
            "Spider OS's research engine. "
            "Use only supplied evidence. "
            "Never invent citations."
        ),
        timeout=300,
    )

    if not synthesis:
        synthesis = (
            "Deep Forage gathered the "
            "sources, but the local "
            "Ollama model was unavailable."
        )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    safe_topic = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        topic,
    ).strip("_")[:50]

    report_path = (
        REPORT_DIR
        / (
            f"{timestamp}_"
            f"{safe_topic or 'research'}"
            ".md"
        )
    )

    report_lines = [
        f"# Deep Forage: {topic}",
        "",
        f"Generated: "
        f"{datetime.now().isoformat()}",
        "",
        synthesis,
        "",
        "## Sources",
        "",
    ]

    for number, source in enumerate(
        sources,
        start=1,
    ):
        report_lines.append(
            f"{number}. "
            f"[{source['title']}]"
            f"({source['url']})"
        )

    report_path.write_text(
        "\n".join(
            report_lines
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "topic": topic,
        "queries": queries,
        "sources": sources,
        "report": synthesis,
        "report_path": str(
            report_path
        ),
    }
