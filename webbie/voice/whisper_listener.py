#!/usr/bin/env python3

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


WHISPER_BIN = (
    shutil.which("whisper-cli")
    or "/usr/local/bin/whisper-cli"
)

MODEL_PATH = Path(
    os.environ.get(
        "WEBBIE_WHISPER_MODEL",
        "/usr/local/share/spider-os/whisper/ggml-base.en.bin",
    )
)

CHUNK_SECONDS = int(
    os.environ.get(
        "WEBBIE_WHISPER_CHUNK_SECONDS",
        "4",
    )
)

RUNTIME_DIR = Path(
    os.environ.get(
        "XDG_RUNTIME_DIR",
        f"/run/user/{os.getuid()}",
    )
) / "spider-os"

SPEAKING_MARKER = (
    RUNTIME_DIR
    / "webbie-speaking"
)


def ready():
    return (
        Path(WHISPER_BIN).exists()
        and MODEL_PATH.exists()
        and shutil.which("arecord")
    )


def record_chunk(path):
    result = subprocess.run(
        [
            "arecord",
            "-q",
            "-f",
            "S16_LE",
            "-r",
            "16000",
            "-c",
            "1",
            "-d",
            str(CHUNK_SECONDS),
            path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    return result.returncode == 0


def transcribe(path):
    output_base = (
        str(path)
        + ".webbie"
    )

    output_file = Path(
        output_base + ".txt"
    )

    command = [
        WHISPER_BIN,
        "-m",
        str(MODEL_PATH),
        "-f",
        str(path),
        "-l",
        "en",
        "-nt",
        "-otxt",
        "-of",
        output_base,
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
            check=False,
        )

        if result.returncode != 0:
            return ""

        if not output_file.exists():
            return ""

        text = output_file.read_text(
            encoding="utf-8",
            errors="replace",
        ).strip()

        junk = {
            "",
            "[blank_audio]",
            "[silence]",
            "(silence)",
            "[music]",
            "(music)",
        }

        if text.lower() in junk:
            return ""

        return text

    except Exception:
        return ""

    finally:
        try:
            output_file.unlink()
        except OSError:
            pass


def listen_forever(
    on_text,
    should_continue,
):
    if not ready():
        raise RuntimeError(
            "whisper.cpp or its model is not installed"
        )

    RUNTIME_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    while should_continue():

        # Do not let Webbie hear herself talking.
        if SPEAKING_MARKER.exists():
            time.sleep(0.25)
            continue

        audio_path = None

        try:
            with tempfile.NamedTemporaryFile(
                prefix="webbie-",
                suffix=".wav",
                delete=False,
            ) as temp:
                audio_path = temp.name

            if not record_chunk(
                audio_path
            ):
                time.sleep(1)
                continue

            # If Webbie began speaking during capture,
            # throw this chunk away.
            if SPEAKING_MARKER.exists():
                continue

            phrase = transcribe(
                audio_path
            )

            if phrase:
                on_text(phrase)

        finally:
            if audio_path:
                try:
                    Path(
                        audio_path
                    ).unlink()
                except OSError:
                    pass


if __name__ == "__main__":
    print(
        "whisper.cpp ready:"
        if ready()
        else
        "whisper.cpp unavailable"
    )
