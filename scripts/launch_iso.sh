#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"
# shellcheck source=scripts/ovmf.sh
source "${script_dir}/ovmf.sh"

VM_MEMORY=${VM_MEMORY:-8192}
VM_CPUS=${VM_CPUS:-4}
VM_DISK_SIZE=${VM_DISK_SIZE:-40G}
BIOS=${BIOS:-0}
VM_SECURE_BOOT=${VM_SECURE_BOOT:-1}
VM_RESET_DISK=${VM_RESET_DISK:-0}
SIMULATE_WINDOWS=${SIMULATE_WINDOWS:-0}
QEMU_BIN=${QEMU_BIN:-qemu-system-x86_64}
QEMU_IMG=${QEMU_IMG:-qemu-img}
QEMU_DISPLAY=${QEMU_DISPLAY:-gtk}
QEMU_VGA=${QEMU_VGA:-virtio}
QEMU_MACHINE=${QEMU_MACHINE:-q35}

cache_dir="${repo_root}/cache"
disk=${VM_DISK:-"${cache_dir}/vm.raw"}
ovmf_vars_was_explicit=0
if [[ -n "${VM_OVMF_VARS:-}" ]]; then
    ovmf_vars_was_explicit=1
    ovmf_vars=${VM_OVMF_VARS}
elif [[ "${VM_SECURE_BOOT}" == "1" ]]; then
    ovmf_vars="${cache_dir}/vm-ovmf-ms-vars.fd"
else
    ovmf_vars="${cache_dir}/vm-ovmf-vars.fd"
fi

usage() {
    printf 'Usage: %s <installer.iso>\n' "$0" >&2
    exit 2
}

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

create_thin_raw_disk() {
    local path=$1
    local size=$2

    rm -f "${path}"
    "${QEMU_IMG}" create -q -f raw -o preallocation=off "${path}" "${size}"
}

find_ntfs_mkfs() {
    if command -v mkfs.ntfs >/dev/null 2>&1; then
        command -v mkfs.ntfs
    elif command -v mkntfs >/dev/null 2>&1; then
        command -v mkntfs
    else
        return 1
    fi
}

create_simulated_windows_disk() {
    local root_cmd=()
    local ntfs_mkfs
    local loop=""
    local recovery_start_sector=$((129 * 1024 * 1024 / 512))
    local windows_start_sector=$((2177 * 1024 * 1024 / 512))

    require_command parted
    require_command losetup
    require_command mkfs.vfat
    ntfs_mkfs=$(find_ntfs_mkfs) || {
        printf 'Required command not found: mkfs.ntfs or mkntfs\n' >&2
        printf 'Install ntfsprogs/ntfs-3g to use SIMULATE_WINDOWS=1.\n' >&2
        exit 1
    }

    if [[ "${UID}" -ne 0 ]]; then
        require_command sudo
        root_cmd=(sudo)
    fi

    log "Creating simulated Windows target disk: ${disk} (${VM_DISK_SIZE})"
    create_thin_raw_disk "${disk}" "${VM_DISK_SIZE}"

    cleanup_loop() {
        if [[ -n "${loop}" ]]; then
            "${root_cmd[@]}" losetup -d "${loop}" || true
        fi
    }
    trap cleanup_loop RETURN

    loop=$("${root_cmd[@]}" losetup --find --show --partscan "${disk}")
    "${root_cmd[@]}" parted -s "${loop}" mklabel gpt
    "${root_cmd[@]}" parted -s "${loop}" mkpart EFI fat32 1MiB 129MiB
    "${root_cmd[@]}" parted -s "${loop}" name 1 EFI
    "${root_cmd[@]}" parted -s "${loop}" set 1 esp on
    "${root_cmd[@]}" parted -s "${loop}" mkpart recovery ntfs 129MiB 2177MiB
    "${root_cmd[@]}" parted -s "${loop}" name 2 WindowsRecovery
    "${root_cmd[@]}" parted -s "${loop}" type 2 de94bba4-06d1-4d40-a16a-bfd50179d6ac
    "${root_cmd[@]}" parted -s "${loop}" mkpart windows ntfs 2177MiB 100%
    "${root_cmd[@]}" parted -s "${loop}" name 3 "Windows"
    "${root_cmd[@]}" parted -s "${loop}" type 3 ebd0a0a2-b9e5-4433-87c0-68b6b72699c7
    "${root_cmd[@]}" partprobe "${loop}" || true
    "${root_cmd[@]}" udevadm settle || true

    "${root_cmd[@]}" mkfs.vfat -F32 -n WIN_EFI "${loop}p1"
    "${root_cmd[@]}" "${ntfs_mkfs}" -F -f -q -p "${recovery_start_sector}" -H 255 -S 63 -L WINRE "${loop}p2"
    "${root_cmd[@]}" "${ntfs_mkfs}" -F -f -q -p "${windows_start_sector}" -H 255 -S 63 -L WINDOWS "${loop}p3"

    trap - RETURN
    cleanup_loop
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

if (($# != 1)); then
    usage
fi

if [[ ! -f "$1" ]]; then
    printf 'Installer ISO not found: %s\n' "$1" >&2
    exit 1
fi
iso=$(realpath "$1")

require_command "${QEMU_BIN}"
require_command "${QEMU_IMG}"

mkdir -p "$(dirname -- "${disk}")" "$(dirname -- "${ovmf_vars}")"
case "${SIMULATE_WINDOWS}" in
    1)
        create_simulated_windows_disk
        ;;
    0)
        if [[ "${VM_RESET_DISK}" == "1" ]]; then
            log "Resetting installer target disk: ${disk}"
            rm -f "${disk}"
        fi

        if [[ ! -e "${disk}" ]]; then
            log "Creating installer target disk: ${disk} (${VM_DISK_SIZE})"
            create_thin_raw_disk "${disk}" "${VM_DISK_SIZE}"
        else
            log "Using installer target disk: ${disk}"
        fi
        ;;
    *)
        printf 'Unsupported SIMULATE_WINDOWS value: %s\n' "${SIMULATE_WINDOWS}" >&2
        printf 'Use SIMULATE_WINDOWS=1 to recreate a dummy Windows disk or SIMULATE_WINDOWS=0 for a plain target disk.\n' >&2
        exit 1
        ;;
esac

qemu_args=(
    -enable-kvm
    -cpu host
    -m "${VM_MEMORY}"
    -smp "${VM_CPUS}"
    -drive "if=none,id=install0,file=${disk},format=raw,cache=writeback,discard=unmap,detect-zeroes=unmap"
    -device "virtio-blk-pci,drive=install0,serial=ANATASE-INSTALL-TARGET"
    -drive "file=${iso},format=raw,media=cdrom,readonly=on"
    -boot order=cd,once=d
    -netdev user,id=net0
    -device virtio-net-pci,netdev=net0
    -vga "${QEMU_VGA}"
    -display "${QEMU_DISPLAY}"
    -serial mon:stdio
)

case "${BIOS}" in
    1)
        firmware=bios
        ;;
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
    *)
        printf 'Unsupported BIOS value: %s\n' "${BIOS}" >&2
        printf 'Use BIOS=0 for UEFI or BIOS=1 for legacy BIOS.\n' >&2
        exit 1
        ;;
esac

log "Launching ${iso} with ${QEMU_BIN} (${firmware})"
exec "${QEMU_BIN}" "${qemu_args[@]}"
