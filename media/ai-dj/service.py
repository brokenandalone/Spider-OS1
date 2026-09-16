#!/usr/bin/env python3
import json, os, re, shutil, subprocess, time, urllib.request, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 9876
MODEL = "qwen3:1.7b"
OLLAMA = "http://127.0.0.1:11434/api/chat"
VOICE = "en-AU-NatashaNeural"
CACHE = Path.home() / ".cache" / "spider-os" / "ai-dj"
CACHE.mkdir(parents=True, exist_ok=True)


def track_text(track):
    if not isinstance(track, dict):
        return "unknown track"
    title = track.get("title") or track.get("name") or track.get("track") or "unknown track"
    artist = track.get("artist") or track.get("artists") or track.get("albumArtist") or ""
    if isinstance(artist, list):
        artist = ", ".join(str(x) for x in artist)
    return f"{title} by {artist}" if artist else str(title)


def ollama_script(current, nxt):
    prompt = (
        "You are Nova, the local AI radio host inside Spider Media Player on Spider OS. "
        "Write a natural radio transition of no more than 35 words. "
        "Do not quote lyrics. Do not invent facts about the artists. "
        f"The song ending is: {track_text(current)}. "
        f"The next song is: {track_text(nxt)}. "
        "Return only the words the DJ should say."
    )
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": "You write concise radio DJ links."},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        OLLAMA,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data.get("message", {}).get("content", "").strip()
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I).strip()
        if text:
            return text
    except Exception:
        pass
    return f"That was {track_text(current)}. Coming up next, {track_text(nxt)}."


def make_audio(text, ident):
    edge = Path("/opt/spider-webbie/bin/edge-tts")
    mp3 = CACHE / f"{ident}.mp3"
    wav = CACHE / f"{ident}.wav"
    if edge.exists():
        try:
            subprocess.run(
                [str(edge), "--voice", VOICE, "--text", text, "--write-media", str(mp3)],
                check=True,
                timeout=60,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if mp3.exists() and mp3.stat().st_size:
                return mp3
        except Exception:
            pass
    espeak = shutil.which("espeak-ng")
    if espeak:
        try:
            subprocess.run([espeak, "-v", "en-au+f3", "-s", "165", "-w", str(wav), text], check=True, timeout=60)
            if wav.exists() and wav.stat().st_size:
                return wav
        except Exception:
            pass
    raise RuntimeError("No working TTS engine is available")


def cleanup():
    cutoff = time.time() - 86400
    for path in CACHE.glob("*"):
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            pass


class Handler(BaseHTTPRequestHandler):
    def headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def log_message(self, fmt, *args):
        return

    def do_OPTIONS(self):
        self.headers(204)

    def do_GET(self):
        if self.path == "/health":
            self.headers(200)
            self.wfile.write(json.dumps({"ok": True, "service": "Spider AI DJ", "port": PORT}).encode())
            return
        self.headers(404)
        self.wfile.write(b'{"error":"not found"}')

    def do_POST(self):
        if self.path != "/dj/prepare":
            self.headers(404)
            self.wfile.write(b'{"error":"not found"}')
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            current = body.get("currentTrack") or {}
            nxt = body.get("nextTrack") or {}
            script = ollama_script(current, nxt)
            ident = f"dj-{int(time.time())}-{uuid.uuid4().hex[:8]}"
            audio = make_audio(script, ident)
            cleanup()
            response = {
                "id": ident,
                "type": body.get("type") or "transition",
                "script": script,
                "audioFile": audio.resolve().as_uri(),
            }
            self.headers(200)
            self.wfile.write(json.dumps(response).encode("utf-8"))
        except Exception as error:
            self.headers(500)
            self.wfile.write(json.dumps({"error": str(error)}).encode("utf-8"))


def main():
    cleanup()
    print(f"Spider AI DJ listening on http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
