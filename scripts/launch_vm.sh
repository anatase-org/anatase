#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

VM_MEMORY=${VM_MEMORY:-4096}
VM_CPUS=${VM_CPUS:-4}
VM_SSH_PORT=${VM_SSH_PORT:-2222}
QEMU_BIN=${QEMU_BIN:-qemu-system-x86_64}
QEMU_DISPLAY=${QEMU_DISPLAY:-gtk}
QEMU_VGA=${QEMU_VGA:-virtio}

cache_dir="${repo_root}/cache"
vm_dir="${cache_dir}/vm"
disk="${vm_dir}/anatase.raw"

log() {
    printf '==> %s\n' "$*"
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        printf 'Required command not found: %s\n' "$1" >&2
        exit 1
    fi
}

require_command "${QEMU_BIN}"

if [[ ! -e "${disk}" ]]; then
    printf 'VM disk not found: %s\n' "${disk}" >&2
    printf 'Run scripts/deploy_vm.sh first to create it.\n' >&2
    exit 1
fi

log "Launching ${disk} with ${QEMU_BIN}"
exec "${QEMU_BIN}" \
    -enable-kvm \
    -cpu host \
    -m "${VM_MEMORY}" \
    -smp "${VM_CPUS}" \
    -drive "file=${disk},format=raw,if=virtio" \
    -netdev "user,id=net0,hostfwd=tcp::${VM_SSH_PORT}-:22" \
    -device virtio-net-pci,netdev=net0 \
    -vga "${QEMU_VGA}" \
    -display "${QEMU_DISPLAY}" \
    -serial mon:stdio
