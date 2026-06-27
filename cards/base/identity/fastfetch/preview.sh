#!/usr/bin/env bash
set -euo pipefail

logo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

sed \
    -e $'s/\\$1/\033[38;5;11m/g' \
    -e $'s/\\$2/\033[38;5;15m/g' \
    -e $'s/\\$3/\033[38;5;7m/g' \
    -e $'s/\\$4/\033[38;5;0m/g' \
    -e $'s/\\$5/\033[38;5;8m/g' \
    "${logo_dir}/logo.txt"
printf '\033[0m\n'
