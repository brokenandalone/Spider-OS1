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
