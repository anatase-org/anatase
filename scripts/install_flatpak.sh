#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

if [[ $# -ne 1 ]]; then
    printf 'usage: %s <flatpak-dir>\n' "${0##*/}" >&2
    exit 2
fi

flatpak_dir=$1
card="${flatpak_dir%/}/card.yaml"

MANIFEST=${MANIFEST:-anatase.yml}
VM_SSH=${VM_SSH:-vm}
REMOTE_DIR=${REMOTE_DIR:-/var/tmp/anatase-flatpaks}

if [[ -x "${repo_root}/venv/bin/ludos" ]]; then
    ludos=("${repo_root}/venv/bin/ludos")
else
    ludos=(ludos)
fi

log() {
    printf '==> %s\n' "$*"
}

if [[ ! -f "${card}" ]]; then
    printf 'Flatpak card not found: %s\n' "${card}" >&2
    exit 1
fi

app_id=$(python3 - "${card}" <<'PY'
import sys
import yaml

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}

try:
    print(data["flatpak"]["id"])
except Exception:
    raise SystemExit(f"{sys.argv[1]}: missing flatpak.id")
PY
)

latest_image="localhost/${app_id}:latest"

log "Building ${flatpak_dir}"
"${ludos[@]}" build "${MANIFEST}" --flatpak "${flatpak_dir}"

if ! podman image exists "${latest_image}"; then
    printf 'Expected image not found after build: %s\n' "${latest_image}" >&2
    exit 1
fi

branch=$(podman image inspect "${latest_image}" --format '{{ index .Config.Labels "org.anatase.flatpak.branch" }}')
branch=${branch:-latest}
archive_dir="${repo_root}/cache/flatpaks"
archive="${archive_dir}/${app_id}-${branch}.oci"
remote_archive="${REMOTE_DIR}/${app_id}-${branch}.oci"

mkdir -p "${archive_dir}"

log "Exporting ${latest_image} to ${archive}"
podman save --format oci-archive -o "${archive}" "${latest_image}"

log "Sending ${archive} to ${VM_SSH}:${remote_archive}"
ssh "${VM_SSH}" "mkdir -p '${REMOTE_DIR}'"
ssh "${VM_SSH}" "cat > '${remote_archive}'" < "${archive}"

log "Installing ${app_id} on ${VM_SSH}"
ssh "${VM_SSH}" "flatpak install --system -y --noninteractive --reinstall --no-deps --image 'oci-archive:${remote_archive}'"

log "Installed ${app_id} (${branch})"
