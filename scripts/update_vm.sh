#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

MANIFEST=${MANIFEST:-anatase.yml}
manifest_image=${MANIFEST##*/}
manifest_image=${manifest_image%.yml}
manifest_image=${manifest_image%.yaml}
IMAGE=${IMAGE:-localhost/images:${manifest_image}}
OSTREE_REF=${OSTREE_REF:-master}
VM_SSH_HOST=${VM_SSH_HOST:-localhost}
VM_SSH_PORT=${VM_SSH_PORT:-2222}
VM_SSH_USER=${VM_SSH_USER:-root}
VM_SSH_KEY=${VM_SSH_KEY:-${HOME:-}/.ssh/id_rsa}
VM_OSTREE_MOUNT_TAG=${VM_OSTREE_MOUNT_TAG:-anatase-ostree}
VM_OSTREE_MOUNT_POINT=${VM_OSTREE_MOUNT_POINT:-/run/anatase/ostree}

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

ssh_args=(
    -p "${VM_SSH_PORT}"
    -o StrictHostKeyChecking=no
)

if [[ -n "${VM_SSH_KEY}" && -r "${VM_SSH_KEY}" ]]; then
    ssh_args+=(-i "${VM_SSH_KEY}")
fi

log "Building ${MANIFEST}"
"${ludos[@]}" build "${MANIFEST}" $@

mkdir -p "${ostree_dir}"

log "Importing ${IMAGE} into ${ostree_dir}"
"${ludos[@]}" bootc ostree-import "${IMAGE}" --ostree-ref "${OSTREE_REF}"

log "Updating VM from ${VM_OSTREE_MOUNT_POINT}:${OSTREE_REF}"
ssh "${ssh_args[@]}" "${VM_SSH_USER}@${VM_SSH_HOST}" \
    bash -s -- "${VM_OSTREE_MOUNT_POINT}" "${VM_OSTREE_MOUNT_TAG}" "${OSTREE_REF}" <<'EOF'
set -euo pipefail

ostree_mount_point=$1
ostree_mount_tag=$2
ostree_ref=$3

sudo mkdir -p "${ostree_mount_point}"
if ! mountpoint -q "${ostree_mount_point}"; then
    sudo mount -t 9p -o trans=virtio,version=9p2000.L,msize=104857600 "${ostree_mount_tag}" "${ostree_mount_point}"
fi

sudo ostree pull-local "${ostree_mount_point}" "${ostree_ref}"
sudo ostree admin deploy "${ostree_ref}"
sudo ostree admin prepare-soft-reboot 0 --reboot || sudo reboot
EOF
