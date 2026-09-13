ovmf_code_is_4m() {
    local path=$1
    [[ -f "${path}" ]] && (($(file_size "${path}") > 3 * 1024 * 1024))
}

ovmf_vars_is_4m() {
    local path=$1
    [[ -f "${path}" ]] && (($(file_size "${path}") >= 512 * 1024))
}

ovmf_vars_matches_code() {
    local code=$1
    local vars=$2

    if ovmf_code_is_4m "${code}"; then
        ovmf_vars_is_4m "${vars}"
    else
        ! ovmf_vars_is_4m "${vars}"
    fi
}

ovmf_pair_candidates() {
    local secure_boot=$1

    if [[ "${secure_boot}" == "1" ]]; then
        cat <<EOF
${cache_dir}/ovmf-ms/OVMF_CODE_4M.ms.fd|${cache_dir}/ovmf-ms/OVMF_VARS_4M.ms.fd
${cache_dir}/ovmf-ms/OVMF_CODE_4M.secboot.fd|${cache_dir}/ovmf-ms/OVMF_VARS_4M.secboot.fd
/usr/share/OVMF/OVMF_CODE_4M.ms.fd|/usr/share/OVMF/OVMF_VARS_4M.ms.fd
/usr/share/OVMF/OVMF_CODE_4M.secboot.fd|/usr/share/OVMF/OVMF_VARS_4M.secboot.fd
/usr/share/edk2/x64/OVMF_CODE.secboot.4m.fd|/usr/share/edk2/x64/OVMF_VARS.ms.4m.fd
/usr/share/edk2/x64/OVMF_CODE.secboot.4m.fd|/usr/share/edk2/x64/OVMF_VARS.secboot.4m.fd
/usr/share/OVMF/OVMF_CODE.ms.fd|/usr/share/OVMF/OVMF_VARS.ms.fd
/usr/share/OVMF/OVMF_CODE.secboot.fd|/usr/share/OVMF/OVMF_VARS.secboot.fd
/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd|/usr/share/edk2/ovmf/OVMF_VARS.ms.fd
/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd|/usr/share/edk2/ovmf/OVMF_VARS.secboot.fd
/usr/share/edk2-ovmf-fedora/edk2/ovmf/OVMF_CODE.secboot.fd|/usr/share/edk2-ovmf-fedora/edk2/ovmf/OVMF_VARS.secboot.fd
EOF
    else
        cat <<EOF
/usr/share/edk2/x64/OVMF_CODE.4m.fd|/usr/share/edk2/x64/OVMF_VARS.4m.fd
/usr/share/OVMF/OVMF_CODE_4M.fd|/usr/share/OVMF/OVMF_VARS_4M.fd
/usr/share/edk2/ovmf/OVMF_CODE.fd|/usr/share/edk2/ovmf/OVMF_VARS.fd
/usr/share/OVMF/OVMF_CODE.fd|/usr/share/OVMF/OVMF_VARS.fd
/usr/share/edk2-ovmf-fedora/edk2/ovmf/OVMF_CODE.fd|/usr/share/edk2-ovmf-fedora/edk2/ovmf/OVMF_VARS.fd
EOF
    fi
}

ovmf_template_candidates_for_code() {
    local secure_boot=$1
    local code=$2

    if ovmf_code_is_4m "${code}"; then
        if [[ "${secure_boot}" == "1" ]]; then
            cat <<EOF
${cache_dir}/ovmf-ms/OVMF_VARS_4M.ms.fd
${cache_dir}/ovmf-ms/OVMF_VARS_4M.secboot.fd
/usr/share/OVMF/OVMF_VARS_4M.ms.fd
/usr/share/OVMF/OVMF_VARS_4M.secboot.fd
/usr/share/edk2/x64/OVMF_VARS.ms.4m.fd
/usr/share/edk2/x64/OVMF_VARS.secboot.4m.fd
EOF
        else
            cat <<EOF
/usr/share/edk2/x64/OVMF_VARS.4m.fd
/usr/share/OVMF/OVMF_VARS_4M.fd
EOF
        fi
    else
        if [[ "${secure_boot}" == "1" ]]; then
            cat <<EOF
/usr/share/OVMF/OVMF_VARS.ms.fd
/usr/share/OVMF/OVMF_VARS.secboot.fd
/usr/share/edk2/ovmf/OVMF_VARS.ms.fd
/usr/share/edk2/ovmf/OVMF_VARS.secboot.fd
/usr/share/edk2-ovmf-fedora/edk2/ovmf/OVMF_VARS.secboot.fd
EOF
        else
            cat <<EOF
/usr/share/edk2/ovmf/OVMF_VARS.fd
/usr/share/OVMF/OVMF_VARS.fd
/usr/share/edk2-ovmf-fedora/edk2/ovmf/OVMF_VARS.fd
EOF
        fi
    fi
}

ovmf_code_candidates_for_template() {
    local secure_boot=$1
    local template=$2

    if ovmf_vars_is_4m "${template}"; then
        if [[ "${secure_boot}" == "1" ]]; then
            cat <<EOF
${cache_dir}/ovmf-ms/OVMF_CODE_4M.ms.fd
${cache_dir}/ovmf-ms/OVMF_CODE_4M.secboot.fd
/usr/share/OVMF/OVMF_CODE_4M.ms.fd
/usr/share/OVMF/OVMF_CODE_4M.secboot.fd
/usr/share/edk2/x64/OVMF_CODE.secboot.4m.fd
EOF
        else
            cat <<EOF
/usr/share/edk2/x64/OVMF_CODE.4m.fd
/usr/share/OVMF/OVMF_CODE_4M.fd
EOF
        fi
    else
        if [[ "${secure_boot}" == "1" ]]; then
            cat <<EOF
/usr/share/OVMF/OVMF_CODE.ms.fd
/usr/share/OVMF/OVMF_CODE.secboot.fd
/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd
/usr/share/edk2-ovmf-fedora/edk2/ovmf/OVMF_CODE.secboot.fd
EOF
        else
            cat <<EOF
/usr/share/edk2/ovmf/OVMF_CODE.fd
/usr/share/OVMF/OVMF_CODE.fd
/usr/share/edk2-ovmf-fedora/edk2/ovmf/OVMF_CODE.fd
EOF
        fi
    fi
}

ovmf_first_matching_pair() {
    local secure_boot=$1
    local code template

    while IFS='|' read -r code template; do
        if [[ -f "${code}" && -f "${template}" ]] && ovmf_vars_matches_code "${code}" "${template}"; then
            printf '%s|%s\n' "${code}" "${template}"
            return 0
        fi
    done < <(ovmf_pair_candidates "${secure_boot}")

    return 1
}

ovmf_first_matching_template() {
    local secure_boot=$1
    local code=$2
    local template

    while IFS= read -r template; do
        if [[ -f "${template}" ]] && ovmf_vars_matches_code "${code}" "${template}"; then
            printf '%s\n' "${template}"
            return 0
        fi
    done < <(ovmf_template_candidates_for_code "${secure_boot}" "${code}")

    return 1
}

ovmf_first_matching_code() {
    local secure_boot=$1
    local template=$2
    local code

    while IFS= read -r code; do
        if [[ -f "${code}" ]] && ovmf_vars_matches_code "${code}" "${template}"; then
            printf '%s\n' "${code}"
            return 0
        fi
    done < <(ovmf_code_candidates_for_template "${secure_boot}" "${template}")

    return 1
}

ovmf_select_firmware() {
    local secure_boot=$1
    local requested_code=${2:-}
    local requested_template=${3:-}
    local pair

    ovmf_code=""
    ovmf_template=""

    if [[ -n "${requested_code}" ]]; then
        ovmf_code=${requested_code}
        if [[ -n "${requested_template}" ]]; then
            ovmf_template=${requested_template}
        elif [[ -f "${ovmf_code}" ]]; then
            ovmf_template=$(ovmf_first_matching_template "${secure_boot}" "${ovmf_code}" || true)
        fi
    elif [[ -n "${requested_template}" ]]; then
        ovmf_template=${requested_template}
        if [[ -f "${ovmf_template}" ]]; then
            ovmf_code=$(ovmf_first_matching_code "${secure_boot}" "${ovmf_template}" || true)
        fi
    else
        pair=$(ovmf_first_matching_pair "${secure_boot}" || true)
        if [[ -n "${pair}" ]]; then
            ovmf_code=${pair%%|*}
            ovmf_template=${pair#*|}
        fi
    fi
}

arm_secure_boot_cache_assets() {
    local output_dir="${cache_dir}/edk2-aarch64"
    local image=${ARM_FIRMWARE_IMAGE:-localhost/images:anatase}

    if ! command -v podman >/dev/null 2>&1; then
        printf 'Secure Boot capable AArch64 firmware was not found, and podman is unavailable to fetch it.\n' >&2
        return 1
    fi
    if ! podman image exists "${image}"; then
        image=registry.fedoraproject.org/fedora:44
    fi

    mkdir -p "${output_dir}"
    printf '==> Fetching Secure Boot capable AArch64 firmware from Fedora\n'
    podman run --rm \
        --volume "${output_dir}:/output:Z" \
        "${image}" \
        bash -ceu '
            dnf -y install edk2-aarch64 >/dev/null
            install -m 0644 \
                /usr/share/edk2/aarch64/QEMU_EFI.qemuvars.fd \
                /output/QEMU_EFI.qemuvars.fd
            install -m 0644 \
                /usr/share/edk2/aarch64/vars.secboot.json \
                /output/vars.secboot.json
        '
}

arm_secure_boot_select_firmware() {
    local requested_code=${1:-}
    local requested_template=${2:-}
    local directory

    arm_secure_boot_code=${requested_code}
    arm_secure_boot_template=${requested_template}

    if [[ -n "${arm_secure_boot_code}" || -n "${arm_secure_boot_template}" ]]; then
        return
    fi

    for directory in \
        /usr/share/edk2/aarch64 \
        "${cache_dir}/edk2-aarch64"; do
        if [[ -s "${directory}/QEMU_EFI.qemuvars.fd" && -s "${directory}/vars.secboot.json" ]]; then
            arm_secure_boot_code="${directory}/QEMU_EFI.qemuvars.fd"
            arm_secure_boot_template="${directory}/vars.secboot.json"
            return
        fi
    done

    arm_secure_boot_cache_assets
    arm_secure_boot_code="${cache_dir}/edk2-aarch64/QEMU_EFI.qemuvars.fd"
    arm_secure_boot_template="${cache_dir}/edk2-aarch64/vars.secboot.json"
}
