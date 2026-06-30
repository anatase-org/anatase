#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

VM_SSH=${VM_SSH:-vm}
FLATPAK_REMOTE=${FLATPAK_REMOTE:-anatase}
DESKTOP_USER=${DESKTOP_USER:-asfd}

log() {
    printf '==> %s\n' "$*"
}

log "Refreshing ${FLATPAK_REMOTE} metadata on ${VM_SSH}"
ssh "${VM_SSH}" bash -s -- "${FLATPAK_REMOTE}" "${DESKTOP_USER}" <<'EOF'
set -euo pipefail

flatpak_remote=$1
desktop_user=$2

if [[ -n "${desktop_user}" ]] && id -u "${desktop_user}" >/dev/null 2>&1; then
    desktop_uid=$(id -u "${desktop_user}")
    desktop_home=$(getent passwd "${desktop_user}" | cut -d: -f6)

    pkill -u "${desktop_user}" plasma-discover || true
    runuser -u "${desktop_user}" -- \
        env "XDG_RUNTIME_DIR=/run/user/${desktop_uid}" \
        appstreamcli refresh-cache --force || true
    rm -rf "${desktop_home}/.cache/discover"
fi

flatpak --system update --appstream "${flatpak_remote}"
appstreamcli refresh-cache --force || true

flatpak --system remote-ls --app "${flatpak_remote}" | sed -n '1,20p'
stat -c '%y %n' \
    "/var/lib/flatpak/appstream/${flatpak_remote}/x86_64/.timestamp" \
    "/var/lib/flatpak/appstream/${flatpak_remote}/x86_64/appstream.xml.gz" \
    2>/dev/null || true
EOF
