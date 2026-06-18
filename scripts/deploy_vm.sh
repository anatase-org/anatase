#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

IMAGE=${IMAGE:-localhost/anatase:f44-x86_64}
OSTREE_REF=${OSTREE_REF:-master}
DISK_SIZE=${DISK_SIZE:-40G}
VM_MEMORY=${VM_MEMORY:-4096}
VM_CPUS=${VM_CPUS:-4}
VM_SSH_PORT=${VM_SSH_PORT:-2222}
QEMU_BIN=${QEMU_BIN:-qemu-system-x86_64}
QEMU_DISPLAY=${QEMU_DISPLAY:-gtk}
QEMU_VGA=${QEMU_VGA:-virtio}
VM_KERNEL_ARGS=${VM_KERNEL_ARGS:-}

cache_dir="${repo_root}/cache"
vm_dir="${cache_dir}/vm"
ostree_dir="${cache_dir}/ostree"
disk="${vm_dir}/anatase.raw"

if [[ -x "${repo_root}/venv/bin/ludos" ]]; then
    ludos=("${repo_root}/venv/bin/ludos")
else
    ludos=(ludos)
fi

if [[ "${UID}" -eq 0 ]]; then
    rootful_podman=(podman)
else
    rootful_podman=(sudo podman)
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

append_vm_kernel_args() {
    if [[ -z "${VM_KERNEL_ARGS}" ]]; then
        return
    fi

    local loop=""
    local mount_dir=""
    trap 'set +e; if [[ -n "${mount_dir}" ]] && mountpoint -q "${mount_dir}"; then sudo umount "${mount_dir}"; fi; if [[ -n "${loop}" ]]; then sudo losetup -d "${loop}"; fi; if [[ -n "${mount_dir}" ]]; then rmdir "${mount_dir}" 2>/dev/null; fi; trap - RETURN' RETURN

    log "Adding VM kernel args: ${VM_KERNEL_ARGS}"
    loop=$(sudo losetup --find --show --partscan "${disk}")
    mount_dir=$(mktemp -d "${TMPDIR:-/tmp}/anatase-vm.XXXXXX")
    sudo mount "${loop}p3" "${mount_dir}"

    local entries=()
    shopt -s nullglob
    entries=("${mount_dir}"/boot/loader*/entries/*.conf)
    shopt -u nullglob

    if ((${#entries[@]} == 0)); then
        printf 'No bootloader entries found in %s\n' "${disk}" >&2
        return 1
    fi

    local entry tmp
    for entry in "${entries[@]}"; do
        tmp=$(mktemp)
        sudo awk -v args="${VM_KERNEL_ARGS}" '
            BEGIN { n = split(args, a, /[[:space:]]+/) }
            /^options[[:space:]]/ {
                padded = " " $0 " "
                for (i = 1; i <= n; i++) {
                    if (a[i] != "" && index(padded, " " a[i] " ") == 0) {
                        $0 = $0 " " a[i]
                        padded = padded a[i] " "
                    }
                }
            }
            { print }
        ' "${entry}" >"${tmp}"
        sudo install -m 0644 "${tmp}" "${entry}"
        rm -f "${tmp}"
    done
}

copy_image_to_rootful_storage() {
    if [[ "${UID}" -eq 0 ]]; then
        log "Already running as root; using rootful podman storage directly"
        return
    fi

    if ! podman image exists "${IMAGE}"; then
        printf 'Image %s not found in rootless podman storage\n' "${IMAGE}" >&2
        exit 1
    fi

    local user_img_id
    user_img_id=$(podman image inspect "${IMAGE}" --format '{{.Id}}')

    local root_img_id
    root_img_id=$("${rootful_podman[@]}" image inspect "${IMAGE}" --format '{{.Id}}' 2>/dev/null || true)

    if [[ -n "${root_img_id}" && "${user_img_id}" == "${root_img_id}" ]]; then
        log "Rootful podman storage already has ${IMAGE}"
        return
    elif [[ -n "${root_img_id}" ]]; then
        log "Re-using older sha image ${IMAGE}, if you updated bootc delete it."
        return
    fi

    log "Copying ${IMAGE} from rootless to rootful podman storage"
    podman save "${IMAGE}" | "${rootful_podman[@]}" load
}

mkdir -p "${vm_dir}"

log "Importing ${IMAGE} into ${ostree_dir}"
"${ludos[@]}" bootc ostree-import "${IMAGE}"

copy_image_to_rootful_storage

log "Creating ${disk} (${DISK_SIZE})"
rm -f "${disk}"
truncate -s "${DISK_SIZE}" "${disk}"

log "Installing ${IMAGE} to ${disk}"
"${rootful_podman[@]}" run --rm --privileged --pid=host --ipc=host \
    --security-opt label=type:unconfined_t \
    -v /var/lib/containers:/var/lib/containers \
    -v /dev:/dev \
    -v /run/udev:/run/udev \
    -v /var/tmp:/var/tmp \
    -v "${vm_dir}:/output" \
    -v "${ostree_dir}:/ludos/ostree:ro" \
    "${IMAGE}" \
    bootc install to-disk \
        --wipe \
        --via-loopback \
        --generic-image \
        --filesystem btrfs \
        --target-transport containers-storage \
        --target-imgref "${IMAGE}" \
        --skip-fetch-check \
        --ostree-repo /ludos/ostree \
        --ostree-ref "${OSTREE_REF}" \
        /output/anatase.raw

log "Created ${disk}"
append_vm_kernel_args

require_command "${QEMU_BIN}"

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
