#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

VM_MEMORY=${VM_MEMORY:-8192}
VM_CPUS=${VM_CPUS:-4}
VM_SSH_PORT=${VM_SSH_PORT:-2222}
BIOS=${BIOS:-0}
QEMU_BIN=${QEMU_BIN:-qemu-system-x86_64}
QEMU_DISPLAY=${QEMU_DISPLAY:-gtk}
QEMU_VGA=${QEMU_VGA:-virtio}
VM_KERNEL_ARGS=${VM_KERNEL_ARGS:-}
VM_OSTREE_SHARE=${VM_OSTREE_SHARE:-1}
VM_OSTREE_MOUNT_TAG=${VM_OSTREE_MOUNT_TAG:-anatase-ostree}
VM_OSTREE_MOUNT_POINT=${VM_OSTREE_MOUNT_POINT:-/run/anatase/ostree}

cache_dir="${repo_root}/cache"
ostree_dir="${cache_dir}/ostree"
disk="${cache_dir}/vm.raw"
ovmf_vars=${VM_OVMF_VARS:-"${cache_dir}/vm-ovmf-vars.fd"}

log() {
    printf '==> %s\n' "$*"
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        printf 'Required command not found: %s\n' "$1" >&2
        exit 1
    fi
}

first_existing() {
    local path
    for path in "$@"; do
        if [[ -e "${path}" ]]; then
            printf '%s\n' "${path}"
            return 0
        fi
    done
    return 1
}

append_vm_kernel_args() {
    if [[ -z "${VM_KERNEL_ARGS}" ]]; then
        return
    fi

    local loop=""
    local mount_dir=""
    trap 'set +e; if [[ -n "${mount_dir}" ]] && mountpoint -q "${mount_dir}/boot"; then sudo umount "${mount_dir}/boot"; fi; if [[ -n "${mount_dir}" ]] && mountpoint -q "${mount_dir}"; then sudo umount "${mount_dir}"; fi; if [[ -n "${loop}" ]]; then sudo losetup -d "${loop}"; fi; if [[ -n "${mount_dir}" ]]; then rmdir "${mount_dir}/boot" "${mount_dir}" 2>/dev/null; fi; trap - RETURN' RETURN

    log "Adding VM kernel args: ${VM_KERNEL_ARGS}"
    loop=$(sudo losetup --find --show --partscan "${disk}")
    mount_dir=$(mktemp -d "${TMPDIR:-/tmp}/anatase-vm.XXXXXX")
    sudo mount "${loop}p4" "${mount_dir}"
    sudo mkdir -p "${mount_dir}/boot"
    sudo mount "${loop}p3" "${mount_dir}/boot"

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

require_command "${QEMU_BIN}"

if [[ ! -e "${disk}" ]]; then
    printf 'VM disk not found: %s\n' "${disk}" >&2
    printf 'Run scripts/deploy_vm.sh first to create it.\n' >&2
    exit 1
fi

append_vm_kernel_args

qemu_args=(
    -enable-kvm
    -cpu host
    -m "${VM_MEMORY}"
    -smp "${VM_CPUS}"
    -drive "file=${disk},format=raw,if=virtio"
    -netdev "user,id=net0,hostfwd=tcp::${VM_SSH_PORT}-:22"
    -device virtio-net-pci,netdev=net0
    -vga "${QEMU_VGA}"
    -display "${QEMU_DISPLAY}"
    -serial mon:stdio
)

if [[ "${VM_OSTREE_SHARE}" == "1" ]]; then
    mkdir -p "${ostree_dir}"
    log "Sharing ${ostree_dir} as 9p tag ${VM_OSTREE_MOUNT_TAG}"
    log "Mount in the VM with: sudo mkdir -p ${VM_OSTREE_MOUNT_POINT} && sudo mount -t 9p -o trans=virtio,version=9p2000.L,msize=104857600 ${VM_OSTREE_MOUNT_TAG} ${VM_OSTREE_MOUNT_POINT}"
    qemu_args+=(
        -fsdev "local,id=ostree,path=${ostree_dir},security_model=none,multidevs=remap"
        -device "virtio-9p-pci,fsdev=ostree,mount_tag=${VM_OSTREE_MOUNT_TAG}"
    )
fi

case "${BIOS}" in
    0)
        ovmf_code=${QEMU_OVMF_CODE:-}
        if [[ -z "${ovmf_code}" ]]; then
            ovmf_code=$(first_existing \
                /usr/share/edk2/x64/OVMF_CODE.4m.fd \
                /usr/share/edk2/ovmf/OVMF_CODE.fd \
                /usr/share/OVMF/OVMF_CODE.fd || true)
        fi

        ovmf_template=${QEMU_OVMF_VARS_TEMPLATE:-}
        if [[ -z "${ovmf_template}" ]]; then
            ovmf_template=$(first_existing \
                /usr/share/edk2/x64/OVMF_VARS.4m.fd \
                /usr/share/edk2/ovmf/OVMF_VARS.fd \
                /usr/share/OVMF/OVMF_VARS.fd || true)
        fi

        if [[ ! -f "${ovmf_code}" ]]; then
            printf 'OVMF code file not found. Set QEMU_OVMF_CODE or install edk2-ovmf.\n' >&2
            exit 1
        fi
        if [[ ! -f "${ovmf_template}" ]]; then
            printf 'OVMF vars template not found. Set QEMU_OVMF_VARS_TEMPLATE or install edk2-ovmf.\n' >&2
            exit 1
        fi

        mkdir -p "$(dirname -- "${ovmf_vars}")"
        if [[ ! -e "${ovmf_vars}" ]]; then
            log "Creating OVMF variables store: ${ovmf_vars}"
            cp "${ovmf_template}" "${ovmf_vars}"
        fi

        qemu_args=(
            -drive "if=pflash,format=raw,readonly=on,file=${ovmf_code}"
            -drive "if=pflash,format=raw,file=${ovmf_vars}"
            "${qemu_args[@]}"
        )
        firmware=uefi
        ;;
    1)
        firmware=bios
        ;;
    *)
        printf 'Unsupported BIOS value: %s\n' "${BIOS}" >&2
        printf 'Use BIOS=0 for UEFI or BIOS=1 for legacy BIOS.\n' >&2
        exit 1
        ;;
esac

log "Launching ${disk} with ${QEMU_BIN} (${firmware})"
exec "${QEMU_BIN}" "${qemu_args[@]}"
