#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
identity_dir="${script_dir}/../../cards/base/identity"

browser_svg="${identity_dir}/browser.svg"
browser_outline_svg="${identity_dir}/browser-outline.svg"
letterhead_svg="${identity_dir}/letterhead-onwhite.svg"

if ! command -v rsvg-convert >/dev/null 2>&1; then
    echo "error: rsvg-convert is required" >&2
    exit 1
fi

if command -v magick >/dev/null 2>&1; then
    imagemagick=(magick)
elif command -v convert >/dev/null 2>&1; then
    imagemagick=(convert)
else
    echo "error: ImageMagick is required" >&2
    exit 1
fi

for source in "${browser_svg}" "${browser_outline_svg}" "${letterhead_svg}"; do
    if [[ ! -f "${source}" ]]; then
        echo "error: missing ${source}" >&2
        exit 1
    fi
done

cp -a "${browser_svg}" "${script_dir}/browser.svg"
cp -a "${browser_outline_svg}" "${script_dir}/browser-outline.svg"

for size in 16 24 32 48 64 128 256; do
    rsvg-convert \
        --width "${size}" \
        --height "${size}" \
        --page-width "${size}" \
        --page-height "${size}" \
        --keep-aspect-ratio \
        --format png \
        --output "${script_dir}/chromium-browser-${size}.png" \
        "${browser_svg}"
done

for size in 16 32; do
    rsvg-convert \
        --width "${size}" \
        --height "${size}" \
        --page-width "${size}" \
        --page-height "${size}" \
        --keep-aspect-ratio \
        --format png \
        --output "${script_dir}/browser-outline-${size}.png" \
        "${browser_outline_svg}"
    "${imagemagick[@]}" \
        "${script_dir}/browser-outline-${size}.png" \
        -fill "#5f6368" \
        -colorize 100 \
        "${script_dir}/browser-outline-${size}.png"
done

rsvg-convert \
    --width 272 \
    --height 92 \
    --page-width 272 \
    --page-height 92 \
    --keep-aspect-ratio \
    --format svg \
    --output "${script_dir}/new-tab-google-logo.svg" \
    "${letterhead_svg}"

python3 - "${browser_outline_svg}" "${script_dir}/browser-outline.icon" <<'PY'
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

source = Path(sys.argv[1])
target = Path(sys.argv[2])


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def parse_number_list(value):
    return [float(n) for n in re.findall(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", value)]


def parse_transform(value):
    transforms = []
    for name, args in re.findall(r"(matrix|translate)\(([^)]*)\)", value):
        nums = parse_number_list(args)
        if name == "matrix":
            if len(nums) != 6:
                raise SystemExit(f"unsupported matrix transform in {source}: {value}")
            transforms.append(tuple(nums))
        elif name == "translate":
            tx = nums[0]
            ty = nums[1] if len(nums) > 1 else 0.0
            transforms.append((1.0, 0.0, 0.0, 1.0, tx, ty))
    return transforms


def apply_matrix(point, matrix):
    x, y = point
    a, b, c, d, e, f = matrix
    return (a * x + c * y + e, b * x + d * y + f)


def apply_transforms(point, transforms):
    for matrix in reversed(transforms):
        point = apply_matrix(point, matrix)
    return point


token_re = re.compile(r"[AaCcHhLlMmQqSsTtVvZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


def parse_path(d, transforms):
    tokens = token_re.findall(d)
    index = 0
    command = None
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    out = []

    def has_number():
        return index < len(tokens) and not re.match(r"^[A-Za-z]$", tokens[index])

    def read_number():
        nonlocal index
        value = float(tokens[index])
        index += 1
        return value

    def read_point(relative):
        x = read_number()
        y = read_number()
        if relative:
            return (current[0] + x, current[1] + y)
        return (x, y)

    while index < len(tokens):
        if re.match(r"^[A-Za-z]$", tokens[index]):
            command = tokens[index]
            index += 1
        if command is None:
            raise SystemExit(f"path command missing in {source}")

        relative = command.islower()
        op = command.upper()

        if op == "M":
            point = read_point(relative)
            current = start = point
            out.append(("MOVE_TO", apply_transforms(point, transforms)))
            while has_number():
                point = read_point(relative)
                current = point
                out.append(("LINE_TO", apply_transforms(point, transforms)))
            command = "l" if relative else "L"
        elif op == "L":
            while has_number():
                point = read_point(relative)
                current = point
                out.append(("LINE_TO", apply_transforms(point, transforms)))
        elif op == "H":
            while has_number():
                x = read_number()
                if relative:
                    x += current[0]
                current = (x, current[1])
                out.append(("LINE_TO", apply_transforms(current, transforms)))
        elif op == "V":
            while has_number():
                y = read_number()
                if relative:
                    y += current[1]
                current = (current[0], y)
                out.append(("LINE_TO", apply_transforms(current, transforms)))
        elif op == "C":
            while has_number():
                c1 = read_point(relative)
                c2 = read_point(relative)
                end = read_point(relative)
                current = end
                out.append((
                    "CUBIC_TO",
                    apply_transforms(c1, transforms),
                    apply_transforms(c2, transforms),
                    apply_transforms(end, transforms),
                ))
        elif op == "Z":
            current = start
            out.append(("CLOSE",))
        else:
            raise SystemExit(f"unsupported path command {command} in {source}")

    return out


root = ET.parse(source).getroot()
view_box = parse_number_list(root.attrib["viewBox"])
if len(view_box) != 4:
    raise SystemExit(f"unsupported viewBox in {source}")
min_x, min_y, view_width, view_height = view_box

commands = []


def collect(element, transforms):
    transform = element.attrib.get("transform")
    if transform:
        transforms = [*transforms, *parse_transform(transform)]
    if local_name(element.tag) == "path" and element.attrib.get("d"):
        if commands:
            commands.append(("NEW_PATH",))
        commands.extend(parse_path(element.attrib["d"], transforms))
    for child in element:
        collect(child, transforms)


collect(root, [])
if not commands:
    raise SystemExit(f"no path commands found in {source}")


def fmt(value):
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    if text == "-0":
        return "0"
    return text


def emit_rep(size):
    scale = size / max(view_width, view_height)
    dx = -min_x * scale + (size - view_width * scale) / 2
    dy = -min_y * scale + (size - view_height * scale) / 2
    lines = [f"CANVAS_DIMENSIONS, {size},"]
    for command in commands:
        name = command[0]
        if name in ("NEW_PATH", "CLOSE"):
            lines.append(f"{name},")
            continue
        coords = []
        for x, y in command[1:]:
            coords.extend((fmt(x * scale + dx), fmt(y * scale + dy)))
        lines.append(f"{name}, {', '.join(coords)},")
    return lines


target.write_text(
    "// Generated by generate_logo.sh from browser-outline.svg.\n"
    "// Use of this source code is governed by Chromium's BSD-style license.\n\n"
    + "\n".join(emit_rep(32))
    + "\n"
    + "\n".join(emit_rep(16))
    + "\n"
)
PY
