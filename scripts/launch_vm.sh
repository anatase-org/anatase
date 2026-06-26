#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"
# shellcheck source=scripts/ovmf.sh
source "${script_dir}/ovmf.sh"

VM_MEMORY=${VM_MEMORY:-8192}
VM_CPUS=${VM_CPUS:-4}
VM_SSH_PORT=${VM_SSH_PORT:-2222}
BIOS=${BIOS:-0}
VM_SECURE_BOOT=${VM_SECURE_BOOT:-1}
QEMU_BIN=${QEMU_BIN:-qemu-system-x86_64}
QEMU_DISPLAY=${QEMU_DISPLAY:-gtk}
QEMU_VGA=${QEMU_VGA:-virtio}
QEMU_GL=${QEMU_GL:-1}
QEMU_GPU_HOSTMEM=${QEMU_GPU_HOSTMEM:-1G}
QEMU_VENUS=${QEMU_VENUS:-0}
QEMU_MACHINE=${QEMU_MACHINE:-q35}
VM_KERNEL_ARGS=${VM_KERNEL_ARGS:-}
VM_OSTREE_SHARE=${VM_OSTREE_SHARE:-1}
VM_OSTREE_MOUNT_TAG=${VM_OSTREE_MOUNT_TAG:-anatase-ostree}
VM_OSTREE_MOUNT_POINT=${VM_OSTREE_MOUNT_POINT:-/run/anatase/ostree}

cache_dir="${repo_root}/cache"
ostree_dir="${cache_dir}/ostree"
disk="${cache_dir}/vm.raw"
ovmf_vars_was_explicit=0
if [[ -n "${VM_OVMF_VARS:-}" ]]; then
    ovmf_vars_was_explicit=1
    ovmf_vars=${VM_OVMF_VARS}
elif [[ "${VM_SECURE_BOOT}" == "1" ]]; then
    ovmf_vars="${cache_dir}/vm-ovmf-ms-vars.fd"
else
    ovmf_vars="${cache_dir}/vm-ovmf-vars.fd"
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

machine_with_smm() {
    local machine=$1
    if [[ "${machine}" == *smm=* ]]; then
        printf '%s\n' "${machine}"
    else
        printf '%s,smm=on\n' "${machine}"
    fi
}

file_size() {
    stat -c '%s' "$1"
}

display_with_gl() {
    local display=$1

    if [[ "${display}" == *",gl="* ]]; then
        printf '%s\n' "${display}"
    else
        printf '%s,gl=on\n' "${display}"
    fi
}

qemu_graphics_args() {
    if [[ "${QEMU_GL}" == "1" && "${QEMU_VGA}" == "virtio" ]]; then
        local device="virtio-vga-gl,blob=on,hostmem=${QEMU_GPU_HOSTMEM}"
        if [[ "${QEMU_VENUS}" == "1" ]]; then
            device+=",venus=on"
        fi
        printf '%s\n' -device "${device}"
        printf '%s\n' -display "$(display_with_gl "${QEMU_DISPLAY}")"
    else
        printf '%s\n' -vga "${QEMU_VGA}"
        printf '%s\n' -display "${QEMU_DISPLAY}"
    fi
}

require_matching_ovmf_flash() {
    local code_size vars_size
    code_size=$(file_size "${ovmf_code}")
    vars_size=$(file_size "${ovmf_vars}")

    if ! ovmf_vars_matches_code "${ovmf_code}" "${ovmf_vars}"; then
        if ((code_size > 3 * 1024 * 1024 && vars_size < 512 * 1024)); then
            printf 'OVMF vars store is too small for the selected 4M OVMF code image: %s\n' "${ovmf_vars}" >&2
            printf 'Use a matching 4M variables template, for example OVMF_VARS_4M.ms.fd.\n' >&2
        else
            printf 'OVMF vars store does not match the selected OVMF code image: %s\n' "${ovmf_vars}" >&2
        fi
        exit 1
    fi
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

mapfile -t graphics_args < <(qemu_graphics_args)

qemu_args=(
    -enable-kvm
    -cpu host
    -m "${VM_MEMORY}"
    -smp "${VM_CPUS}"
    -drive "file=${disk},format=raw,if=virtio"
    -netdev "user,id=net0,hostfwd=tcp::${VM_SSH_PORT}-:22"
    -device virtio-net-pci,netdev=net0
    "${graphics_args[@]}"
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
        ovmf_select_firmware "${VM_SECURE_BOOT}" "${QEMU_OVMF_CODE:-}" "${QEMU_OVMF_VARS_TEMPLATE:-}"

        if [[ ! -f "${ovmf_code}" ]]; then
            if [[ "${VM_SECURE_BOOT}" == "1" ]]; then
                printf 'Secure Boot OVMF code file not found. Set QEMU_OVMF_CODE or install edk2-ovmf with Secure Boot support.\n' >&2
            else
                printf 'OVMF code file not found. Set QEMU_OVMF_CODE or install edk2-ovmf.\n' >&2
            fi
            exit 1
        fi
        if [[ ! -f "${ovmf_template}" ]]; then
            if [[ "${VM_SECURE_BOOT}" == "1" ]]; then
                printf 'Microsoft-key OVMF vars template not found. Set QEMU_OVMF_VARS_TEMPLATE to an enrolled OVMF_VARS file, or set VM_SECURE_BOOT=0 for unenrolled UEFI.\n' >&2
            else
                printf 'OVMF vars template not found. Set QEMU_OVMF_VARS_TEMPLATE or install edk2-ovmf.\n' >&2
            fi
            exit 1
        fi
        if ! ovmf_vars_matches_code "${ovmf_code}" "${ovmf_template}"; then
            printf 'OVMF vars template does not match the selected OVMF code image: %s\n' "${ovmf_template}" >&2
            exit 1
        fi

        mkdir -p "$(dirname -- "${ovmf_vars}")"
        if [[ -e "${ovmf_vars}" ]] && ! ovmf_vars_matches_code "${ovmf_code}" "${ovmf_vars}"; then
            if [[ "${ovmf_vars_was_explicit}" == "1" ]]; then
                require_matching_ovmf_flash
            fi
            log "Replacing incompatible OVMF variables store: ${ovmf_vars}"
            cp "${ovmf_template}" "${ovmf_vars}"
        elif [[ ! -e "${ovmf_vars}" ]]; then
            log "Creating OVMF variables store: ${ovmf_vars}"
            cp "${ovmf_template}" "${ovmf_vars}"
        fi
        require_matching_ovmf_flash

        if [[ "${VM_SECURE_BOOT}" == "1" ]]; then
            qemu_args=(
                -machine "$(machine_with_smm "${QEMU_MACHINE}")"
                -global driver=cfi.pflash01,property=secure,value=on
                -drive "if=pflash,format=raw,unit=0,readonly=on,file=${ovmf_code}"
                -drive "if=pflash,format=raw,unit=1,file=${ovmf_vars}"
                "${qemu_args[@]}"
            )
            firmware="uefi secureboot"
        elif [[ "${VM_SECURE_BOOT}" == "0" ]]; then
            qemu_args=(
                -machine "${QEMU_MACHINE}"
                -drive "if=pflash,format=raw,unit=0,readonly=on,file=${ovmf_code}"
                -drive "if=pflash,format=raw,unit=1,file=${ovmf_vars}"
                "${qemu_args[@]}"
            )
            firmware=uefi
        else
            printf 'Unsupported VM_SECURE_BOOT value: %s\n' "${VM_SECURE_BOOT}" >&2
            printf 'Use VM_SECURE_BOOT=1 for Secure Boot or VM_SECURE_BOOT=0 for unenrolled UEFI.\n' >&2
            exit 1
        fi
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
