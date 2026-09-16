#!/usr/bin/env bash

set -Eeuo pipefail

# Public builds never receive the private Kabel/AI-DJ bundle by accident.
SPM_PROFILE="${SPM_PROFILE:-public}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="${ROOT}/build"

BASE_VERSION="24.04.5"
BASE_NAME="ubuntustudio-${BASE_VERSION}-dvd-amd64.iso"
BASE_URL="https://cdimage.ubuntu.com/ubuntustudio/releases/24.04/release/${BASE_NAME}"
SUMS_URL="https://cdimage.ubuntu.com/ubuntustudio/releases/24.04/release/SHA256SUMS"

BASE_ISO="${BUILD}/${BASE_NAME}"
ISO_MOUNT="${BUILD}/iso-mount"
ISO_TREE="${BUILD}/iso-tree"
ROOTFS="${BUILD}/rootfs"
LIVE_ROOTFS="${BUILD}/live-rootfs"

OUTPUT="${BUILD}/Spider_OS_${BASE_VERSION}_amd64.iso"

cleanup() {
    set +e

    mountpoint -q "${ROOTFS}/dev"  && umount -R -l "${ROOTFS}/dev"
    mountpoint -q "${ROOTFS}/proc" && umount -l "${ROOTFS}/proc"
    mountpoint -q "${ROOTFS}/sys"  && umount -l "${ROOTFS}/sys"
    mountpoint -q "${ROOTFS}/run"  && umount -R -l "${ROOTFS}/run"
    mountpoint -q "${ISO_MOUNT}"   && umount -l "${ISO_MOUNT}"
}

trap cleanup EXIT

if [[ "${EUID}" -ne 0 ]]; then
    echo "Run this script with sudo."
    exit 1
fi

mkdir -p \
    "${BUILD}" \
    "${ISO_MOUNT}" \
    "${ISO_TREE}"

echo "=================================================="
echo " Spider OS Native ISO Builder"
echo " Base: Ubuntu Studio ${BASE_VERSION}"
echo "=================================================="

if [[ ! -f "${BASE_ISO}" ]]; then
    echo "Downloading official Ubuntu Studio base..."
    curl -fL \
        --retry 5 \
        --retry-delay 5 \
        -o "${BASE_ISO}" \
        "${BASE_URL}"
fi

echo "Verifying upstream ISO..."

curl -fsSL "${SUMS_URL}" -o "${BUILD}/SHA256SUMS.upstream"

(
    cd "${BUILD}"
    grep -F -- "*${BASE_NAME}" SHA256SUMS.upstream > SHA256SUMS.verify
    sha256sum -c SHA256SUMS.verify
)

echo "Mounting base ISO..."

mount -o loop,ro "${BASE_ISO}" "${ISO_MOUNT}"

echo "Copying ISO filesystem..."

rm -rf "${ISO_TREE}"
mkdir -p "${ISO_TREE}"

rsync -aH \
    --exclude="/casper/standard.squashfs" \
    --exclude="/casper/standard.live.squashfs" \
    "${ISO_MOUNT}/" \
    "${ISO_TREE}/"

echo "Extracting layered Ubuntu Studio filesystem..."

rm -rf "${ROOTFS}"

STANDARD_LAYER="${ISO_MOUNT}/casper/standard.squashfs"
LIVE_LAYER="${ISO_MOUNT}/casper/standard.live.squashfs"

if [[ ! -f "${STANDARD_LAYER}" ]]; then
    echo "ERROR: Missing Ubuntu Studio install layer: ${STANDARD_LAYER}"
    ls -lah "${ISO_MOUNT}/casper/"
    exit 1
fi

if [[ ! -f "${LIVE_LAYER}" ]]; then
    echo "ERROR: Missing Ubuntu Studio live-session layer: ${LIVE_LAYER}"
    ls -lah "${ISO_MOUNT}/casper/"
    exit 1
fi

echo "Extracting Ubuntu Studio installed-system layer..."

unsquashfs \
    -d "${ROOTFS}" \
    "${STANDARD_LAYER}"

echo "Extracting Ubuntu Studio live-session layer..."

rm -rf "${LIVE_ROOTFS}"

unsquashfs \
    -d "${LIVE_ROOTFS}" \
    "${LIVE_LAYER}"

umount "${ISO_MOUNT}"

echo "Installing Spider OS files..."

install -d "${ROOTFS}/usr/local/lib/spider-os"

rsync -a \
    "${ROOT}/spider-core/" \
    "${ROOTFS}/usr/local/lib/spider-os/spider-core/"

rsync -a \
    "${ROOT}/webbie/" \
    "${ROOTFS}/usr/local/lib/spider-os/webbie/"

rsync -a \
    "${ROOT}/forage/" \
    "${ROOTFS}/usr/local/lib/spider-os/forage/"

rsync -a \
    "${ROOT}/the-web/" \
    "${ROOTFS}/usr/local/lib/spider-os/the-web/"

rsync -a \
    "${ROOT}/kali-bay/" \
    "${ROOTFS}/usr/local/lib/spider-os/kali-bay/"

install -d "${ROOTFS}/usr/local/lib/spider-os/branding"

if [[ -d "${ROOT}/branding" ]]; then
    rsync -a \
        "${ROOT}/branding/" \
        "${ROOTFS}/usr/local/lib/spider-os/branding/"
fi

echo "Installing Spider Study workspace..."

install -d \
    "${ROOTFS}/usr/local/lib/spider-os/study"

rsync -a --delete \
    "${ROOT}/study/" \
    "${ROOTFS}/usr/local/lib/spider-os/study/"

chmod +x \
    "${ROOTFS}/usr/local/lib/spider-os/study/bin/study" \
    "${ROOTFS}/usr/local/lib/spider-os/study/study.py"

install -Dm644 \
    "${ROOT}/distro/systemd/spider-os.service" \
    "${ROOTFS}/usr/lib/systemd/system/spider-os.service"

install -Dm644 \
    "${ROOT}/webbie/service/webbie.service" \
    "${ROOTFS}/usr/lib/systemd/user/webbie.service"

install -Dm644 \
    "${ROOT}/distro/systemd/ollama.service" \
    "${ROOTFS}/usr/lib/systemd/system/ollama.service"

install -Dm644 \
    "${ROOT}/distro/packages/spider-os-packages.list" \
    "${ROOTFS}/tmp/spider-os-packages.list"

cat > "${ROOTFS}/etc/spider-os-release" <<RELEASE
NAME="Spider OS"
VERSION="0.1 Development"
ID="spider-os"
ID_LIKE="ubuntu debian"
UBUNTU_BASE="${BASE_VERSION}"
DESKTOP="KDE Plasma"
SHELL="The Web"
RESIDENT_AI="Webbie"
SEARCH="Forage"
SECURITY_WORKSPACE="Kali Bay"
TAGLINE="YOUR LIFE. ONE WEB."
RELEASE

echo "Preparing chroot..."

mount --rbind /dev "${ROOTFS}/dev"
mount --make-rslave "${ROOTFS}/dev"

mount -t proc proc "${ROOTFS}/proc"
mount -t sysfs sys "${ROOTFS}/sys"

mount --rbind /run "${ROOTFS}/run"
mount --make-rslave "${ROOTFS}/run"

# /run is bind-mounted, so the chroot already has resolver access.

echo "Installing Spider OS dependencies..."

chroot "${ROOTFS}" /bin/bash <<'CHROOT'
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

if [[ -f /etc/apt/sources.list.d/dvd.list ]]; then
    mv \
        /etc/apt/sources.list.d/dvd.list \
        /etc/apt/sources.list.d/dvd.list.spider-disabled
fi

apt-get update

grep -vE '^[[:space:]]*(#|$)' \
    /tmp/spider-os-packages.list \
    > /tmp/spider-packages.clean

xargs -r apt-get install -y < /tmp/spider-packages.clean

echo "Installing whisper.cpp for Webbie..."

rm -rf /tmp/whisper.cpp

WHISPER_REPO="$(
    printf '%s%s'         'https://github.com/'         'ggml-org/whisper.cpp.git'
)"

git clone     --depth 1     "${WHISPER_REPO}"     /tmp/whisper.cpp

cmake     -S /tmp/whisper.cpp     -B /tmp/whisper.cpp/build     -DCMAKE_BUILD_TYPE=Release

cmake     --build /tmp/whisper.cpp/build     --config Release     -j"$(nproc)"

install     -Dm755     /tmp/whisper.cpp/build/bin/whisper-cli     /usr/local/bin/whisper-cli

install     -d     -m755     /usr/local/share/spider-os/whisper

bash     /tmp/whisper.cpp/models/download-ggml-model.sh base.en     /usr/local/share/spider-os/whisper

test     -x /usr/local/bin/whisper-cli

test     -f /usr/local/share/spider-os/whisper/ggml-base.en.bin

echo "Webbie whisper.cpp engine installed."

rm -rf /tmp/whisper.cpp

echo "Installing Webbie neural voice runtime..."

python3 -m venv /opt/spider-webbie

/opt/spider-webbie/bin/pip install \
    --no-cache-dir \
    --upgrade \
    pip

/opt/spider-webbie/bin/pip install \
    --no-cache-dir \
    edge-tts

echo "Installing Forage search runtime..."

python3 -m venv /opt/spider-forage

/opt/spider-forage/bin/pip install \
    --no-cache-dir \
    --upgrade \
    pip

/opt/spider-forage/bin/pip install \
    --no-cache-dir \
    "ddgs==9.16.0"

echo "Installing Ollama local AI runtime..."

rm -rf /usr/lib/ollama

curl -fsSL \
    https://ollama.com/download/ollama-linux-amd64.tar.zst \
    | tar --zstd -x -C /usr

if ! id ollama >/dev/null 2>&1; then
    useradd \
        --system \
        --user-group \
        --create-home \
        --home-dir /usr/share/ollama \
        --shell /usr/sbin/nologin \
        ollama
fi

install -d \
    -o ollama \
    -g ollama \
    -m 0755 \
    /usr/share/ollama/.ollama/models

echo "Bundling Webbie local AI model..."

su \
    -s /bin/bash \
    ollama \
    -c 'HOME=/usr/share/ollama OLLAMA_MODELS=/usr/share/ollama/.ollama/models nohup /usr/bin/ollama serve >/tmp/spider-ollama-build.log 2>&1 & echo $! >/tmp/spider-ollama.pid'

for attempt in $(seq 1 30); do
    if curl -fsS \
        http://127.0.0.1:11434/api/tags \
        >/dev/null 2>&1
    then
        break
    fi

    sleep 1
done

if ! curl -fsS \
    http://127.0.0.1:11434/api/tags \
    >/dev/null 2>&1
then
    echo "Ollama failed to start during image build."
    cat /tmp/spider-ollama-build.log || true
    exit 1
fi

su \
    -s /bin/bash \
    ollama \
    -c 'HOME=/usr/share/ollama OLLAMA_MODELS=/usr/share/ollama/.ollama/models /usr/bin/ollama pull qwen3:1.7b'

if [[ -f /tmp/spider-ollama.pid ]]; then
    kill "$(cat /tmp/spider-ollama.pid)" 2>/dev/null || true
fi

rm -f \
    /tmp/spider-ollama.pid \
    /tmp/spider-ollama-build.log

chmod +x \
    /usr/local/lib/spider-os/spider-core/bin/spider-core \
    /usr/local/lib/spider-os/webbie/webbie \
    /usr/local/lib/spider-os/webbie/agent/webbie.py

apt-get clean

rm -rf \
    /var/lib/apt/lists/* \
    /tmp/spider-os-packages.list \
    /tmp/spider-packages.clean
CHROOT

cleanup

echo "Enabling Spider OS services..."

systemctl \
    --root="${ROOTFS}" \
    enable spider-os.service

systemctl \
    --root="${ROOTFS}" \
    enable ollama.service

systemctl \
    --root="${ROOTFS}" \
    --global \
    enable webbie.service

echo "Updating Spider OS filesystem metadata..."

chroot "${ROOTFS}" \
    dpkg-query \
    -W \
    --showformat='${Package} ${Version}\n' \
    > "${ISO_TREE}/casper/standard.manifest"

# Keep the overall manifest synchronized with the installed-system layer.
cp \
    "${ISO_TREE}/casper/standard.manifest" \
    "${ISO_TREE}/casper/filesystem.manifest"

ROOTFS_SIZE="$(
    du -sx --block-size=1 "${ROOTFS}" |
    cut -f1
)"

printf '%s\n' "${ROOTFS_SIZE}" \
    > "${ISO_TREE}/casper/standard.size"

printf '%s\n' "${ROOTFS_SIZE}" \
    > "${ISO_TREE}/casper/filesystem.size"

echo "Creating Spider OS standard.squashfs..."

rm -f "${ISO_TREE}/casper/standard.squashfs"



SPIDER_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"


echo "Installing Spider OS system identity..."

cat > "${ROOTFS}/etc/os-release" <<'SPIDER_OS_RELEASE'
NAME="Spider OS"
PRETTY_NAME="Spider OS 0.1"
ID=ubuntu
ID_LIKE=debian
VERSION_ID="24.04"
VERSION="0.1 (Ubuntu 24.04 LTS base)"
VERSION_CODENAME=noble
UBUNTU_CODENAME=noble
HOME_URL="https://github.com/brokenandalone/Spider-OS1"
SUPPORT_URL="https://github.com/brokenandalone/Spider-OS1"
BUG_REPORT_URL="https://github.com/brokenandalone/Spider-OS1/issues"
SPIDER_OS_VERSION="0.1"
SPIDER_OS_BASE="Ubuntu Studio 24.04.5"
SPIDER_OS_SHELL="The Web"
SPIDER_OS_AI="Webbie"
SPIDER_OS_SEARCH="Forage"
SPIDER_OS_SECURITY="Kali Bay"
SPIDER_OS_TAGLINE="YOUR LIFE. ONE WEB."
SPIDER_OS_RELEASE

cp "${ROOTFS}/etc/os-release" \
   "${ROOTFS}/usr/lib/os-release"

cat > "${ROOTFS}/etc/issue" <<'SPIDER_ISSUE'
Spider OS 0.1 \n \l

SPIDER_ISSUE

cat > "${ROOTFS}/etc/issue.net" <<'SPIDER_ISSUE_NET'
Spider OS 0.1
SPIDER_ISSUE_NET

install -d "${ROOTFS}/etc/default/grub.d"

cat > "${ROOTFS}/etc/default/grub.d/99-spider-os.cfg" <<'SPIDER_GRUB'
GRUB_DISTRIBUTOR="Spider OS"
GRUB_BACKGROUND="/usr/share/backgrounds/spider-os-wallpaper.png"
SPIDER_GRUB

echo "Installing Spider OS visual branding..."

install -Dm644 \
  "${SPIDER_REPO_ROOT}/branding/wallpapers/spider-os-wallpaper.png" \
  "${ROOTFS}/usr/share/backgrounds/spider-os-wallpaper.png"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/branding/splash/spider-os-splash.png" \
  "${ROOTFS}/usr/share/spider-os/branding/spider-os-splash.png"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/branding/icons/spider-os-logo.png" \
  "${ROOTFS}/usr/share/pixmaps/spider-os-logo.png"

install -d "${ROOTFS}/usr/share/spider-os/workspaces"
cp -a \
  "${SPIDER_REPO_ROOT}/branding/workspaces/." \
  "${ROOTFS}/usr/share/spider-os/workspaces/"

install -Dm755 \
  "${SPIDER_REPO_ROOT}/distro/config/branding/apply-spider-branding.sh" \
  "${ROOTFS}/usr/local/lib/spider-os/branding/apply-spider-branding.sh"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/autostart/spider-branding.desktop" \
  "${ROOTFS}/etc/xdg/autostart/spider-branding.desktop"


echo "Installing Spider OS Plymouth theme..."

install -d \
  "${ROOTFS}/usr/share/plymouth/themes/spider-os" \
  "${ROOTFS}/etc/alternatives"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/plymouth/spider-os.plymouth" \
  "${ROOTFS}/usr/share/plymouth/themes/spider-os/spider-os.plymouth"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/plymouth/spider-os.script" \
  "${ROOTFS}/usr/share/plymouth/themes/spider-os/spider-os.script"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/branding/splash/spider-os-splash.png" \
  "${ROOTFS}/usr/share/plymouth/themes/spider-os/spider-os-splash.png"

ln -sfn \
  /usr/share/plymouth/themes/spider-os/spider-os.plymouth \
  "${ROOTFS}/etc/alternatives/default.plymouth"

ln -sfn \
  /etc/alternatives/default.plymouth \
  "${ROOTFS}/usr/share/plymouth/themes/default.plymouth"

# Spider OS login-screen branding.
install -d "${ROOTFS}/etc/sddm.conf.d"
cat > "${ROOTFS}/etc/sddm.conf.d/spider-os.conf" <<'SDDM'
[Theme]
Current=breeze
SDDM

install -d "${ROOTFS}/usr/share/sddm/themes/breeze"
cat > "${ROOTFS}/usr/share/sddm/themes/breeze/theme.conf.user" <<'SDDM_THEME'
[General]
background=/usr/share/backgrounds/spider-os-wallpaper.png
SDDM_THEME

echo "Installing Spider Media Player profile: ${SPM_PROFILE}"
"${ROOT}/distro/install-spm.sh" "${ROOTFS}" "${ROOT}" "${SPM_PROFILE}"

echo "Installing Spider OS desktop integration..."

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/installer/whitelabel.yaml" \
  "${ROOTFS}/usr/share/desktop-provision/whitelabel.yaml"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/autostart/the-web.desktop" \
  "${ROOTFS}/etc/xdg/autostart/the-web.desktop"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/autostart/the-web.desktop" \
  "${ROOTFS}/usr/share/applications/the-web.desktop"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/applications/webbie.desktop" \
  "${ROOTFS}/usr/share/applications/webbie.desktop"


install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/applications/study.desktop" \
  "${ROOTFS}/usr/share/applications/study.desktop"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/applications/forage.desktop" \
  "${ROOTFS}/usr/share/applications/forage.desktop"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/applications/deep-forage.desktop" \
  "${ROOTFS}/usr/share/applications/deep-forage.desktop"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/applications/kali-bay.desktop" \
  "${ROOTFS}/usr/share/applications/kali-bay.desktop"

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/autostart/the-web.desktop" \
  "${ROOTFS}/etc/skel/.config/autostart/the-web.desktop"

echo "Creating Spider OS live-session layer..."

echo "Installing Spider OS live payload..."

install -d "${LIVE_ROOTFS}/usr/local/lib/spider-os"

rsync -a \
    "${ROOT}/spider-core/" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/spider-core/"

rsync -a \
    "${ROOT}/webbie/" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/webbie/"

rsync -a \
    "${ROOT}/forage/" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/forage/"

rsync -a \
    "${ROOT}/the-web/" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/the-web/"

rsync -a \
    "${ROOT}/kali-bay/" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/kali-bay/"

chmod +x \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/spider-core/bin/spider-core" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/webbie/webbie" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/webbie/agent/webbie.py" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/the-web/shell/main.py"

# Spider Core service in live session.
install -Dm644 \
    "${ROOT}/distro/systemd/spider-os.service" \
    "${LIVE_ROOTFS}/etc/systemd/system/spider-os.service"

install -d \
    "${LIVE_ROOTFS}/etc/systemd/system/graphical.target.wants"

ln -sfn \
    /etc/systemd/system/spider-os.service \
    "${LIVE_ROOTFS}/etc/systemd/system/graphical.target.wants/spider-os.service"

# Webbie resident user service in live session.
echo "Installing Study into live Spider OS..."

install -d \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/study"

rsync -a --delete \
    "${ROOT}/study/" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/study/"

chmod +x \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/study/bin/study" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/study/study.py"

install -Dm644 \
    "${ROOT}/webbie/service/webbie.service" \
    "${LIVE_ROOTFS}/etc/systemd/user/webbie.service"

install -Dm644 \
    "${ROOT}/distro/systemd/ollama.service" \
    "${LIVE_ROOTFS}/usr/lib/systemd/system/ollama.service"

install -d \
    "${LIVE_ROOTFS}/etc/systemd/user/default.target.wants"

ln -sfn \
    /etc/systemd/user/webbie.service \
    "${LIVE_ROOTFS}/etc/systemd/user/default.target.wants/webbie.service"

echo "Neutralizing inherited Ubuntu Studio live Plasma layout..."

# This inherited Ubuntu Studio live look-and-feel is crashing
# plasmashell with:
#   ReferenceError: plasma is not defined
rm -rf \
    "${LIVE_ROOTFS}/usr/share/plasma/look-and-feel/org.ubuntustudio-live.desktop"

# Replace any live-session defaults/scripts still requesting the
# broken Ubuntu Studio live look-and-feel with KDE Breeze.
for cfgroot in \
    "${LIVE_ROOTFS}/etc/xdg" \
    "${LIVE_ROOTFS}/etc/skel" \
    "${LIVE_ROOTFS}/usr/share/xsessions" \
    "${LIVE_ROOTFS}/usr/share/plasma" \
    "${LIVE_ROOTFS}/usr/share/ubuntustudio"
do
    [[ -d "${cfgroot}" ]] || continue

    while IFS= read -r cfg; do
        sed -i \
            's/org\.ubuntustudio-live\.desktop/org.kde.breeze.desktop/g' \
            "${cfg}"
    done < <(
        grep -Ilr \
            'org\.ubuntustudio-live\.desktop' \
            "${cfgroot}" \
            2>/dev/null || true
    )
done

# The log showed plasmashell starting before kactivitymanagerd
# was ready. Make the user service ordering explicit.
install -d \
    "${LIVE_ROOTFS}/etc/systemd/user/plasma-plasmashell.service.d"

cat > \
    "${LIVE_ROOTFS}/etc/systemd/user/plasma-plasmashell.service.d/10-spider-kactivity.conf" \
    <<'SPIDER_KACTIVITY'
[Unit]
Wants=plasma-kactivitymanagerd.service
After=plasma-kactivitymanagerd.service
SPIDER_KACTIVITY

# The Web remains native and automatic, but let Plasma finish
# initializing before the Qt command center appears.
if [[ -f "${LIVE_ROOTFS}/etc/xdg/autostart/the-web.desktop" ]]; then
    sed -i \
        "s|^Exec=.*|Exec=sh -c 'sleep 10; exec python3 /usr/local/lib/spider-os/the-web/shell/main.py'|" \
        "${LIVE_ROOTFS}/etc/xdg/autostart/the-web.desktop"
fi

# Refuse to build if a live-user configuration still explicitly
# selects the crashing Ubuntu Studio live look-and-feel.
STALE_LIVE_REFS="$(
    grep -Ilr \
        'org\.ubuntustudio-live\.desktop' \
        "${LIVE_ROOTFS}/etc/xdg" \
        "${LIVE_ROOTFS}/etc/skel" \
        2>/dev/null || true
)"

if [[ -n "${STALE_LIVE_REFS}" ]]; then
    echo "ERROR: Stale Ubuntu Studio live Plasma references remain:"
    echo "${STALE_LIVE_REFS}"
    exit 1
fi

echo "Spider OS live Plasma safety fixes applied."

# Spider OS live-session visual identity.
install -Dm644 \
    "${ROOT}/branding/wallpapers/spider-os-wallpaper.png" \
    "${LIVE_ROOTFS}/usr/share/backgrounds/spider-os-wallpaper.png"

install -Dm644 \
    "${ROOT}/branding/icons/spider-os-logo.png" \
    "${LIVE_ROOTFS}/usr/share/pixmaps/spider-os-logo.png"

install -Dm644 \
    "${ROOT}/branding/splash/spider-os-splash.png" \
    "${LIVE_ROOTFS}/usr/share/spider-os/branding/spider-os-splash.png"

# Live desktop branding and The Web startup.
install -Dm755 \
    "${ROOT}/distro/config/branding/apply-spider-branding.sh" \
    "${LIVE_ROOTFS}/usr/local/lib/spider-os/branding/apply-spider-branding.sh"

install -Dm644 \
    "${ROOT}/distro/config/autostart/the-web.desktop" \
    "${LIVE_ROOTFS}/etc/xdg/autostart/the-web.desktop"

install -Dm644 \
    "${ROOT}/distro/config/applications/webbie.desktop" \
    "${LIVE_ROOTFS}/usr/share/applications/webbie.desktop"


install -Dm644 \
    "${ROOT}/distro/config/applications/study.desktop" \
    "${LIVE_ROOTFS}/usr/share/applications/study.desktop"

install -Dm644 \
    "${ROOT}/distro/config/applications/forage.desktop" \
    "${LIVE_ROOTFS}/usr/share/applications/forage.desktop"

install -Dm644 \
    "${ROOT}/distro/config/applications/deep-forage.desktop" \
    "${LIVE_ROOTFS}/usr/share/applications/deep-forage.desktop"

install -Dm644 \
    "${ROOT}/distro/config/applications/kali-bay.desktop" \
    "${LIVE_ROOTFS}/usr/share/applications/kali-bay.desktop"

# Spider OS live-session system identity.
install -d \
    "${LIVE_ROOTFS}/etc" \
    "${LIVE_ROOTFS}/usr/lib"

cat > "${LIVE_ROOTFS}/etc/os-release" <<'SPIDER_LIVE_RELEASE'
NAME="Spider OS"
PRETTY_NAME="Spider OS 0.1"
ID=ubuntu
ID_LIKE=debian
VERSION_ID="24.04"
VERSION="0.1 (Ubuntu 24.04 LTS base)"
VERSION_CODENAME=noble
UBUNTU_CODENAME=noble
SPIDER_OS_VERSION="0.1"
SPIDER_OS_BASE="Ubuntu Studio 24.04.5"
SPIDER_OS_SHELL="The Web"
SPIDER_OS_AI="Webbie"
SPIDER_OS_SEARCH="Forage"
SPIDER_OS_SECURITY="Kali Bay"
SPIDER_OS_TAGLINE="YOUR LIFE. ONE WEB."
SPIDER_LIVE_RELEASE

cp \
    "${LIVE_ROOTFS}/etc/os-release" \
    "${LIVE_ROOTFS}/usr/lib/os-release"

cat > "${LIVE_ROOTFS}/etc/issue" <<'SPIDER_LIVE_ISSUE'
Spider OS 0.1 Live \n \l
SPIDER_LIVE_ISSUE

# Provide an explicitly Spider-branded installer launcher.
install -d \
    "${LIVE_ROOTFS}/usr/share/applications" \
    "${LIVE_ROOTFS}/etc/skel/Desktop"

cat > "${LIVE_ROOTFS}/usr/share/applications/install-spider-os.desktop" <<'SPIDER_INSTALLER'
[Desktop Entry]
Type=Application
Name=Install Spider OS
Comment=Install Spider OS to this computer
Exec=/snap/bin/ubuntu-desktop-bootstrap --try-or-install
TryExec=/snap/bin/ubuntu-desktop-bootstrap
Icon=spider-os-logo
Terminal=false
Categories=System;
SPIDER_INSTALLER

cp \
    "${LIVE_ROOTFS}/usr/share/applications/install-spider-os.desktop" \
    "${LIVE_ROOTFS}/etc/skel/Desktop/Install Spider OS.desktop"

chmod 755 \
    "${LIVE_ROOTFS}/etc/skel/Desktop/Install Spider OS.desktop"

# Rename any existing Ubuntu installer launchers we can safely identify.
while IFS= read -r desktop_file; do
    sed -i \
        -e 's/Install Ubuntu Studio/Install Spider OS/g' \
        -e 's/Install Ubuntu 24\.04\.5 LTS/Install Spider OS/g' \
        -e 's/Install Ubuntu/Install Spider OS/g' \
        "${desktop_file}"
done < <(
    grep -Ilr \
        'ubuntu-desktop-bootstrap' \
        "${LIVE_ROOTFS}/usr/share/applications" \
        "${LIVE_ROOTFS}/etc/skel" \
        2>/dev/null || true
)

# Media identity.
if [[ -d "${ISO_TREE}/.disk" ]]; then
    printf '%s\n' \
        'Spider OS 0.1 - Ubuntu Studio 24.04.5 base' \
        > "${ISO_TREE}/.disk/info"
fi

# Rename visible GRUB menu references without touching binaries.
for grub_cfg in \
    "${ISO_TREE}/boot/grub/grub.cfg" \
    "${ISO_TREE}/boot/grub/loopback.cfg"
do
    if [[ -f "${grub_cfg}" ]]; then
        sed -i \
            -e 's/Ubuntu Studio/Spider OS/g' \
            -e 's/quiet splash/quiet plymouth.enable=0/g' \
            "${grub_cfg}"
    fi
done

install -Dm644 \
  "${SPIDER_REPO_ROOT}/distro/config/installer/whitelabel.yaml" \
  "${LIVE_ROOTFS}/usr/share/desktop-provision/whitelabel.yaml"

rm -f "${ISO_TREE}/casper/standard.live.squashfs"

mksquashfs \
    "${LIVE_ROOTFS}" \
    "${ISO_TREE}/casper/standard.live.squashfs" \
    -comp zstd \
    -noappend

if [[ -f "${ISO_TREE}/casper/standard.live.size" ]]; then
    du -sx --block-size=1 "${LIVE_ROOTFS}" \
        | cut -f1 \
        > "${ISO_TREE}/casper/standard.live.size"
fi

rm -rf "${LIVE_ROOTFS}"

mksquashfs \
    "${ROOTFS}" \
    "${ISO_TREE}/casper/standard.squashfs" \
    -comp zstd \
    -noappend

echo "Updating Casper SHA256 checksums..."

rm -f \
    "${ISO_TREE}/casper/SHA256SUMS" \
    "${ISO_TREE}/casper/SHA256SUMS.gpg"

(
    cd "${ISO_TREE}/casper"

    find . \
        -maxdepth 1 \
        -type f \
        ! -name SHA256SUMS \
        ! -name SHA256SUMS.gpg \
        -printf '%P\0' \
        | sort -z \
        | xargs -0 sha256sum \
        > SHA256SUMS
)

echo "Removing temporary uncompressed root filesystem..."

rm -rf "${ROOTFS}"

echo "Updating ISO checksums..."

(
    cd "${ISO_TREE}"

    find . \
        -type f \
        ! -name md5sum.txt \
        -print0 \
        | sort -z \
        | xargs -0 md5sum \
        > md5sum.txt
)

echo "Building bootable Spider OS ISO..."

rm -f "${OUTPUT}"

xorriso \
    -indev "${BASE_ISO}" \
    -outdev "${OUTPUT}" \
    -boot_image any replay \
    -volid "SPIDER_OS" \
    -map "${ISO_TREE}" / \
    -commit

echo "Verifying ISO boot metadata..."

xorriso \
    -indev "${OUTPUT}" \
    -report_el_torito plain

sha256sum "${OUTPUT}" \
    > "${OUTPUT}.sha256"

echo
echo "=================================================="
echo " Spider OS ISO complete"
echo
echo " ${OUTPUT}"
echo "=================================================="
