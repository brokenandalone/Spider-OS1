#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
export SPM_PROFILE=personal
exec "${ROOT}/distro/build-iso.sh"
