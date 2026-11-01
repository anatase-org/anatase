#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec "${PYTHON:-python3}" "${repo_root}/scripts/iso-test/host.py" "$@"
