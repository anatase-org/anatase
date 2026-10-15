"""Validate all architecture inputs before publishing or promoting image indexes."""

import argparse
import json
import os
from pathlib import Path
import subprocess


IMAGE_NAMES = ("anatase", "base")
ARCHES = {"x86_64": "amd64", "aarch64": "arm64"}
VERSION_LABEL = "org.opencontainers.image.version"


def publication_images(outputs: dict[str, list[dict]]) -> list[dict[str, str]]:
    by_arch = {}
    for arch in ARCHES:
        entries = outputs[arch]
        by_arch[arch] = {}
        for entry in entries:
            name = entry["name"]
            version = entry.get("version")
            if name not in IMAGE_NAMES or name in by_arch[arch] or not version:
                raise ValueError(f"Invalid image metadata for {arch}: {entry}")
            by_arch[arch][name] = version
    if by_arch["x86_64"] != by_arch["aarch64"]:
        raise ValueError("Image names and versions must match across architecture outputs")
    return [
        {"name": name, "version": by_arch["x86_64"][name]}
        for name in IMAGE_NAMES
        if name in by_arch["x86_64"]
    ]


def inspect_image(name: str, tag: str, arch: str) -> dict:
    result = subprocess.run(
        [
            "skopeo", "--override-arch", ARCHES[arch], "inspect", "--no-tags",
            f"docker://i.anatase.org/{name}:{tag}",
        ],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def validate_images(images: list[dict[str, str]], *, prefix: str = "", tag: str = "") -> None:
    for image in images:
        for arch, oci_arch in ARCHES.items():
            source_tag = tag or f"{prefix}{arch}"
            source = inspect_image(image["name"], source_tag, arch)
            if (
                source.get("Architecture") != oci_arch
                or source.get("Labels", {}).get(VERSION_LABEL) != image["version"]
            ):
                raise ValueError(
                    f"{image['name']}:{source_tag} does not match "
                    f"{oci_arch} version {image['version']}"
                )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "promote"))
    args = parser.parse_args()
    if args.mode == "build":
        images = publication_images({
            "x86_64": json.loads(os.environ["X86_IMAGES"]),
            "aarch64": json.loads(os.environ["ARM_IMAGES"]),
        })
        validate_images(images, prefix=os.environ.get("LUDOS_INTERIM_PREFIX", ""))
    else:
        images = [
            {
                "name": name,
                "version": inspect_image(name, "rolling", "x86_64")["Labels"][VERSION_LABEL],
            }
            for name in IMAGE_NAMES
        ]
        if any(not image["version"] for image in images):
            raise ValueError("Rolling images must have a version label")
        validate_images(images, tag="rolling")
    Path("publish-images.json").write_text(json.dumps(images) + "\n")
    if "GITHUB_OUTPUT" in os.environ:
        anatase = next((image for image in images if image["name"] == "anatase"), None)
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"anatase={str(anatase is not None).lower()}\n")
            output.write(f"version={anatase['version'] if anatase else ''}\n")


if __name__ == "__main__":
    main()
