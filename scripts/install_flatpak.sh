#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "${script_dir}/.." && pwd)
cd "${repo_root}"

usage() {
    printf 'usage: %s [--arch x86_64|aarch64] [flatpak-dir]\n' "${0##*/}" >&2
    exit 2
}

arch=
if [[ ${1:-} == --arch ]]; then
    [[ $# -ge 2 ]] || usage
    arch=$2
    shift 2
fi
[[ $# -le 1 ]] || usage

case ${arch} in
    amd64) arch=x86_64 ;;
    arm64) arch=aarch64 ;;
    ''|x86_64|aarch64) ;;
    *) usage ;;
esac

build_arch_args=()
if [[ -n ${arch} ]]; then
    build_arch_args=(--arch "${arch}")
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
    python3 - "${MANIFEST}" "${arch}" "$@" <<'PY'
from pathlib import Path
import datetime
import platform
import sys
import yaml

manifest_path = Path(sys.argv[1])
arch_override = sys.argv[2]
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
if arch_override:
    manifest_env["arch"] = arch_override
manifest_env["version"] = datetime.date.today().strftime("%Y%m%d")
manifest_env["releasever"] = substitute(manifest["releasever"], manifest_env)
manifest_env["arch"] = substitute(manifest_env.get("arch", ""), manifest_env)
manifest_env["arch"] = {"amd64": "x86_64", "arm64": "aarch64"}.get(
    manifest_env["arch"], manifest_env["arch"]
)
manifest_env = {
    key: substitute(value, manifest_env)
    for key, value in manifest_env.items()
}
distro = substitute(manifest["distro"], manifest_env)
if "$" in distro:
    raise SystemExit(f"{manifest_path}: could not resolve distro '{distro}'")
repository = f"localhost/{local_prefix}flatpaks"

if len(sys.argv) > 3:
    refs = sys.argv[3:]
else:
    configured = manifest.get("flatpaks") or []
    if isinstance(configured, list):
        by_arch = {"*": []}
        for item in configured:
            if isinstance(item, str):
                by_arch["*"].append(item)
            elif isinstance(item, dict):
                for key, values in item.items():
                    if (
                        not isinstance(key, str)
                        or not isinstance(values, list)
                        or not all(isinstance(value, str) for value in values)
                    ):
                        raise SystemExit(f"{manifest_path}: invalid architecture entry in 'flatpaks'")
                    by_arch.setdefault(key, []).extend(values)
            else:
                raise SystemExit(f"{manifest_path}: invalid entry in 'flatpaks'")
    elif isinstance(configured, dict):
        by_arch = configured
        if not all(
            isinstance(key, str)
            and isinstance(values, list)
            and all(isinstance(value, str) for value in values)
            for key, values in by_arch.items()
        ):
            raise SystemExit(f"{manifest_path}: invalid architecture entry in 'flatpaks'")
    else:
        raise SystemExit(f"{manifest_path}: 'flatpaks' must be a list or architecture mapping")
    refs = list(dict.fromkeys(by_arch.get("*", []) + by_arch.get(manifest_env["arch"], [])))
    if not refs:
        raise SystemExit(f"{manifest_path}: 'flatpaks' has no entries for {manifest_env['arch']}")

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
        for candidate in (path.with_suffix(".yml"), path.with_suffix(".yaml")):
            if candidate.exists():
                card = candidate
                break
        else:
            card = path.with_suffix(".yml")
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

    if card.name in ("card.yaml", "card.yml"):
        app_name = card.parent.name
    else:
        app_name = card.stem
    image = f"{repository}:{app_name}"
    print(f"{ref}\t{card}\t{app_id.strip()}\t{app_name}\t{image}\t{manifest_env['arch']}")
PY
}

install_app_image() {
    local app_id=$1
    local image=$2
    local target_arch=$3

    if ! podman image exists "${image}"; then
        printf 'Expected image not found after build: %s\n' "${image}" >&2
        exit 1
    fi

    local image_arch expected_image_arch
    image_arch=$(podman image inspect "${image}" --format '{{ .Architecture }}')
    case ${target_arch} in
        aarch64) expected_image_arch=arm64 ;;
        x86_64) expected_image_arch=amd64 ;;
        *) printf 'Unsupported Flatpak architecture: %s\n' "${target_arch}" >&2; exit 1 ;;
    esac
    if [[ ${image_arch} != "${expected_image_arch}" ]]; then
        printf 'Image %s has architecture %s; expected %s\n' \
            "${image}" "${image_arch}" "${expected_image_arch}" >&2
        exit 1
    fi

    local branch
    branch=$(podman image inspect "${image}" --format '{{ index .Config.Labels "org.anatase.flatpak.branch" }}')
    branch=${branch:-latest}
    local remote_archive="${REMOTE_DIR}/install-flatpak.oci"

    log "Sending ${image} to ${VM_SSH}:${remote_archive}"
    ssh "${VM_SSH}" "mkdir -p '${REMOTE_DIR}'"
    if ! podman save --format oci-archive "${image}" \
        | ssh "${VM_SSH}" "cat > '${remote_archive}'"; then
        ssh "${VM_SSH}" "rm -f '${remote_archive}'" || true
        return 1
    fi

    log "Installing ${app_id} on ${VM_SSH}"
    ssh "${VM_SSH}" "archive='${remote_archive}'; trap 'rm -f \"\$archive\"' EXIT; sudo flatpak install --system -y --noninteractive --reinstall --no-deps --image \"oci-archive:\$archive\""

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
    "${ludos[@]}" build "${MANIFEST}" "${build_arch_args[@]}" --flatpaks
else
    flatpak_dir=$1
    flatpak_cards=$(read_flatpak_cards "${flatpak_dir}")
    while IFS= read -r flatpak_row; do
        flatpak_rows+=("${flatpak_row}")
    done <<< "${flatpak_cards}"

    log "Building ${flatpak_dir}"
    "${ludos[@]}" build "${MANIFEST}" "${build_arch_args[@]}" --flatpak "${flatpak_dir}"
fi

for flatpak_row in "${flatpak_rows[@]}"; do
    IFS=$'\t' read -r _flatpak_ref _card app_id app_name image target_arch <<< "${flatpak_row}"
    install_app_image "${app_id}" "${image}" "${target_arch}"
done

register_anatase_runtime
