#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


INFO_LABEL = "org.anatase.ludos.info"
VERSION_LABEL = "org.opencontainers.image.version"
REVISION_LABEL = "org.opencontainers.image.revision"
SOURCE_LABEL = "org.opencontainers.image.source"

FEDORA_RELEASE = re.compile(r"\.fc\d+")
GIT_HASH = re.compile(r"(\+git\.\d+\.g)([0-9a-f]{5})[0-9a-f]+")
MAJOR_PACKAGES = {
    "Kernel": ("kernel-core", "kernel-common"),
    "Firmware": ("atheros-firmware",),
    "Mesa": ("mesa-filesystem",),
    "Nvidia": ("nvidia-driver",),
    "Gamescope": ("gamescope",),
    "KDE": ("plasma-desktop",),
    "HHD": ("hhd",),
    "Spaces": ("spaces",),
}


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def labels(manifest: dict[str, Any]) -> dict[str, str]:
    return manifest["Labels"]


def clean_version(version: str) -> str:
    version = version.replace(".ludos", "")
    version = FEDORA_RELEASE.sub("", version)
    return GIT_HASH.sub(r"\1\2", version)


def packages(manifest: dict[str, Any]) -> dict[str, str]:
    info = json.loads(labels(manifest)[INFO_LABEL])
    return {
        name: clean_version(version)
        for name, version in info["packages"].items()
    }


def version(manifest: dict[str, Any]) -> str:
    return labels(manifest)[VERSION_LABEL]


def format_version(previous: str | None, current: str | None) -> str:
    if previous is None:
        return current or ""
    if current is None:
        return previous
    if previous == current:
        return current
    return f"{previous} ➡️ {current}"


def major_package_version(
    package_versions: dict[str, str], package_names: tuple[str, ...]
) -> str | None:
    return next(
        (package_versions[name] for name in package_names if name in package_versions),
        None,
    )


def major_packages(previous: dict[str, str], current: dict[str, str]) -> str:
    rows = []
    for display_name, package_names in MAJOR_PACKAGES.items():
        old = major_package_version(previous, package_names)
        new = major_package_version(current, package_names)
        if old is None and new is None:
            continue
        rows.append(f"| **{display_name}** | {format_version(old, new)} |")

    if not rows:
        return ""
    return "### Major packages\n\n| Name | Version |\n| --- | --- |\n" + "\n".join(rows)


def major_packages_for_images(
    images: Sequence[tuple[str, dict[str, Any] | None, dict[str, Any]]],
) -> str:
    package_sets = [
        (
            name,
            packages(previous) if previous is not None else {},
            packages(current),
        )
        for name, previous, current in images
    ]
    rows = []
    for display_name, package_names in MAJOR_PACKAGES.items():
        if not any(
            major_package_version(previous, package_names) is not None
            or major_package_version(current, package_names) is not None
            for _name, previous, current in package_sets
        ):
            continue
        image_versions = [
            (
                name,
                format_version(
                    major_package_version(previous, package_names),
                    major_package_version(current, package_names),
                ),
            )
            for name, previous, current in package_sets
        ]
        versions = {value for _name, value in image_versions}
        if len(versions) == 1:
            value = image_versions[0][1]
        else:
            value = "<br>".join(
                f"**{name}:** {image_version or 'Not installed'}"
                for name, image_version in image_versions
            )
        rows.append(f"| **{display_name}** | {value} |")

    if not rows:
        return ""
    return (
        "### Major packages\n\n"
        "| Name | Version |\n"
        "| --- | --- |\n"
        + "\n".join(rows)
    )


def package_changes(
    previous: dict[str, str], current: dict[str, str], heading: str = "Packages"
) -> str:
    rows = []
    seen_versions: set[tuple[str | None, str | None]] = set()
    major_package_names = {
        package_name
        for package_names in MAJOR_PACKAGES.values()
        for package_name in package_names
    }
    major_versions = {
        versions.get(package_name)
        for versions in (previous, current)
        for package_name in major_package_names
    } - {None}

    for name in sorted(previous.keys() | current.keys()):
        old = previous.get(name)
        new = current.get(name)
        change = (old, new)

        if old == new or name in major_package_names:
            continue
        if old in major_versions or new in major_versions:
            continue
        if change in seen_versions:
            continue
        seen_versions.add(change)

        if old is None:
            rows.append(f"| ✨ | {name} | | {new} |")
        elif new is None:
            rows.append(f"| ❌ | {name} | {old} | |")
        else:
            rows.append(f"| 🔄 | {name} | {old} | {new} |")

    if not rows:
        return ""
    return (
        f"### {heading}\n\n"
        "| | Name | Previous | New |\n"
        "| --- | --- | --- | --- |\n"
        + "\n".join(rows)
    )


def package_changes_for_images(
    images: Sequence[tuple[str, dict[str, Any] | None, dict[str, Any]]],
) -> str:
    sections = []
    for name, previous, current in images:
        if previous is None:
            continue
        changes = package_changes(
            packages(previous),
            packages(current),
            heading=f"Packages ({name})",
        )
        if changes:
            sections.append(changes)
    return "\n\n".join(sections)


def commits(previous: dict[str, Any], current: dict[str, Any]) -> str:
    previous_revision = labels(previous)[REVISION_LABEL]
    current_revision = labels(current)[REVISION_LABEL]
    if previous_revision == current_revision:
        return ""

    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", previous_revision, current_revision],
        capture_output=True,
        text=True,
    )
    if ancestry.returncode != 0:
        print(
            "Skipping commit changelog because the previous revision is not "
            "available in the current commit history: "
            f"{previous_revision} -> {current_revision}",
            file=sys.stderr,
        )
        return ""

    result = subprocess.run(
        [
            "git",
            "log",
            "--pretty=format:%H%x00%an%x00%s",
            f"{previous_revision}..{current_revision}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    source = labels(current).get(SOURCE_LABEL, "").rstrip("/")
    rows = []
    for line in result.stdout.splitlines():
        commit_hash, author, subject = line.split("\0", 2)
        if subject.lower().startswith("merge"):
            continue
        author = author.split(maxsplit=1)[0].replace("|", "\\|")
        subject = subject.replace("|", "\\|")
        short_hash = commit_hash[:6]
        commit = f"[{short_hash}]({source}/commit/{commit_hash})" if source else short_hash
        rows.append(f"| **{commit}** | {author} | {subject} |")

    if not rows:
        return ""
    return (
        "### Commits\n\n"
        "| Commit | Author | Subject |\n"
        "| --- | --- | --- |\n"
        + "\n".join(rows)
    )


def changelog(
    previous: dict[str, Any],
    current: dict[str, Any],
    channel: str | None = None,
    *,
    image_name: str = "Image",
    additional_images: Sequence[tuple[str, dict[str, Any] | None, dict[str, Any]]] = (),
) -> str:
    previous_version = version(previous)
    images = ((image_name, previous, current), *additional_images)

    sections = [
        (
            f"From previous {f'`{channel.lower()}` ' if channel else ''}version "
            f"`{previous_version}` there are the following changes. Only one package name is shown for each version."
        ),
        major_packages_for_images(images),
        commits(previous, current),
        package_changes_for_images(images),
    ]
    return "\n\n".join(section for section in sections if section) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an Anatase changelog from two skopeo inspect manifests."
    )
    parser.add_argument("previous", type=Path, help="Previous manifest JSON")
    parser.add_argument("current", type=Path, help="Current manifest JSON")
    parser.add_argument(
        "--image-name",
        default="Image",
        help="Name shown for the positional manifest pair",
    )
    parser.add_argument(
        "--image",
        action="append",
        nargs=3,
        default=[],
        metavar=("NAME", "PREVIOUS", "CURRENT"),
        help=(
            "Additional named image pair. Use '-' for PREVIOUS when that image "
            "did not exist in the previous release."
        ),
    )
    parser.add_argument("--channel", help="Release channel shown in the introduction")
    args = parser.parse_args()

    additional_images = tuple(
        (
            name,
            None if previous == "-" else load_manifest(Path(previous)),
            load_manifest(Path(current)),
        )
        for name, previous, current in args.image
    )
    print(
        changelog(
            load_manifest(args.previous),
            load_manifest(args.current),
            args.channel,
            image_name=args.image_name,
            additional_images=additional_images,
        ),
        end="",
    )


if __name__ == "__main__":
    main()
