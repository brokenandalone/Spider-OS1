#!/usr/bin/env python3

import os
import shutil
import subprocess
import tempfile


ONLINE_VOICE = "en-AU-NatashaNeural"
OFFLINE_VOICE = "en-au+f3"


def _edge_tts_binary():
    candidates = [
        "/opt/spider-webbie/bin/edge-tts",
        "/usr/local/bin/edge-tts",
        shutil.which("edge-tts"),
    ]

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    return None


def _speak_edge(text):
    edge_tts = _edge_tts_binary()

    if not edge_tts:
        return False

    player = shutil.which("mpv")

    if not player:
        return False

    path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        ) as temp:
            path = temp.name

        subprocess.run(
            [
                edge_tts,
                "--voice",
                ONLINE_VOICE,
                "--text",
                text,
                "--write-media",
                path,
            ],
            check=True,
            timeout=60,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        subprocess.run(
            [
                player,
                "--no-video",
                "--really-quiet",
                path,
            ],
            check=True,
            timeout=120,
        )

        return True

    except Exception:
        return False

    finally:
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass


def _speak_espeak(text):
    binary = shutil.which("espeak-ng")

    if not binary:
        return False

    try:
        subprocess.run(
            [
                binary,
                "-v",
                OFFLINE_VOICE,
                "-s",
                "165",
                text,
            ],
            check=False,
            timeout=120,
        )

        return True

    except Exception:
        return False


def speak(text):
    text = str(text or "").strip()

    if not text:
        return

    if _speak_edge(text):
        return

    _speak_espeak(text)


if __name__ == "__main__":
    import sys

    speak(" ".join(sys.argv[1:]) or "Webbie voice online.")
