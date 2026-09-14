#!/usr/bin/env bash

set -Eeuo pipefail

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

OUTPUT="${BUILD}/Spider_OS_${BASE_VERSION}_amd64.iso"

cleanup() {
    set +e

    mountpoint -q "${ROOTFS}/dev"  && umount -l "${ROOTFS}/dev"
    mountpoint -q "${ROOTFS}/proc" && umount -l "${ROOTFS}/proc"
    mountpoint -q "${ROOTFS}/sys"  && umount -l "${ROOTFS}/sys"
    mountpoint -q "${ROOTFS}/run"  && umount -l "${ROOTFS}/run"
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
    "${ISO_MOUNT}/" \
    "${ISO_TREE}/"

echo "Extracting layered Ubuntu Studio filesystem..."

rm -rf "${ROOTFS}"

STANDARD_LAYER="${ISO_MOUNT}/casper/standard.squashfs"

if [[ ! -f "${STANDARD_LAYER}" ]]; then
    echo "ERROR: Missing Ubuntu Studio install layer: ${STANDARD_LAYER}"
    ls -lah "${ISO_MOUNT}/casper/"
    exit 1
fi

echo "Extracting Ubuntu Studio installed-system layer..."

unsquashfs \
    -d "${ROOTFS}" \
    "${STANDARD_LAYER}"

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

install -Dm644 \
    "${ROOT}/distro/systemd/spider-os.service" \
    "${ROOTFS}/etc/systemd/system/spider-os.service"

install -Dm644 \
    "${ROOT}/webbie/service/webbie.service" \
    "${ROOTFS}/etc/systemd/user/webbie.service"

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

mount --bind /dev "${ROOTFS}/dev"
mount -t proc proc "${ROOTFS}/proc"
mount -t sysfs sys "${ROOTFS}/sys"
mount --bind /run "${ROOTFS}/run"

# /run is bind-mounted, so the chroot already has resolver access.

echo "Installing Spider OS dependencies..."

chroot "${ROOTFS}" /bin/bash <<'CHROOT'
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update

grep -vE '^[[:space:]]*(#|$)' \
    /tmp/spider-os-packages.list \
    > /tmp/spider-packages.clean

xargs -r apt-get install -y < /tmp/spider-packages.clean

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
