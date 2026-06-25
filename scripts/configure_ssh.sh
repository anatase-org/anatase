#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

VM_ROOT_SSH_KEY=${VM_ROOT_SSH_KEY:-${HOME:-}/.ssh/id_rsa.pub}
VM_DISK=${VM_DISK:-${repo_root}/cache/vm.raw}

if [[ "${UID}" -eq 0 ]]; then
    sudo_cmd=()
else
    sudo_cmd=(sudo)
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

if [[ ! -e "${VM_DISK}" ]]; then
    printf 'VM disk not found: %s\n' "${VM_DISK}" >&2
    printf 'Run scripts/deploy_vm.sh first to create it, or set VM_DISK.\n' >&2
    exit 1
fi

if [[ ! -s "${VM_ROOT_SSH_KEY}" ]]; then
    printf 'Root SSH public key not found or empty: %s\n' "${VM_ROOT_SSH_KEY}" >&2
    printf 'Set VM_ROOT_SSH_KEY to the public key to authorize.\n' >&2
    exit 1
fi

require_command losetup
require_command mount
require_command blkid

cache_dir="${repo_root}/cache"
mkdir -p "${cache_dir}"

mnt=$(mktemp -d "${cache_dir}/anatase-ssh.XXXXXX")
loop=""
kpartx_mapped=0
cleanup_done=0

cleanup() {
    local fail_on_error=${1:-0}
    local status=0

    set +e

    if [[ "${cleanup_done}" == 1 ]]; then
        return 0
    fi

    sync

    if [[ -d "${mnt}" ]] && mountpoint -q "${mnt}"; then
        "${sudo_cmd[@]}" umount "${mnt}" || status=1
    fi

    if [[ "${kpartx_mapped}" == 1 && -n "${loop}" ]]; then
        "${sudo_cmd[@]}" kpartx -d "${loop}" || status=1
        kpartx_mapped=0
    fi

    if [[ -n "${loop}" ]]; then
        if "${sudo_cmd[@]}" losetup -d "${loop}"; then
            loop=""
        else
            status=1
        fi
    fi

    rmdir "${mnt}" 2>/dev/null || true
    cleanup_done=1

    if [[ "${fail_on_error}" == 1 && "${status}" -ne 0 ]]; then
        printf 'Failed to unmount VM filesystems or detach %s\n' "${loop:-loop device}" >&2
        return "${status}"
    fi

    return 0
}
trap cleanup EXIT

settle_block_devices() {
    if command -v partprobe >/dev/null 2>&1; then
        "${sudo_cmd[@]}" partprobe "${loop}" || true
    fi
    if command -v udevadm >/dev/null 2>&1; then
        "${sudo_cmd[@]}" udevadm settle || true
    fi
}

find_root_partition() {
    local part type

    for part in "$@"; do
        [[ -b "${part}" ]] || continue
        type=$("${sudo_cmd[@]}" blkid -o value -s TYPE "${part}" 2>/dev/null || true)
        if [[ "${type}" == btrfs ]]; then
            printf '%s\n' "${part}"
            return 0
        fi
    done

    return 1
}

discover_root_partition() {
    local base root_part i candidates=()

    settle_block_devices
    for i in {1..50}; do
        root_part=$(find_root_partition "${loop}"p4 "${loop}"p3 "${loop}"p2 "${loop}"p1 || true)
        if [[ -n "${root_part}" ]]; then
            printf '%s\n' "${root_part}"
            return 0
        fi
        sleep 0.1
    done

    if ! command -v kpartx >/dev/null 2>&1; then
        printf 'Could not find a btrfs root partition for %s, and kpartx is not installed\n' "${loop}" >&2
        return 1
    fi

    printf '==> Mapping partitions for %s with kpartx\n' "${loop}" >&2
    "${sudo_cmd[@]}" kpartx -a "${loop}" >/dev/null
    kpartx_mapped=1
    settle_block_devices

    base=$(basename -- "${loop}")
    for i in {1..16}; do
        candidates+=("/dev/mapper/${base}p${i}")
    done

    for i in {1..50}; do
        root_part=$(find_root_partition "${candidates[@]}" || true)
        if [[ -n "${root_part}" ]]; then
            printf '%s\n' "${root_part}"
            return 0
        fi
        sleep 0.1
    done

    printf 'Could not find a btrfs root partition for %s\n' "${loop}" >&2
    return 1
}

find_sysroot() {
    if [[ -d "${mnt}/ostree/deploy" ]]; then
        printf '%s\n' "${mnt}"
    elif [[ -d "${mnt}/root/ostree/deploy" ]]; then
        printf '%s\n' "${mnt}/root"
    else
        return 1
    fi
}

configure_root_ssh() {
    local root_ssh_authorized_key=$1
    local configured_stateroots=0
    local configured_deployments=0
    local sysroot stateroot var_dir ssh_dir auth_keys deployment wants sshd_config_dir restorecon_unit

    sysroot=$(find_sysroot) || {
        printf 'No OSTree sysroot found in mounted VM disk\n' >&2
        return 1
    }

    for stateroot in "${sysroot}"/ostree/deploy/*; do
        [[ -d "${stateroot}/var" ]] || continue

        var_dir="${stateroot}/var"
        if [[ "${sysroot}" != "${mnt}" && -d "${mnt}/var" ]]; then
            var_dir="${mnt}/var"
        fi

        ssh_dir="${var_dir}/roothome/.ssh"
        auth_keys="${ssh_dir}/authorized_keys"

        "${sudo_cmd[@]}" install -d -m 0700 -o root -g root "${ssh_dir}"
        "${sudo_cmd[@]}" touch "${auth_keys}"
        if ! "${sudo_cmd[@]}" grep -Fxq -- "${root_ssh_authorized_key}" "${auth_keys}"; then
            printf '%s\n' "${root_ssh_authorized_key}" | "${sudo_cmd[@]}" tee -a "${auth_keys}" >/dev/null
        fi
        "${sudo_cmd[@]}" chmod 0600 "${auth_keys}"
        "${sudo_cmd[@]}" chown root:root "${auth_keys}"
        configured_stateroots=$((configured_stateroots + 1))
    done

    for deployment in "${sysroot}"/ostree/deploy/*/deploy/*.0; do
        [[ -d "${deployment}/etc" ]] || continue

        wants="${deployment}/etc/systemd/system/multi-user.target.wants"
        "${sudo_cmd[@]}" install -d -m 0755 "${wants}"
        "${sudo_cmd[@]}" ln -sfn /usr/lib/systemd/system/sshd.service "${wants}/sshd.service"
        "${sudo_cmd[@]}" ln -sfn /etc/systemd/system/anatase-vm-root-ssh-restorecon.service "${wants}/anatase-vm-root-ssh-restorecon.service"

        sshd_config_dir="${deployment}/etc/ssh/sshd_config.d"
        "${sudo_cmd[@]}" install -d -m 0755 "${sshd_config_dir}"
        printf 'PermitRootLogin prohibit-password\n' | "${sudo_cmd[@]}" tee "${sshd_config_dir}/10-anatase-vm-root-login.conf" >/dev/null
        "${sudo_cmd[@]}" chmod 0644 "${sshd_config_dir}/10-anatase-vm-root-login.conf"

        restorecon_unit="${deployment}/etc/systemd/system/anatase-vm-root-ssh-restorecon.service"
        "${sudo_cmd[@]}" tee "${restorecon_unit}" >/dev/null <<'UNIT_EOF'
[Unit]
Description=Relabel VM root SSH access files
Before=sshd.service
ConditionPathExists=/var/roothome/.ssh/authorized_keys

[Service]
Type=oneshot
ExecStart=/usr/sbin/restorecon -RF /var/roothome/.ssh /etc/ssh/sshd_config.d/10-anatase-vm-root-login.conf

[Install]
WantedBy=multi-user.target
UNIT_EOF
        "${sudo_cmd[@]}" chmod 0644 "${restorecon_unit}"
        configured_deployments=$((configured_deployments + 1))
    done

    if [[ "${configured_stateroots}" -eq 0 || "${configured_deployments}" -eq 0 ]]; then
        printf 'No OSTree stateroots/deployments found in mounted VM disk\n' >&2
        return 1
    fi
}

log "Mounting ${VM_DISK}"
loop=$("${sudo_cmd[@]}" losetup --find --show --partscan "${VM_DISK}")
root_part=$(discover_root_partition)
"${sudo_cmd[@]}" mount "${root_part}" "${mnt}"

log "Configuring root SSH access with ${VM_ROOT_SSH_KEY}"
configure_root_ssh "$(<"${VM_ROOT_SSH_KEY}")"

trap - EXIT
cleanup 1

log "Configured root SSH access on ${VM_DISK}"
