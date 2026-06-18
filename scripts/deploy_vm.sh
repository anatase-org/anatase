#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

IMAGE=${IMAGE:-localhost/anatase:f44-x86_64}
OSTREE_REF=${OSTREE_REF:-master}
DISK_SIZE=${DISK_SIZE:-40G}

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
exec "${script_dir}/launch_vm.sh"
