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
