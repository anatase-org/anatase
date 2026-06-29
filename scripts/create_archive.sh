#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
archive_dir="${script_dir}/archives"
stage_dir="${archive_dir}/.build"

require() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1" >&2
        exit 1
    fi
}

require bzip2
require gzip
require python3
require tar
require zip
require 7z

rm -rf -- "${stage_dir}"
mkdir -p -- "${stage_dir}/src" "${archive_dir}"
printf 'Hello world\n' > "${stage_dir}/src/text.tx"

tar -C "${stage_dir}/src" -cjf "${archive_dir}/test.tar.bz2" text.tx
tar -C "${stage_dir}/src" -czf "${archive_dir}/test.tar.gz" text.tx
bzip2 -c "${stage_dir}/src/text.tx" > "${archive_dir}/test.bz2"
gzip -c -n "${stage_dir}/src/text.tx" > "${archive_dir}/test.gz"
tar -C "${stage_dir}/src" -cf "${archive_dir}/test.tar" text.tx
tar -C "${stage_dir}/src" -cjf "${archive_dir}/test.tbz2" text.tx
tar -C "${stage_dir}/src" -czf "${archive_dir}/test.tgz" text.tx
(cd "${stage_dir}/src" && zip -q -X "${archive_dir}/test.zip" text.tx)
(cd "${stage_dir}/src" && 7z a -t7z -mx=9 "${archive_dir}/test.7z" text.tx >/dev/null)

python3 - "${stage_dir}/src/text.tx" "${archive_dir}/test.rar" <<'PY'
from pathlib import Path
import binascii
import struct
import sys

source = Path(sys.argv[1])
out = Path(sys.argv[2])
data = source.read_bytes()
name = source.name.encode()

def hdr_crc(header_without_crc: bytes) -> bytes:
    return struct.pack("<H", binascii.crc32(header_without_crc) & 0xFFFF)

sig = b"Rar!\x1a\x07\x00"
main_body = struct.pack("<BHHHI", 0x73, 0, 13, 0, 0)
file_body = b"".join(
    [
        struct.pack("<BHH", 0x74, 0, 32 + len(name)),
        struct.pack("<II", len(data), len(data)),
        struct.pack("<B", 3),
        struct.pack("<I", binascii.crc32(data) & 0xFFFFFFFF),
        struct.pack("<I", 0),
        struct.pack("<B", 20),
        struct.pack("<B", 0x30),
        struct.pack("<H", len(name)),
        struct.pack("<I", 0o100644),
        name,
    ]
)
end_body = struct.pack("<BHH", 0x7B, 0, 7)
out.write_bytes(
    sig
    + hdr_crc(main_body)
    + main_body
    + hdr_crc(file_body)
    + file_body
    + data
    + hdr_crc(end_body)
    + end_body
)
PY

python3 - "${stage_dir}/src/text.tx" "${archive_dir}/test.Z" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
out = Path(sys.argv[2])

def compress_lzw(data: bytes, maxbits: int = 16, block_mode: bool = True) -> bytes:
    if not data:
        return bytes([0x1F, 0x9D, (0x80 if block_mode else 0) | maxbits])

    next_code = 257 if block_mode else 256
    width = 9
    max_code_for_width = (1 << width) - 1
    table = {bytes([i]): i for i in range(256)}
    bitbuf = 0
    bitcount = 0
    output = bytearray([0x1F, 0x9D, (0x80 if block_mode else 0) | maxbits])

    def emit(code: int) -> None:
        nonlocal bitbuf, bitcount
        bitbuf |= code << bitcount
        bitcount += width
        while bitcount >= 8:
            output.append(bitbuf & 0xFF)
            bitbuf >>= 8
            bitcount -= 8

    w = bytes([data[0]])
    for byte in data[1:]:
        c = bytes([byte])
        wc = w + c
        if wc in table:
            w = wc
            continue
        emit(table[w])
        if next_code < (1 << maxbits):
            table[wc] = next_code
            next_code += 1
            if next_code > max_code_for_width and width < maxbits:
                width += 1
                max_code_for_width = (1 << width) - 1
        w = c

    emit(table[w])
    if bitcount:
        output.append(bitbuf & 0xFF)
    return bytes(output)

out.write_bytes(compress_lzw(source.read_bytes()))
PY

rm -rf -- "${stage_dir}"
echo "Created archives in ${archive_dir}"
