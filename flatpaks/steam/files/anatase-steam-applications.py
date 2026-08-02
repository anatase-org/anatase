#!/usr/bin/python3

import configparser
import fcntl
import hashlib
import io
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path


HOST_LAUNCH = "/app/bin/hrun"
IMAGE_EXTENSIONS = {".png", ".svg"}


@dataclass(frozen=True)
class Source:
    applications: Path
    icons: tuple[Path, ...]
    translations: tuple[tuple[str, str], ...] = ()


def desktop_parser() -> configparser.ConfigParser:
    parser = configparser.ConfigParser(
        interpolation=None,
        strict=False,
        delimiters=("=",),
        comment_prefixes=("#",),
        inline_comment_prefixes=None,
        empty_lines_in_values=False,
    )
    parser.optionxform = str
    return parser


def read_desktop(path: Path) -> configparser.ConfigParser | None:
    parser = desktop_parser()
    try:
        with path.open(encoding="utf-8", errors="replace") as source:
            parser.read_file(source)
    except (OSError, configparser.Error):
        return None
    if not parser.has_section("Desktop Entry"):
        return None
    return parser


def true_value(entry: configparser.SectionProxy, key: str) -> bool:
    return entry.get(key, "").strip().casefold() == "true"


def included(parser: configparser.ConfigParser) -> bool:
    entry = parser["Desktop Entry"]
    return (
        entry.get("Type", "Application").strip() == "Application"
        and bool(entry.get("Exec", "").strip())
        and not true_value(entry, "Hidden")
        and not true_value(entry, "NoDisplay")
        and not true_value(entry, "Terminal")
    )


def serialize(parser: configparser.ConfigParser) -> bytes:
    output = io.StringIO()
    parser.write(output, space_around_delimiters=False)
    return output.getvalue().encode()


def atomic_write(path: Path, contents: bytes, mode: int = 0o644) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        output = os.fdopen(descriptor, "wb")
        descriptor = -1
        with output:
            output.write(contents)
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(path)
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
        raise


def atomic_copy(source: Path, destination: Path, mode: int = 0o644) -> None:
    atomic_write(destination, source.read_bytes(), mode)


def mask_contents() -> bytes:
    return b"[Desktop Entry]\nType=Application\nHidden=true\n"


def translate_absolute_icon(icon: str, source: Source) -> Path:
    for original, replacement in source.translations:
        if icon == original.rstrip("/") or icon.startswith(original):
            return Path(replacement + icon[len(original) :])
    return Path(icon)


def icon_size(path: Path) -> int | None:
    for parent in path.parents:
        match = re.fullmatch(r"([0-9]+)x[0-9]+", parent.name)
        if match:
            return int(match.group(1))
    return None


def icon_rank(path: Path) -> tuple[int, int, int, str]:
    if path.suffix.casefold() == ".svg":
        return (1, 0, 0, str(path))
    size = icon_size(path)
    if size is None:
        return (0, 3, 0, str(path))
    if size == 256:
        return (0, 0, 0, str(path))
    if size > 256:
        return (0, 1, size - 256, str(path))
    return (0, 2, 256 - size, str(path))


class IconResolver:
    def __init__(self) -> None:
        self._indexes: dict[tuple[Path, ...], dict[str, list[Path]]] = {}

    def _index(self, roots: tuple[Path, ...]) -> dict[str, list[Path]]:
        if roots in self._indexes:
            return self._indexes[roots]
        index: dict[str, list[Path]] = {}
        for root in roots:
            if not root.is_dir():
                continue
            for directory, _, filenames in os.walk(root):
                for filename in filenames:
                    path = Path(directory, filename)
                    if path.suffix.casefold() not in IMAGE_EXTENSIONS:
                        continue
                    index.setdefault(path.stem, []).append(path)
                    index.setdefault(path.name, []).append(path)
        self._indexes[roots] = index
        return index

    def resolve(self, icon: str, source: Source) -> Path | None:
        if not icon:
            return None
        if icon.startswith("/"):
            path = translate_absolute_icon(icon, source)
            if path.suffix.casefold() in IMAGE_EXTENSIONS and path.is_file():
                return path
            return None
        candidates = self._index(source.icons).get(icon, [])
        if not candidates:
            candidates = self._index(source.icons).get(Path(icon).stem, [])
        existing = [candidate for candidate in candidates if candidate.is_file()]
        return min(existing, key=icon_rank) if existing else None


def icon_destination(root: Path, desktop_id: str, source: Path) -> Path:
    stem = desktop_id.removesuffix(".desktop")
    safe_stem = re.sub(r"[^A-Za-z0-9._-]", "_", stem)
    digest = hashlib.sha256(desktop_id.encode()).hexdigest()[:8]
    return root / "icons" / f"{safe_stem}-{digest}{source.suffix.casefold()}"


def rewrite_host_commands(parser: configparser.ConfigParser) -> None:
    entry = parser["Desktop Entry"]
    entry["DBusActivatable"] = "false"
    entry.pop("TryExec", None)
    entry.pop("Path", None)
    for section_name in parser.sections():
        if section_name != "Desktop Entry" and not section_name.startswith(
            "Desktop Action "
        ):
            continue
        section = parser[section_name]
        command = section.get("Exec", "").strip()
        if command:
            section["Exec"] = f"{HOST_LAUNCH} {command}"


def remove_stale(directory: Path, expected: set[str]) -> None:
    for path in directory.iterdir():
        if path.name not in expected and (path.is_file() or path.is_symlink()):
            path.unlink()


def reconcile(
    root: Path,
    sources: tuple[Source, ...],
    reaper_source: Path,
    own_desktop_ids: set[str],
) -> None:
    applications = root / "applications"
    icons = root / "icons"
    binaries = root / "bin"
    for directory in (root, applications, icons, binaries):
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory.chmod(0o700)

    with (root / "rewrite.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        atomic_copy(reaper_source, binaries / "reaper", 0o755)

        selected: dict[str, tuple[Path, Source]] = {}
        for source in sources:
            if not source.applications.is_dir():
                continue
            for path in sorted(source.applications.glob("*.desktop")):
                selected.setdefault(path.name, (path, source))

        expected_applications: set[str] = set()
        expected_icons: set[str] = set()
        resolver = IconResolver()
        for desktop_id, (path, source) in selected.items():
            destination = applications / desktop_id
            expected_applications.add(desktop_id)
            parser = read_desktop(path)
            if desktop_id in own_desktop_ids or parser is None or not included(parser):
                atomic_write(destination, mask_contents())
                continue

            rewrite_host_commands(parser)

            entry = parser["Desktop Entry"]
            resolved_icon = resolver.resolve(entry.get("Icon", "").strip(), source)
            if resolved_icon is None:
                entry.pop("Icon", None)
            else:
                icon_path = icon_destination(root, desktop_id, resolved_icon)
                atomic_copy(resolved_icon, icon_path)
                expected_icons.add(icon_path.name)
                entry["Icon"] = str(icon_path)
            atomic_write(destination, serialize(parser))

        for desktop_id in own_desktop_ids:
            if desktop_id not in expected_applications:
                expected_applications.add(desktop_id)
                atomic_write(applications / desktop_id, mask_contents())

        remove_stale(applications, expected_applications)
        remove_stale(icons, expected_icons)


def configured_sources() -> tuple[Source, ...]:
    sandbox_data_home = Path(
        os.environ.get(
            "ANATASE_STEAM_SANDBOX_DATA_HOME",
            str(Path.home() / ".var/app/org.anatase.Steam/data"),
        )
    )
    user_flatpak = sandbox_data_home / "flatpak"
    return (
        Source(
            user_flatpak / "exports/share/applications",
            (user_flatpak / "exports/share/icons",),
        ),
        Source(
            Path("/var/lib/flatpak/exports/share/applications"),
            (Path("/var/lib/flatpak/exports/share/icons"),),
        ),
        Source(
            Path("/var/usrlocal/share/applications"),
            (Path("/var/usrlocal/share/applications/spaces-icons"),),
            translations=(("/usr/local/", "/var/usrlocal/"),),
        ),
        Source(
            Path("/usr/share/applications"),
            (Path("/usr/share/icons"), Path("/usr/share/pixmaps")),
        ),
    )


def main() -> None:
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    flatpak_id = os.environ.get("FLATPAK_ID", "org.anatase.Steam")
    reconcile(
        runtime / "anatase-steam",
        configured_sources(),
        Path("/app/libexec/anatase-steam-reaper"),
        {"steam.desktop", f"{flatpak_id}.desktop"},
    )


if __name__ == "__main__":
    main()
