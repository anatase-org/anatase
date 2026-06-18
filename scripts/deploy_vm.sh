#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

IMAGE=${IMAGE:-localhost/anatase:f44-x86_64}
OSTREE_REF=${OSTREE_REF:-master}
DISK_SIZE=${DISK_SIZE:-40G}
VM_ROOT_SSH_KEY=${VM_ROOT_SSH_KEY:-${HOME:-}/.ssh/id_rsa.pub}

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

configure_root_ssh() {
    if [[ ! -s "${VM_ROOT_SSH_KEY}" ]]; then
        return
    fi

    local loop=""
    local mount_dir=""
    trap 'set +e; if [[ -n "${mount_dir}" ]] && mountpoint -q "${mount_dir}"; then sudo umount "${mount_dir}"; fi; if [[ -n "${loop}" ]]; then sudo losetup -d "${loop}"; fi; if [[ -n "${mount_dir}" ]]; then rmdir "${mount_dir}" 2>/dev/null; fi; trap - RETURN' RETURN

    log "Configuring root SSH access with ${VM_ROOT_SSH_KEY}"
    loop=$(sudo losetup --find --show --partscan "${disk}")
    mount_dir=$(mktemp -d "${TMPDIR:-/tmp}/anatase-vm.XXXXXX")
    sudo mount "${loop}p3" "${mount_dir}"

    local key
    key=$(<"${VM_ROOT_SSH_KEY}")

    local nullglob_was_set=0
    if shopt -q nullglob; then
        nullglob_was_set=1
    fi

    local stateroot ssh_dir auth_keys
    shopt -s nullglob
    for stateroot in "${mount_dir}"/ostree/deploy/*; do
        [[ -d "${stateroot}/var" ]] || continue

        ssh_dir="${stateroot}/var/roothome/.ssh"
        auth_keys="${ssh_dir}/authorized_keys"

        sudo install -d -m 0700 -o root -g root "${ssh_dir}"
        sudo touch "${auth_keys}"
        if ! sudo grep -Fxq -- "${key}" "${auth_keys}"; then
            printf '%s\n' "${key}" | sudo tee -a "${auth_keys}" >/dev/null
        fi
        sudo chmod 0600 "${auth_keys}"
        sudo chown root:root "${auth_keys}"
    done

    local deployment wants sshd_config_dir restorecon_unit
    for deployment in "${mount_dir}"/ostree/deploy/*/deploy/*.0; do
        [[ -d "${deployment}/etc" ]] || continue

        wants="${deployment}/etc/systemd/system/multi-user.target.wants"
        sudo install -d -m 0755 "${wants}"
        sudo ln -sfn /usr/lib/systemd/system/sshd.service "${wants}/sshd.service"
        sudo ln -sfn /etc/systemd/system/anatase-vm-root-ssh-restorecon.service "${wants}/anatase-vm-root-ssh-restorecon.service"

        sshd_config_dir="${deployment}/etc/ssh/sshd_config.d"
        sudo install -d -m 0755 "${sshd_config_dir}"
        printf 'PermitRootLogin prohibit-password\n' | sudo tee "${sshd_config_dir}/10-anatase-vm-root-login.conf" >/dev/null
        sudo chmod 0644 "${sshd_config_dir}/10-anatase-vm-root-login.conf"

        restorecon_unit="${deployment}/etc/systemd/system/anatase-vm-root-ssh-restorecon.service"
        sudo tee "${restorecon_unit}" >/dev/null <<'EOF'
[Unit]
Description=Relabel VM root SSH access files
Before=sshd.service
ConditionPathExists=/var/roothome/.ssh/authorized_keys

[Service]
Type=oneshot
ExecStart=/usr/sbin/restorecon -RF /var/roothome/.ssh /etc/ssh/sshd_config.d/10-anatase-vm-root-login.conf

[Install]
WantedBy=multi-user.target
EOF
        sudo chmod 0644 "${restorecon_unit}"
    done
    if ((nullglob_was_set == 0)); then
        shopt -u nullglob
    fi
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
configure_root_ssh
exec "${script_dir}/launch_vm.sh"
