#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ! -f distro/build-iso.sh || ! -d the-web || ! -d webbie ]]; then
  echo "Run this from the root of the Spider-OS1 repository." >&2
  exit 1
fi

ROOT="$(pwd)"
mkdir -p media/ai-dj media/bin distro/assets/media distro/config/applications distro/systemd

cat > media/ai-dj/service.py <<'PY'
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
PY

cat > media/ai-dj/spider-ai-dj.service <<'SERVICE'
[Unit]
Description=Spider Media Player AI DJ Service
After=network-online.target ollama.service
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/lib/spider-os/media/ai-dj/service.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=false

[Install]
WantedBy=default.target
SERVICE

cat > media/bin/spider-media-player <<'SH2'
#!/usr/bin/env bash
set -Eeuo pipefail
PROFILE="public"
[[ -r /etc/spider-os/media-profile ]] && PROFILE="$(tr -d '[:space:]' < /etc/spider-os/media-profile)"
export SPIDER_SPM_PROFILE="${PROFILE}"
if [[ "${PROFILE}" == "personal" ]]; then
  export SPIDER_AI_DJ_SERVICE="http://127.0.0.1:9876"
  export SPIDER_AI_DJ_AVAILABLE=1
else
  export SPIDER_AI_DJ_AVAILABLE=0
fi
exec /opt/spider-media-player/spider-media-player "$@"
SH2

cat > distro/config/applications/spider-media-player.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Spider Media Player
GenericName=Media Player
Comment=Spider OS media workspace
Exec=/usr/local/bin/spider-media-player
Icon=spider-os-logo
Terminal=false
Categories=AudioVideo;Audio;Video;
StartupNotify=true
DESKTOP

cat > distro/install-spm.sh <<'SH2'
#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${1:?rootfs required}"
REPO="${2:?repo root required}"
PROFILE="${3:-public}"
ASSETS="${REPO}/distro/assets/media"

case "${PROFILE}" in
  personal)
    CANDIDATES=(
      "${ASSETS}/Spider-Media-Player-7.5.0-Kabel-Linux-x64.zip"
      "${ASSETS}/Spider-Media-Player-7.5.0-Kabel-Linux-x64-NORMALIZED.zip"
    )
    ;;
  public)
    CANDIDATES=("${ASSETS}/Spider-Media-Player-Public-Linux-x64.zip")
    ;;
  *)
    echo "Unknown SPM profile: ${PROFILE}" >&2
    exit 2
    ;;
esac

ZIP=""
for candidate in "${CANDIDATES[@]}"; do
  [[ -f "${candidate}" ]] && ZIP="${candidate}" && break
done

if [[ -z "${ZIP}" ]]; then
  if [[ "${PROFILE}" == "public" ]]; then
    echo "Public Spider Media Player package not supplied; skipping Media for public image."
    exit 0
  fi
  echo "Personal Kabel package missing from distro/assets/media." >&2
  exit 1
fi

echo "Installing Spider Media Player profile: ${PROFILE}"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

python3 - "${ZIP}" "${TMP}" <<'PY'
import pathlib, sys, zipfile
src = pathlib.Path(sys.argv[1])
dst = pathlib.Path(sys.argv[2])
with zipfile.ZipFile(src) as z:
    for info in z.infolist():
        name = info.filename.replace('\\', '/').lstrip('/')
        if not name:
            continue
        rel = pathlib.PurePosixPath(name)
        if '..' in rel.parts:
            raise SystemExit(f"unsafe zip path: {name}")
        out = dst.joinpath(*rel.parts)
        if name.endswith('/'):
            out.mkdir(parents=True, exist_ok=True)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        with z.open(info) as r, open(out, 'wb') as w:
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                w.write(chunk)
PY

SOURCE="${TMP}/linux-unpacked"
[[ -x "${SOURCE}/spider-media-player" ]] || chmod 0755 "${SOURCE}/spider-media-player" 2>/dev/null || true
[[ -f "${SOURCE}/spider-media-player" ]] || { echo "SPM executable missing" >&2; exit 1; }

rm -rf "${ROOTFS}/opt/spider-media-player"
install -d "${ROOTFS}/opt/spider-media-player"
cp -a "${SOURCE}/." "${ROOTFS}/opt/spider-media-player/"
chmod 0755 "${ROOTFS}/opt/spider-media-player/spider-media-player"
[[ -f "${ROOTFS}/opt/spider-media-player/chrome_crashpad_handler" ]] && chmod 0755 "${ROOTFS}/opt/spider-media-player/chrome_crashpad_handler"
[[ -f "${ROOTFS}/opt/spider-media-player/chrome-sandbox" ]] && chmod 4755 "${ROOTFS}/opt/spider-media-player/chrome-sandbox" || true

install -d "${ROOTFS}/etc/spider-os"
printf '%s\n' "${PROFILE}" > "${ROOTFS}/etc/spider-os/media-profile"
install -Dm755 "${REPO}/media/bin/spider-media-player" "${ROOTFS}/usr/local/bin/spider-media-player"
install -Dm644 "${REPO}/distro/config/applications/spider-media-player.desktop" "${ROOTFS}/usr/share/applications/spider-media-player.desktop"

if [[ "${PROFILE}" == "personal" ]]; then
  install -d "${ROOTFS}/usr/local/lib/spider-os/media/ai-dj"
  install -Dm755 "${REPO}/media/ai-dj/service.py" "${ROOTFS}/usr/local/lib/spider-os/media/ai-dj/service.py"
  install -Dm644 "${REPO}/media/ai-dj/spider-ai-dj.service" "${ROOTFS}/usr/lib/systemd/user/spider-ai-dj.service"
  install -d "${ROOTFS}/etc/systemd/user/default.target.wants"
  ln -sfn /usr/lib/systemd/user/spider-ai-dj.service "${ROOTFS}/etc/systemd/user/default.target.wants/spider-ai-dj.service"
else
  rm -rf "${ROOTFS}/usr/local/lib/spider-os/media/ai-dj"
  rm -f "${ROOTFS}/usr/lib/systemd/user/spider-ai-dj.service"
  rm -f "${ROOTFS}/etc/systemd/user/default.target.wants/spider-ai-dj.service"
fi

echo "Spider Media Player ${PROFILE} profile installed."
SH2

cat > distro/build-personal.sh <<'SH2'
#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
export SPM_PROFILE=personal
exec "${ROOT}/distro/build-iso.sh"
SH2

cat > the-web/shell/main.py <<'PY'
#!/usr/bin/env python3
import os, subprocess, sys
from pathlib import Path
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QBrush, QFont, QPalette, QPixmap
from PyQt5.QtWidgets import QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

SPIDER_ROOT = Path('/usr/local/lib/spider-os')
if not SPIDER_ROOT.exists():
    SPIDER_ROOT = Path(__file__).resolve().parents[2]
WALLPAPER = SPIDER_ROOT / 'branding' / 'wallpapers' / 'spider-os-wallpaper.png'

class TheWeb(QMainWindow):
    def __init__(self):
        super().__init__()
        self.wallpaper = None
        self.setWindowTitle('The Web | Spider OS')
        self.resize(1280, 820)
        self.setMinimumSize(1000, 650)
        self.build_ui()
        self.load_wallpaper()
        self.set_workspace('default')
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(5000)
        self.refresh_status()

    def build_ui(self):
        self.setStyleSheet('''
            QWidget#root { background: rgba(8,6,11,235); color:#f5eff8; }
            QLabel { color:#f5eff8; }
            QPushButton { background:rgba(70,25,105,225); border:1px solid #7e22ce; border-radius:9px; padding:11px; color:white; font-weight:bold; text-align:left; }
            QPushButton:hover { background:#6b21a8; border-color:#c084fc; }
            QFrame#card { background:rgba(18,13,24,225); border:1px solid #3c2946; border-radius:12px; }
        ''')
        root = QWidget(); root.setObjectName('root'); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(28,24,28,24)
        title = QLabel('SPIDER OS'); title.setFont(QFont('Sans Serif', 34, QFont.Bold)); title.setStyleSheet('color:#c084fc;')
        outer.addWidget(title)
        tagline = QLabel('YOUR LIFE. ONE WEB.'); tagline.setStyleSheet('color:#a99caf; font-size:14px; font-weight:bold;'); outer.addWidget(tagline)
        body = QHBoxLayout(); outer.addLayout(body, 1)
        side = QVBoxLayout(); body.addLayout(side)
        for label, fn in [
            ('WEBBIE', self.open_webbie), ('FORAGE', self.open_forage), ('DEEP FORAGE', self.open_deep_forage),
            ('KALI BAY', self.open_kali), ('MEDIA', self.open_media), ('STUDY', self.open_study),
            ('TERMINAL', self.open_terminal), ('SYSTEM SETTINGS', self.open_settings),
        ]:
            b=QPushButton(label); b.setMinimumWidth(190); b.clicked.connect(fn); side.addWidget(b)
        side.addStretch(1)
        center = QVBoxLayout(); body.addLayout(center, 1)
        heading = QLabel('THE WEB'); heading.setFont(QFont('Sans Serif', 26, QFont.Bold)); heading.setStyleSheet('color:#e9d5ff;'); center.addWidget(heading)
        intro = QLabel('Native Spider OS home · Webbie · research · security · media · study'); intro.setStyleSheet('color:#b2a5ba;'); center.addWidget(intro)
        grid = QGridLayout(); center.addLayout(grid, 1)
        cards = [
            ('Webbie','Resident voice AI','Talk, launch, organize, assist',self.open_webbie),
            ('Forage','Search & discovery','Local knowledge + web search',self.open_forage),
            ('Deep Forage','Research','Multi-source research and synthesis',self.open_deep_forage),
            ('Kali Bay','Security workspace','Isolated full Kali environment',self.open_kali),
            ('Media','Spider Media Player 7.5 Kabel','Personal AI DJ build',self.open_media),
            ('Study','Education workspace','Courses, assignments, notes, research',self.open_study),
        ]
        for i,(name,sub,desc,fn) in enumerate(cards):
            frame=QFrame(); frame.setObjectName('card'); lay=QVBoxLayout(frame)
            n=QLabel(name); n.setStyleSheet('font-size:20px;font-weight:bold;color:#d8b4fe;'); lay.addWidget(n)
            s=QLabel(sub); s.setStyleSheet('font-weight:bold;color:#bca9c8;'); lay.addWidget(s)
            d=QLabel(desc); d.setWordWrap(True); d.setStyleSheet('color:#96899f;'); lay.addWidget(d); lay.addStretch(1)
            o=QPushButton('OPEN'); o.clicked.connect(fn); lay.addWidget(o)
            grid.addWidget(frame, i//2, i%2)
        self.service_status = QLabel(); self.service_status.setStyleSheet('color:#978b9f; padding-top:8px;'); center.addWidget(self.service_status)
        self.status = QLabel('Spider OS ready.'); self.status.setStyleSheet('color:#c7b9d1; padding-top:5px;'); outer.addWidget(self.status)

    def load_wallpaper(self):
        if WALLPAPER.exists(): self.wallpaper=QPixmap(str(WALLPAPER)); self.apply_wallpaper()
    def apply_wallpaper(self):
        if self.wallpaper is None or self.wallpaper.isNull(): return
        p=QPalette(self.palette()); p.setBrush(QPalette.Window,QBrush(self.wallpaper.scaled(self.size(),Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation))); self.setPalette(p); self.setAutoFillBackground(True)
    def resizeEvent(self,e): self.apply_wallpaper(); super().resizeEvent(e)

    def set_workspace(self,name):
        runtime=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))/'spider-os'
        try: runtime.mkdir(parents=True,exist_ok=True); (runtime/'workspace').write_text(name,encoding='utf-8')
        except Exception: pass

    def launch(self,cmd,workspace='default',message='Opened.'):
        self.set_workspace(workspace)
        try: subprocess.Popen([str(x) for x in cmd],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True); self.status.setText(message)
        except Exception as e: self.status.setText(str(e))

    def open_webbie(self): self.launch(['python3',SPIDER_ROOT/'webbie/ui/webbie-ui.py'],'default','Webbie opened.')
    def open_forage(self): self.launch(['python3',SPIDER_ROOT/'forage/forage.py'],'forage','Forage opened.')
    def open_deep_forage(self): self.launch(['python3',SPIDER_ROOT/'forage/deep-forage/deep_forage.py'],'forage','Deep Forage opened.')
    def open_kali(self): self.launch([SPIDER_ROOT/'kali-bay/bin/kali-bay'],'kali-bay','Kali Bay opened.')
    def open_media(self): self.launch(['/usr/local/bin/spider-media-player'],'media','Spider Media Player opened.')
    def open_study(self): self.launch(['python3',SPIDER_ROOT/'study/study.py'],'study','Study opened.')
    def open_terminal(self): self.launch(['konsole'],'default','Terminal opened.')
    def open_settings(self): self.launch(['systemsettings'],'system','System Settings opened.')

    def is_active(self,cmd):
        try: return subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2).returncode == 0
        except Exception: return False
    def refresh_status(self):
        webbie=self.is_active(['systemctl','--user','is-active','--quiet','webbie.service'])
        core=self.is_active(['systemctl','is-active','--quiet','spider-os.service'])
        ollama=self.is_active(['systemctl','is-active','--quiet','ollama.service'])
        dj=self.is_active(['systemctl','--user','is-active','--quiet','spider-ai-dj.service'])
        self.service_status.setText(f"Webbie: {'ONLINE' if webbie else 'OFFLINE'}   ·   Core: {'ONLINE' if core else 'OFFLINE'}   ·   Local AI: {'ONLINE' if ollama else 'OFFLINE'}   ·   AI DJ: {'ONLINE' if dj else 'OFFLINE'}")


def main():
    app=QApplication(sys.argv); app.setApplicationName('The Web'); w=TheWeb(); w.showMaximized(); sys.exit(app.exec_())
if __name__=='__main__': main()
PY

python3 <<'PY'
from pathlib import Path
p=Path('distro/build-iso.sh')
s=p.read_text()
if 'SPM_PROFILE="${SPM_PROFILE:-public}"' not in s:
    anchor='set -Eeuo pipefail\n'
    if anchor not in s: raise SystemExit('ERROR: build-iso.sh set -Eeuo pipefail anchor missing')
    s=s.replace(anchor, anchor+'\n# Public builds never receive the private Kabel/AI-DJ bundle by accident.\nSPM_PROFILE="${SPM_PROFILE:-public}"\n',1)
call='''echo "Installing Spider Media Player profile: ${SPM_PROFILE}"\n"${ROOT}/distro/install-spm.sh" "${ROOTFS}" "${ROOT}" "${SPM_PROFILE}"\n\n'''
if 'distro/install-spm.sh" "${ROOTFS}"' not in s:
    marker='echo "Installing Spider OS desktop integration..."\n'
    if marker not in s: raise SystemExit('ERROR: desktop integration anchor missing in build-iso.sh')
    s=s.replace(marker,call+marker,1)
p.write_text(s)
print('build-iso.sh Media integration: OK')
PY

cat > distro/validate-feature-complete.sh <<'SH2'
#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
fail=0
ok(){ printf 'OK  %s\n' "$1"; }
bad(){ printf 'ERR %s\n' "$1"; fail=1; }
for f in \
  webbie/agent/webbie.py webbie/voice/whisper_listener.py webbie/brain/brain.py \
  forage/forage.py forage/engine.py forage/deep-forage/deep_forage.py \
  kali-bay/bin/kali-bay kali-bay/ui/kali_bay.py \
  study/study.py study/store.py \
  media/ai-dj/service.py media/bin/spider-media-player \
  the-web/shell/main.py distro/install-spm.sh distro/build-personal.sh; do
  [[ -f "$f" ]] && ok "$f" || bad "$f missing"
done
python3 -m py_compile webbie/agent/webbie.py webbie/voice/whisper_listener.py webbie/brain/brain.py forage/engine.py forage/forage.py forage/deep-forage/deep_forage.py kali-bay/ui/kali_bay.py study/store.py study/study.py media/ai-dj/service.py the-web/shell/main.py && ok 'Python syntax' || bad 'Python syntax'
for f in distro/build-iso.sh distro/install-spm.sh distro/build-personal.sh kali-bay/bin/kali-bay media/bin/spider-media-player; do bash -n "$f" || bad "$f syntax"; done
ok 'Shell syntax'
if grep -Rqi pocketsphinx webbie distro/packages/spider-os-packages.list; then bad 'PocketSphinx remains'; else ok 'Whisper replaced PocketSphinx'; fi
ASSET=''
for f in distro/assets/media/Spider-Media-Player-7.5.0-Kabel-Linux-x64.zip distro/assets/media/Spider-Media-Player-7.5.0-Kabel-Linux-x64-NORMALIZED.zip; do [[ -f "$f" ]] && ASSET="$f" && break; done
if [[ -n "$ASSET" ]]; then
  python3 - "$ASSET" <<'PY'
import sys,zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    names={n.replace('\\','/') for n in z.namelist()}
    assert 'linux-unpacked/spider-media-player' in names
    assert 'linux-unpacked/resources/app.asar' in names
print('OK  Spider Media Player 7.5 Kabel package')
PY
else
  bad 'Personal Kabel ZIP missing from distro/assets/media'
fi
[[ $fail -eq 0 ]] || exit 1
echo '========================================'
echo ' SPIDER OS FEATURE VALIDATION: PASSED'
echo '========================================'
SH2

chmod 755 media/ai-dj/service.py media/bin/spider-media-player distro/install-spm.sh distro/build-personal.sh distro/validate-feature-complete.sh the-web/shell/main.py
chmod 644 media/ai-dj/spider-ai-dj.service distro/config/applications/spider-media-player.desktop

grep -qxF 'distro/assets/media/*.zip' .gitignore || echo 'distro/assets/media/*.zip' >> .gitignore
grep -qxF '__pycache__/' .gitignore || echo '__pycache__/' >> .gitignore
grep -qxF '*.pyc' .gitignore || echo '*.pyc' >> .gitignore
find webbie forage kali-bay study media the-web -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

./distro/validate-feature-complete.sh

echo
echo '=== STAGING SOURCE (PERSONAL ZIP STAYS LOCAL/GITIGNORED) ==='
git add -A
git status --short

echo
echo '=== COMMIT ==='
git commit -m 'Complete Spider OS feature integration' || true

echo
echo '=== PUSH FEATURE BRANCH ==='
git push -u origin HEAD

echo
echo '========================================'
echo ' SPIDER OS SOURCE: FEATURE COMPLETE'
echo ' Personal build command:'
echo '   sudo -E ./distro/build-personal.sh'
echo '========================================'
