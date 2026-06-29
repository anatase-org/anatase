#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

if [[ $# -gt 1 ]]; then
    printf 'usage: %s [flatpak-dir]\n' "${0##*/}" >&2
    exit 2
fi

MANIFEST=${MANIFEST:-anatase.yml}
VM_SSH=${VM_SSH:-vm}
REMOTE_DIR=${REMOTE_DIR:-/var/tmp/anatase-flatpaks}

if [[ -n "${LUDOS:-}" ]]; then
    ludos=("${LUDOS}")
elif [[ -x "${repo_root}/venv/bin/ludos" ]]; then
    ludos=("${repo_root}/venv/bin/ludos")
else
    ludos=(ludos)
fi

log() {
    printf '==> %s\n' "$*"
}

read_flatpak_cards() {
    python3 - "${MANIFEST}" "$@" <<'PY'
from pathlib import Path
import sys
import yaml

manifest_path = Path(sys.argv[1])
root = manifest_path.resolve().parent

if len(sys.argv) > 2:
    refs = sys.argv[2:]
else:
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f) or {}
    refs = manifest.get("flatpaks") or []
    if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
        raise SystemExit(f"{manifest_path}: 'flatpaks' must be a list of strings")
    if not refs:
        raise SystemExit(f"{manifest_path}: 'flatpaks' must contain at least one item")

for ref in refs:
    path = Path(ref)
    if not path.is_absolute():
        path = root / path
    if path.is_dir():
        for candidate in (path / "card.yaml", path / "card.yml"):
            if candidate.exists():
                card = candidate
                break
        else:
            card = path / "card.yaml"
    elif path.suffix in (".yaml", ".yml"):
        card = path
    else:
        card = path / "card.yaml"
    if not card.exists():
        raise SystemExit(f"Flatpak card not found: {card}")

    with card.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    try:
        app_id = data["flatpak"]["id"]
    except Exception:
        raise SystemExit(f"{card}: missing flatpak.id")
    if not isinstance(app_id, str) or not app_id.strip():
        raise SystemExit(f"{card}: missing flatpak.id")

    print(f"{ref}\t{card}\t{app_id.strip()}")
PY
}

install_app_image() {
    local app_id=$1
    local image_name
    image_name=$(python3 - "${app_id}" <<'PY'
import sys

print(sys.argv[1].lower())
PY
)
    local latest_image="localhost/${image_name}:latest"

    if ! podman image exists "${latest_image}"; then
        printf 'Expected image not found after build: %s\n' "${latest_image}" >&2
        exit 1
    fi

    local branch
    branch=$(podman image inspect "${latest_image}" --format '{{ index .Config.Labels "org.anatase.flatpak.branch" }}')
    branch=${branch:-latest}
    local archive_dir="${repo_root}/cache/flatpaks"
    local archive="${archive_dir}/${app_id}-${branch}.oci"
    local remote_archive="${REMOTE_DIR}/${app_id}-${branch}.oci"

    mkdir -p "${archive_dir}"

    log "Exporting ${latest_image} to ${archive}"
    podman save --format oci-archive -o "${archive}" "${latest_image}"

    log "Sending ${archive} to ${VM_SSH}:${remote_archive}"
    ssh "${VM_SSH}" "mkdir -p '${REMOTE_DIR}'"
    ssh "${VM_SSH}" "cat > '${remote_archive}'" < "${archive}"

    log "Installing ${app_id} on ${VM_SSH}"
    ssh "${VM_SSH}" "flatpak install --system -y --noninteractive --reinstall --no-deps --image 'oci-archive:${remote_archive}'"

    log "Installed ${app_id} (${branch})"
}

register_anatase_runtime() {
    log "Registering Anatase Flatpak runtime on ${VM_SSH}"
    ssh "${VM_SSH}" '
        set -e
        if systemctl cat anatase-flatpak-extensions.service >/dev/null 2>&1; then
            sudo systemctl restart anatase-flatpak-extensions.service
        elif [ -x /usr/libexec/anatase-flatpak-extensions ]; then
            sudo /usr/libexec/anatase-flatpak-extensions start
        else
            printf "%s\n" "Anatase Flatpak runtime helper is not installed" >&2
            exit 1
        fi
    '
}

declare -a app_ids=()
flatpak_cards=

if [[ $# -eq 0 ]]; then
    flatpak_cards=$(read_flatpak_cards)
    while IFS=$'\t' read -r flatpak_ref _card app_id; do
        app_ids+=("${app_id}")
    done <<< "${flatpak_cards}"

    log "Building flatpaks from ${MANIFEST}"
    "${ludos[@]}" build "${MANIFEST}" --flatpaks
else
    flatpak_dir=$1
    flatpak_cards=$(read_flatpak_cards "${flatpak_dir}")
    while IFS=$'\t' read -r flatpak_ref _card app_id; do
        app_ids+=("${app_id}")
    done <<< "${flatpak_cards}"

    log "Building ${flatpak_dir}"
    "${ludos[@]}" build "${MANIFEST}" --flatpak "${flatpak_dir}"
fi

for app_id in "${app_ids[@]}"; do
    install_app_image "${app_id}"
done

register_anatase_runtime
