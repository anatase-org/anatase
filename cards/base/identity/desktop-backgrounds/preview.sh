#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

outdir=svgs
mkdir -p "${outdir}"
rm -f "${outdir}"/*.svg

apply_palette() {
  local palette=$1
  local source_svg=$2
  local output_svg=$3
  local key value

  cp -p "${source_svg}" "${output_svg}"

  while IFS='=' read -r key value; do
    case "${key}" in
      ""|\#*) continue ;;
    esac
    sed -i "s|@${key}@|${value}|g" "${output_svg}"
  done < "${palette}"

  if grep -Eq '@[A-Z0-9_]+@' "${output_svg}"; then
    echo "Unresolved palette token in ${output_svg}" >&2
    grep -nE '@[A-Z0-9_]+@' "${output_svg}" >&2
    exit 1
  fi

  if command -v xmllint >/dev/null 2>&1; then
    xmllint --noout "${output_svg}"
  fi
}

for source_svg in anatase-*.svg; do
  name=${source_svg%.svg}
  apply_palette palette-day "${source_svg}" "${outdir}/${name}-day.svg"
  apply_palette palette-night "${source_svg}" "${outdir}/${name}-night.svg"
done

printf 'Rendered preview SVGs under %s/%s\n' "$(pwd)" "${outdir}"
