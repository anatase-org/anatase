#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

if [[ $# -lt 1 ]]; then
    printf 'usage: %s <host> [ludos build args...]\n' "${0##*/}" >&2
    exit 2
fi

DEVICE_HOST=$1
shift

MANIFEST=${MANIFEST:-anatase.yml}
manifest_image=${MANIFEST##*/}
manifest_image=${manifest_image%.yml}
manifest_image=${manifest_image%.yaml}
IMAGE=${IMAGE:-localhost/images:${manifest_image}}
OSTREE_REF=${OSTREE_REF:-master}
DEVICE_OSTREE_DIR=${DEVICE_OSTREE_DIR:-ostree-update}

cache_dir="${repo_root}/cache"
ostree_dir="${cache_dir}/ostree"

if [[ -x "${repo_root}/venv/bin/ludos" ]]; then
    ludos=("${repo_root}/venv/bin/ludos")
else
    ludos=(ludos)
fi

log() {
    printf '==> %s\n' "$*"
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        printf 'Required command not found: %s\n' "$1" >&2
        exit 1
    fi
}

shell_quote() {
    printf '%q' "$1"
}

require_command ostree
require_command rsync

log "Building ${MANIFEST}"
"${ludos[@]}" build "${MANIFEST}" "$@"

mkdir -p "${ostree_dir}"

log "Importing ${IMAGE} into ${ostree_dir}"
"${ludos[@]}" bootc ostree-import "${IMAGE}" --ostree-ref "${OSTREE_REF}"

log "Preparing ${DEVICE_HOST}:${DEVICE_OSTREE_DIR}"
remote_ostree_path=$(ssh "${DEVICE_HOST}" bash -s -- "${DEVICE_OSTREE_DIR}" <<'EOF'
set -euo pipefail

device_ostree_dir=$1

mkdir -p -- "${device_ostree_dir}"
cd -- "${device_ostree_dir}"
pwd -P
EOF
)

log "Syncing ${ostree_dir} to ${DEVICE_HOST}:${remote_ostree_path}"
remote_rsync_path=$(shell_quote "${remote_ostree_path}/")
rsync -aX --delete "${ostree_dir}/" "${DEVICE_HOST}:${remote_rsync_path}"

remote_ostree_dir=$(shell_quote "${remote_ostree_path}")
remote_ref=$(shell_quote "${OSTREE_REF}")
remote_script="set -euo pipefail; sudo ostree pull-local --repo=/sysroot/ostree/repo ${remote_ostree_dir} ${remote_ref}; sudo ostree admin deploy ${remote_ref}; sudo ostree admin prepare-soft-reboot 0 --reboot || sudo reboot"
log "Deploying ${OSTREE_REF} on ${DEVICE_HOST}"
ssh "${DEVICE_HOST}" "bash -c $(shell_quote "${remote_script}")"
