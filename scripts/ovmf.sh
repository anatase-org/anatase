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
