#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


INFO_LABEL = "org.anatase.ludos.info"
VERSION_LABEL = "org.opencontainers.image.version"
REVISION_LABEL = "org.opencontainers.image.revision"
SOURCE_LABEL = "org.opencontainers.image.source"

FEDORA_RELEASE = re.compile(r"\.fc\d+")
GIT_HASH = re.compile(r"(\+git\.\d+\.g)([0-9a-f]{5})[0-9a-f]+")
MAJOR_PACKAGES = {
    "Kernel": "kernel-core",
    "Firmware": "atheros-firmware",
    "Mesa": "mesa-filesystem",
    "Nvidia": "nvidia-driver",
    "Gamescope": "gamescope",
    "KDE": "plasma-desktop",
    "HHD": "hhd",
    "Spaces": "spaces",
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


def major_packages(previous: dict[str, str], current: dict[str, str]) -> str:
    rows = []
    for display_name, package_name in MAJOR_PACKAGES.items():
        if package_name not in previous and package_name not in current:
            continue
        rows.append(
            f"| **{display_name}** | "
            f"{format_version(previous.get(package_name), current.get(package_name))} |"
        )

    if not rows:
        return ""
    return "### Major packages\n\n| Name | Version |\n| --- | --- |\n" + "\n".join(rows)


def package_changes(previous: dict[str, str], current: dict[str, str]) -> str:
    rows = []
    seen_versions: set[tuple[str | None, str | None]] = set()
    major_versions = {
        versions.get(package_name)
        for versions in (previous, current)
        for package_name in MAJOR_PACKAGES.values()
    } - {None}

    for name in sorted(previous.keys() | current.keys()):
        old = previous.get(name)
        new = current.get(name)
        change = (old, new)

        if old == new or name in MAJOR_PACKAGES.values():
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
        "### Packages\n\n"
        "| | Name | Previous | New |\n"
        "| --- | --- | --- | --- |\n"
        + "\n".join(rows)
    )


def commits(previous: dict[str, Any], current: dict[str, Any]) -> str:
    previous_revision = labels(previous)[REVISION_LABEL]
    current_revision = labels(current)[REVISION_LABEL]
    if previous_revision == current_revision:
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
    previous: dict[str, Any], current: dict[str, Any], channel: str | None = None
) -> str:
    previous_version = version(previous)
    previous_packages = packages(previous)
    current_packages = packages(current)

    sections = [
        (
            f"From previous {f'`{channel.lower()}` ' if channel else ''}version "
            f"`{previous_version}` there are the following changes:"
        ),
        major_packages(previous_packages, current_packages),
        commits(previous, current),
        package_changes(previous_packages, current_packages),
    ]
    return "\n\n".join(section for section in sections if section) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an Anatase changelog from two skopeo inspect manifests."
    )
    parser.add_argument("previous", type=Path, help="Previous manifest JSON")
    parser.add_argument("current", type=Path, help="Current manifest JSON")
    parser.add_argument("--channel", help="Release channel shown in the introduction")
    args = parser.parse_args()

    print(
        changelog(
            load_manifest(args.previous), load_manifest(args.current), args.channel
        ),
        end="",
    )


if __name__ == "__main__":
    main()
