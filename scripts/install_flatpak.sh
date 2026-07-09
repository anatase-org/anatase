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
import datetime
import platform
import sys
import yaml

manifest_path = Path(sys.argv[1])
root = manifest_path.resolve().parent

def load_dotenv(path):
    if not path.exists():
        return {}
    values = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise SystemExit(f"{path}:{line_number}: expected KEY=VALUE")
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values

def substitute(value, variables):
    value = str(value)
    for key, replacement in variables.items():
        value = value.replace(f"${key}", replacement)
    return value

with manifest_path.open("r", encoding="utf-8") as f:
    manifest = yaml.safe_load(f) or {}

manifest_env = {"arch": platform.machine()}
manifest_env.update(
    {key: str(value) for key, value in (manifest.get("env") or {}).items()}
)
local_values = load_dotenv(root / ".env")
local_prefix = local_values.pop(
    "local_prefix",
    str(manifest.get("local_prefix") or ""),
)
manifest_env.update(local_values)
manifest_env["version"] = datetime.date.today().strftime("%Y%m%d")
manifest_env["releasever"] = substitute(manifest["releasever"], manifest_env)
manifest_env["arch"] = substitute(manifest_env.get("arch", ""), manifest_env)
manifest_env = {
    key: substitute(value, manifest_env)
    for key, value in manifest_env.items()
}
distro = substitute(manifest["distro"], manifest_env)
if "$" in distro:
    raise SystemExit(f"{manifest_path}: could not resolve distro '{distro}'")
repository = f"localhost/{local_prefix}flatpaks"

if len(sys.argv) > 2:
    refs = sys.argv[2:]
else:
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

    app_name = card.parent.name
    image = f"{repository}:{app_name}"
    print(f"{ref}\t{card}\t{app_id.strip()}\t{app_name}\t{image}")
PY
}

install_app_image() {
    local app_id=$1
    local app_name=$2
    local image=$3

    if ! podman image exists "${image}"; then
        printf 'Expected image not found after build: %s\n' "${image}" >&2
        exit 1
    fi

    local branch
    branch=$(podman image inspect "${image}" --format '{{ index .Config.Labels "org.anatase.flatpak.branch" }}')
    branch=${branch:-latest}
    local archive_dir="${repo_root}/cache/flatpaks"
    local archive="${archive_dir}/${app_name}-${branch}.oci"
    local remote_archive="${REMOTE_DIR}/${app_name}-${branch}.oci"

    mkdir -p "${archive_dir}"

    log "Exporting ${image} to ${archive}"
    podman save --format oci-archive -o "${archive}" "${image}"

    log "Sending ${archive} to ${VM_SSH}:${remote_archive}"
    ssh "${VM_SSH}" "mkdir -p '${REMOTE_DIR}'"
    ssh "${VM_SSH}" "cat > '${remote_archive}'" < "${archive}"

    log "Installing ${app_id} on ${VM_SSH}"
    ssh "${VM_SSH}" "sudo flatpak install --system -y --noninteractive --reinstall --no-deps --image 'oci-archive:${remote_archive}'"

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

declare -a flatpak_rows=()
flatpak_cards=

if [[ $# -eq 0 ]]; then
    flatpak_cards=$(read_flatpak_cards)
    while IFS= read -r flatpak_row; do
        flatpak_rows+=("${flatpak_row}")
    done <<< "${flatpak_cards}"

    log "Building flatpaks from ${MANIFEST}"
    "${ludos[@]}" build "${MANIFEST}" --flatpaks
else
    flatpak_dir=$1
    flatpak_cards=$(read_flatpak_cards "${flatpak_dir}")
    while IFS= read -r flatpak_row; do
        flatpak_rows+=("${flatpak_row}")
    done <<< "${flatpak_cards}"

    log "Building ${flatpak_dir}"
    "${ludos[@]}" build "${MANIFEST}" --flatpak "${flatpak_dir}"
fi

for flatpak_row in "${flatpak_rows[@]}"; do
    IFS=$'\t' read -r _flatpak_ref _card app_id app_name image <<< "${flatpak_row}"
    install_app_image "${app_id}" "${app_name}" "${image}"
done

register_anatase_runtime
