#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

MANIFEST=${MANIFEST:-anatase.yml}
manifest_image=${MANIFEST##*/}
manifest_image=${manifest_image%.yml}
manifest_image=${manifest_image%.yaml}
IMAGE=${IMAGE:-localhost/${manifest_image}:f44-x86_64}
OSTREE_REF=${OSTREE_REF:-master}
DISK_SIZE=${DISK_SIZE:-40G}
VM_ROOT_SSH_KEY=${VM_ROOT_SSH_KEY:-${HOME:-}/.ssh/id_rsa.pub}

cache_dir="${repo_root}/cache"
ostree_dir="${cache_dir}/ostree"
disk="${cache_dir}/vm.raw"

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
        log "Re-using older sha image ${IMAGE}, if you updated bootc or your shim/grub delete it."
        return
    fi

    log "Copying ${IMAGE} from rootless to rootful podman storage"
    podman save "${IMAGE}" | "${rootful_podman[@]}" load
}

log "Building ${MANIFEST}"
"${ludos[@]}" build "${MANIFEST}" $@

mkdir -p "${cache_dir}"

log "Importing ${IMAGE} into ${ostree_dir}"
"${ludos[@]}" bootc ostree-import "${IMAGE}"

copy_image_to_rootful_storage

log "Creating ${disk} (${DISK_SIZE})"
rm -f "${disk}"
truncate -s "${DISK_SIZE}" "${disk}"

root_ssh_authorized_key=""
if [[ -s "${VM_ROOT_SSH_KEY}" ]]; then
    log "Configuring root SSH access with ${VM_ROOT_SSH_KEY}"
    root_ssh_authorized_key=$(<"${VM_ROOT_SSH_KEY}")
fi

log "Installing ${IMAGE} to ${disk}"
"${rootful_podman[@]}" run --rm --privileged --pid=host --ipc=host \
    --security-opt label=type:unconfined_t \
    -v /dev:/dev \
    -v /run/udev:/run/udev \
    -v /var/tmp:/var/tmp \
    -v "${cache_dir}:/output" \
    -v "${ostree_dir}:/ludos/ostree:ro" \
    -e "OSTREE_REF=${OSTREE_REF}" \
    -e "VM_ROOT_SSH_AUTHORIZED_KEY=${root_ssh_authorized_key}" \
    "${IMAGE}" \
    bash -ceu '
disk=/output/vm.raw
mnt=$(mktemp -d "${TMPDIR:-/var/tmp}/anatase-install.XXXXXX")
loop=""
cleanup_done=0

cleanup() {
    local fail_on_error=${1:-0}
    local status=0

    set +e

    if [ "${cleanup_done}" = 1 ]; then
        return 0
    fi

    sync

    if [ -d "${mnt}" ]; then
        if command -v findmnt >/dev/null 2>&1 && findmnt -R --target "${mnt}" >/dev/null 2>&1; then
            umount -R "${mnt}" || status=1
        else
            if mountpoint -q "${mnt}/boot/efi"; then
                umount "${mnt}/boot/efi" || status=1
            fi
            if mountpoint -q "${mnt}/boot"; then
                umount "${mnt}/boot" || status=1
            fi
            if mountpoint -q "${mnt}"; then
                umount "${mnt}" || status=1
            fi
        fi
    fi

    if [ -n "${loop}" ]; then
        if losetup -d "${loop}"; then
            loop=""
        else
            status=1
        fi
    fi

    rmdir "${mnt}/boot/efi" "${mnt}/boot" "${mnt}" 2>/dev/null || true
    cleanup_done=1

    if [ "${fail_on_error}" = 1 ] && [ "${status}" -ne 0 ]; then
        printf "Failed to unmount VM install filesystems or detach %s\n" "${loop:-loop device}" >&2
        return "${status}"
    fi

    return 0
}
trap cleanup EXIT

configure_root_ssh() {
    if [ -z "${VM_ROOT_SSH_AUTHORIZED_KEY:-}" ]; then
        return
    fi

    for stateroot in "${mnt}"/ostree/deploy/*; do
        [ -d "${stateroot}/var" ] || continue

        ssh_dir="${stateroot}/var/roothome/.ssh"
        auth_keys="${ssh_dir}/authorized_keys"

        install -d -m 0700 -o root -g root "${ssh_dir}"
        touch "${auth_keys}"
        if ! grep -Fxq -- "${VM_ROOT_SSH_AUTHORIZED_KEY}" "${auth_keys}"; then
            printf "%s\n" "${VM_ROOT_SSH_AUTHORIZED_KEY}" >>"${auth_keys}"
        fi
        chmod 0600 "${auth_keys}"
        chown root:root "${auth_keys}"
    done

    for deployment in "${mnt}"/ostree/deploy/*/deploy/*.0; do
        [ -d "${deployment}/etc" ] || continue

        wants="${deployment}/etc/systemd/system/multi-user.target.wants"
        install -d -m 0755 "${wants}"
        ln -sfn /usr/lib/systemd/system/sshd.service "${wants}/sshd.service"
        ln -sfn /etc/systemd/system/anatase-vm-root-ssh-restorecon.service "${wants}/anatase-vm-root-ssh-restorecon.service"

        sshd_config_dir="${deployment}/etc/ssh/sshd_config.d"
        install -d -m 0755 "${sshd_config_dir}"
        printf "PermitRootLogin prohibit-password\n" >"${sshd_config_dir}/10-anatase-vm-root-login.conf"
        chmod 0644 "${sshd_config_dir}/10-anatase-vm-root-login.conf"

        restorecon_unit="${deployment}/etc/systemd/system/anatase-vm-root-ssh-restorecon.service"
        cat >"${restorecon_unit}" <<UNIT_EOF
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
        chmod 0644 "${restorecon_unit}"
    done
}

loop=$(losetup --find --show --partscan "${disk}")

parted -s "${loop}" mklabel gpt
parted -s "${loop}" mkpart bios_grub 1MiB 2MiB
parted -s "${loop}" set 1 bios_grub on
parted -s "${loop}" mkpart EFI fat32 2MiB 514MiB
parted -s "${loop}" set 2 esp on
parted -s "${loop}" mkpart boot ext4 514MiB 2562MiB
parted -s "${loop}" mkpart root btrfs 2562MiB 100%
partprobe "${loop}" || true
udevadm settle || true

mkfs.vfat -F32 -n ANATASE_EFI "${loop}p2"
mkfs.ext4 -F -L ANATASE_BOOT "${loop}p3"
mkfs.btrfs -f -L ANATASE_ROOT "${loop}p4"

mount "${loop}p4" "${mnt}"
mkdir -p "${mnt}/boot"
mount "${loop}p3" "${mnt}/boot"
mkdir -p "${mnt}/boot/efi"
mount "${loop}p2" "${mnt}/boot/efi"

ostree admin init-fs --modern "${mnt}"
ostree admin stateroot-init --sysroot="${mnt}" anatase
ostree --repo="${mnt}/ostree/repo" pull-local /ludos/ostree "${OSTREE_REF}"

root_uuid=$(blkid -s UUID -o value "${loop}p4")
boot_uuid=$(blkid -s UUID -o value "${loop}p3")
esp_uuid=$(blkid -s UUID -o value "${loop}p2")

ostree admin deploy \
    --sysroot="${mnt}" \
    --os=anatase \
    --karg-none \
    --karg="root=UUID=${root_uuid}" \
    --karg=rw \
    --karg=quiet \
    --karg=rhgb \
    "${OSTREE_REF}"

deployment=$(find "${mnt}/ostree/deploy/anatase/deploy" -maxdepth 1 -type d -name "*.0" | head -n1)
if [ -z "${deployment}" ]; then
    echo "No OSTree deployment was created" >&2
    exit 1
fi

install -d -m 0755 "${deployment}/etc"
cat > "${deployment}/etc/fstab" <<EOF
UUID=${boot_uuid} /boot ext4 defaults 0 2
UUID=${esp_uuid} /boot/efi vfat umask=0077,shortname=winnt 0 2
EOF

configure_root_ssh

install -d -m 0755 "${mnt}/boot/grub2" "${mnt}/boot/efi/EFI"
cat /usr/lib/bootupd/grub2-static/grub-static-pre.cfg \
    /usr/lib/bootupd/grub2-static/configs.d/*.cfg \
    > "${mnt}/boot/grub2/grub.cfg"
printf "set BOOT_UUID=%s\n" "${boot_uuid}" > "${mnt}/boot/grub2/bootuuid.cfg"

grub2-install --target=i386-pc --boot-directory="${mnt}/boot" --recheck "${loop}"

# The source EFI trees may contain hard-linked fallback binaries. The VM ESP is
# vfat, so copy file contents instead of preserving hard-link relationships.
if [ -d /usr/lib/ludos/efi ]; then
    cp -R --no-preserve=mode,ownership,timestamps /usr/lib/ludos/efi/. "${mnt}/boot/efi/"
fi
cp -R --no-preserve=links /usr/lib/efi/shim/*/EFI/. "${mnt}/boot/efi/EFI/"
cp -R --no-preserve=links /usr/lib/efi/grub2/*/EFI/. "${mnt}/boot/efi/EFI/"
efi_vendor=anatase
install -d -m 0755 "${mnt}/boot/efi/EFI/BOOT" "${mnt}/boot/efi/EFI/${efi_vendor}"
if [ -d "${mnt}/boot/efi/EFI/fedora" ]; then
    cp -R --no-preserve=links "${mnt}/boot/efi/EFI/fedora/." "${mnt}/boot/efi/EFI/${efi_vendor}/"
    rm -rf "${mnt}/boot/efi/EFI/fedora"
fi
if [ -f "${mnt}/boot/efi/EFI/${efi_vendor}/grubx64.efi" ]; then
    cp -f "${mnt}/boot/efi/EFI/${efi_vendor}/grubx64.efi" "${mnt}/boot/efi/EFI/BOOT/grubx64.efi"
fi
for grub_cfg in "${mnt}/boot/efi/EFI/${efi_vendor}/grub.cfg" "${mnt}/boot/efi/EFI/BOOT/grub.cfg"; do
    cat > "${grub_cfg}" <<EOF
search --fs-uuid ${boot_uuid} --set boot --no-floppy
set prefix=(\$boot)/grub2
configfile \$prefix/grub.cfg
EOF
done

trap - EXIT
cleanup 1
cleanup_status=$?
if [ "${cleanup_status}" -ne 0 ]; then
    exit "${cleanup_status}"
fi
'

log "Created ${disk}"
exec "${script_dir}/launch_vm.sh"
