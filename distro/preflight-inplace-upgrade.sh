#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${EUID}" -eq 0 ]]; then
  echo "Run this script as your normal Spider OS user, not with sudo."
  echo "The script will ask for sudo only when it needs privileged reads."
  exit 1
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${HOME}/SpiderOS-Upgrade-Preflight-${STAMP}"
mkdir -p "${OUT}"

log() {
  printf '\n===== %s =====\n' "$1" | tee -a "${OUT}/SUMMARY.txt"
}

run_capture() {
  local name="$1"
  shift
  {
    echo "$ $*"
    "$@"
  } >"${OUT}/${name}.txt" 2>&1 || true
}

log "Spider OS in-place upgrade preflight"
echo "Output: ${OUT}" | tee -a "${OUT}/SUMMARY.txt"

run_capture os-release cat /etc/os-release
run_capture lsb-release lsb_release -a
run_capture kernel uname -a
run_capture hostname hostnamectl
run_capture uptime uptime
run_capture disk-layout lsblk -e7 -o NAME,PATH,SIZE,FSTYPE,FSVER,LABEL,UUID,FSAVAIL,FSUSE%,MOUNTPOINTS
run_capture mounts findmnt -R /
run_capture filesystems df -hT
run_capture inodes df -ih
run_capture block-ids sudo blkid
run_capture crypttab sudo cat /etc/crypttab
run_capture fstab sudo cat /etc/fstab
run_capture grub-version grub-install --version
run_capture grub-probe sudo grub-probe /
run_capture cmdline cat /proc/cmdline
run_capture failed-units systemctl --failed --no-pager
run_capture spider-core systemctl status spider-os.service --no-pager
run_capture webbie-user systemctl --user status webbie.service --no-pager
run_capture ollama systemctl status ollama.service --no-pager
run_capture the-web-process pgrep -a -f 'the-web|main.py'
run_capture package-holds apt-mark showhold
run_capture dpkg-audit sudo dpkg --audit
run_capture apt-simulated-upgrade sudo apt-get -s dist-upgrade
run_capture release-upgrades sudo cat /etc/update-manager/release-upgrades
run_capture apt-sources bash -lc "grep -RhsEv '^[[:space:]]*(#|$)' /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null || true"
run_capture recent-errors journalctl -b -p err..alert --no-pager
run_capture last-boot journalctl -b --no-pager -n 250

if [[ -d /sys/firmware/efi ]]; then
  echo "UEFI" > "${OUT}/boot-mode.txt"
  run_capture efi-entries sudo efibootmgr -v
else
  echo "LEGACY_BIOS" > "${OUT}/boot-mode.txt"
fi

log "Backing up critical configuration"
CFGDIR="${OUT}/critical-config"
mkdir -p "${CFGDIR}"
sudo tar -C / -czf "${CFGDIR}/etc-spider-critical.tar.gz" \
  etc/fstab \
  etc/crypttab \
  etc/default/grub \
  etc/default/grub.d \
  etc/update-manager/release-upgrades \
  etc/apt/sources.list \
  etc/apt/sources.list.d \
  etc/systemd/system \
  etc/systemd/user \
  etc/NetworkManager \
  2>"${CFGDIR}/backup-warnings.txt" || true
sudo chown -R "$(id -u):$(id -g)" "${CFGDIR}"

ROOT_AVAIL_KB="$(df --output=avail -k / | tail -n1 | tr -d ' ')"
ROOT_AVAIL_GB="$(( ROOT_AVAIL_KB / 1024 / 1024 ))"

{
  echo
  echo "Boot mode: $(cat "${OUT}/boot-mode.txt")"
  echo "Free space on /: ${ROOT_AVAIL_GB} GiB"
  if (( ROOT_AVAIL_GB < 20 )); then
    echo "WARNING: Less than 20 GiB free on /. Do NOT begin the release upgrade yet."
  else
    echo "Root free-space preflight: PASS"
  fi
  echo
  echo "Preflight finished."
  echo "Do NOT run do-release-upgrade yet."
  echo "Review this report first: ${OUT}"
} | tee -a "${OUT}/SUMMARY.txt"

printf '\nPRELIGHT_DIR=%q\n' "${OUT}"
