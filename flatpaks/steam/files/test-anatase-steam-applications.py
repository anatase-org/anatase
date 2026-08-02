#!/usr/bin/python3

import configparser
import importlib.machinery
import importlib.util
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


APPLICATIONS_PATH = Path(
    os.environ.get(
        "ANATASE_STEAM_APPLICATIONS",
        Path(__file__).with_name("anatase-steam-applications.py"),
    )
)
HRUN_PATH = Path(
    os.environ.get(
        "ANATASE_STEAM_HRUN",
        Path(__file__).with_name("hrun"),
    )
)
REAPER_PATH = Path(
    os.environ.get(
        "ANATASE_STEAM_REAPER",
        Path(__file__).with_name("anatase-steam-reaper.c"),
    )
)

loader = importlib.machinery.SourceFileLoader(
    "anatase_steam_applications", str(APPLICATIONS_PATH)
)
spec = importlib.util.spec_from_loader(loader.name, loader)
applications = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = applications
loader.exec_module(applications)


def write_desktop(directory: Path, desktop_id: str, values: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / desktop_id
    path.write_text(f"[Desktop Entry]\n{values}", encoding="utf-8")
    return path


def parse_desktop(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(path)
    return parser


class ApplicationCatalogTests(unittest.TestCase):
    def test_reconcile_filters_rewrites_and_copies_icons(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "runtime/anatase-steam"
            user_apps = base / "user/applications"
            user_icons = base / "user/icons"
            system_apps = base / "system/applications"
            spaces_apps = base / "spaces/applications"
            runtime_apps = base / "runtime-source/applications"
            runtime_icons = base / "runtime-source/icons"
            reaper = base / "source-reaper"
            reaper.write_bytes(b"reaper")

            user_icon = user_icons / "hicolor/256x256/apps/example.png"
            user_icon.parent.mkdir(parents=True)
            user_icon.write_bytes(b"png-256")
            smaller_icon = user_icons / "hicolor/128x128/apps/example.png"
            smaller_icon.parent.mkdir(parents=True)
            smaller_icon.write_bytes(b"png-128")
            (user_icons / "hicolor/scalable/apps").mkdir(parents=True)
            (user_icons / "hicolor/scalable/apps/example.svg").write_bytes(b"svg")

            write_desktop(
                user_apps,
                "example.desktop",
                "Type=Application\n"
                "Name=User Example\n"
                "Exec=/usr/bin/flatpak run org.example.App %U\n"
                "TryExec=/usr/bin/flatpak\n"
                "Path=/host/path\n"
                "DBusActivatable=true\n"
                "OnlyShowIn=KDE;\n"
                "Icon=example\n"
                "Actions=New;\n\n"
                "[Desktop Action New]\n"
                "Name=New Window\n"
                "Exec=/usr/bin/flatpak run org.example.App --new-window %U\n",
            )
            write_desktop(
                runtime_apps,
                "example.desktop",
                "Type=Application\nName=Lower Example\nExec=/usr/bin/lower\n",
            )

            runtime_icon = runtime_icons / "hicolor/scalable/apps/runtime.svg"
            runtime_icon.parent.mkdir(parents=True)
            runtime_icon.write_bytes(b"runtime-svg")
            write_desktop(
                runtime_apps,
                "runtime.desktop",
                "Type=Application\n"
                "Name=Runtime\n"
                "Exec=/usr/bin/runtime %F\n"
                "NotShowIn=KDE;\n"
                "Icon=runtime\n",
            )

            visible_spaces_icon = base / "mounted/icons/spaces.png"
            visible_spaces_icon.parent.mkdir(parents=True)
            visible_spaces_icon.write_bytes(b"spaces-png")
            write_desktop(
                spaces_apps,
                "spaces-app.desktop",
                "Type=Application\n"
                "Name=Spaces App\n"
                "Exec=/usr/bin/spaces enter --graphical arch -- chrome\n"
                f"Icon={base}/host/icons/spaces.png\n",
            )

            excluded = {
                "hidden.desktop": "Hidden=true\n",
                "nodisplay.desktop": "NoDisplay=true\n",
                "terminal.desktop": "Terminal=true\n",
                "system.desktop": "Categories=Utility;System;\n",
                "development.desktop": "Categories=Development;Utility;\n",
                "link.desktop": "Type=Link\n",
            }
            for desktop_id, extra in excluded.items():
                write_desktop(
                    runtime_apps,
                    desktop_id,
                    "Type=Application\n"
                    "Name=Excluded\n"
                    "Exec=/usr/bin/excluded\n"
                    f"{extra}",
                )
            write_desktop(
                runtime_apps,
                "missing-exec.desktop",
                "Type=Application\nName=Missing Exec\n",
            )

            stale_application = root / "applications/stale.desktop"
            stale_application.parent.mkdir(parents=True)
            stale_application.write_text("stale")
            stale_icon = root / "icons/stale.png"
            stale_icon.parent.mkdir(parents=True)
            stale_icon.write_bytes(b"stale")

            sources = (
                applications.Source(user_apps, (user_icons,)),
                applications.Source(system_apps, ()),
                applications.Source(
                    spaces_apps,
                    (),
                    translations=(
                        (f"{base}/host/", f"{base}/mounted/"),
                    ),
                ),
                applications.Source(runtime_apps, (runtime_icons,)),
            )
            applications.reconcile(
                root,
                sources,
                reaper,
                {"org.anatase.Steam.desktop", "steam.desktop"},
            )

            example = parse_desktop(root / "applications/example.desktop")
            entry = example["Desktop Entry"]
            self.assertEqual(entry["Name"], "User Example")
            self.assertEqual(entry["OnlyShowIn"], "KDE;")
            self.assertEqual(entry["DBusActivatable"], "false")
            self.assertNotIn("TryExec", entry)
            self.assertNotIn("Path", entry)
            self.assertEqual(
                entry["Exec"],
                "/app/bin/hrun "
                "/usr/bin/flatpak run org.example.App %U",
            )
            self.assertEqual(
                example["Desktop Action New"]["Exec"],
                "/app/bin/hrun "
                "/usr/bin/flatpak run org.example.App --new-window %U",
            )
            copied_user_icon = Path(entry["Icon"])
            self.assertEqual(copied_user_icon.read_bytes(), b"png-256")
            self.assertEqual(copied_user_icon.parent, root / "icons")

            runtime = parse_desktop(root / "applications/runtime.desktop")
            self.assertEqual(
                runtime["Desktop Entry"]["Exec"],
                "/app/bin/hrun /usr/bin/runtime %F",
            )
            self.assertEqual(
                runtime["Desktop Entry"]["DBusActivatable"], "false"
            )
            self.assertEqual(runtime["Desktop Entry"]["NotShowIn"], "KDE;")
            self.assertEqual(
                Path(runtime["Desktop Entry"]["Icon"]).read_bytes(),
                b"runtime-svg",
            )

            spaces = parse_desktop(root / "applications/spaces-app.desktop")
            self.assertTrue(
                spaces["Desktop Entry"]["Exec"].startswith(
                    "/app/bin/hrun /usr/bin/spaces "
                )
            )
            self.assertEqual(
                Path(spaces["Desktop Entry"]["Icon"]).read_bytes(),
                b"spaces-png",
            )

            for desktop_id in (*excluded, "missing-exec.desktop"):
                masked = parse_desktop(root / "applications" / desktop_id)
                self.assertEqual(masked["Desktop Entry"]["Hidden"], "true")
            for desktop_id in ("org.anatase.Steam.desktop", "steam.desktop"):
                masked = parse_desktop(root / "applications" / desktop_id)
                self.assertEqual(masked["Desktop Entry"]["Hidden"], "true")

            self.assertFalse(stale_application.exists())
            self.assertFalse(stale_icon.exists())
            self.assertEqual((root / "bin/reaper").read_bytes(), b"reaper")
            self.assertTrue((root / "bin/reaper").stat().st_mode & 0o111)


class HostLaunchTests(unittest.TestCase):
    def test_flatpak_launch_forwards_ids_through_reaper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            mock = base / "flatpak-spawn"
            mock.write_text(
                "#!/bin/bash\nprintf '<%s>\\n' \"$@\"\n",
                encoding="utf-8",
            )
            mock.chmod(0o755)
            environment = {
                **os.environ,
                "PATH": f"{base}:{os.environ['PATH']}",
                "HOME": str(base / "home"),
                "XDG_RUNTIME_DIR": str(base / "run"),
                "SteamAppId": "1234",
                "SteamGameId": "5678",
            }
            completed = subprocess.run(
                [
                    "/bin/bash",
                    HRUN_PATH,
                    "/usr/bin/flatpak",
                    "run",
                    "org.example.App",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(
                completed.stdout.splitlines(),
                [
                    "<--host>",
                    "<--watch-bus>",
                    f"<--directory={base}/home>",
                    "<--env=SteamAppId=1234>",
                    "<--env=SteamGameId=5678>",
                    f"<{base}/run/anatase-steam/bin/reaper>",
                    "<SteamLaunch>",
                    "<AppId=1234>",
                    "<-->",
                    "</usr/bin/flatpak>",
                    "<run>",
                    "<org.example.App>",
                ],
            )

    def test_spaces_launch_forwards_ids_without_outer_reaper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            mock = base / "flatpak-spawn"
            mock.write_text(
                "#!/bin/bash\nprintf '<%s>\\n' \"$@\"\n",
                encoding="utf-8",
            )
            mock.chmod(0o755)
            completed = subprocess.run(
                [
                    "/bin/bash",
                    HRUN_PATH,
                    "/usr/bin/spaces",
                    "enter",
                    "arch",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "PATH": f"{base}:{os.environ['PATH']}",
                    "HOME": str(base / "home"),
                    "SteamAppId": "1234",
                    "SteamGameId": "5678",
                },
            )
            self.assertEqual(
                completed.stdout.splitlines(),
                [
                    "<--host>",
                    "<--watch-bus>",
                    f"<--directory={base}/home>",
                    "<--env=SteamAppId=1234>",
                    "<--env=SteamGameId=5678>",
                    "</usr/bin/spaces>",
                    "<enter>",
                    "<arch>",
                ],
            )


class ReaperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.reaper = Path(cls.temporary.name) / "reaper"
        subprocess.run(
            [
                os.environ.get("CC", "cc"),
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(REAPER_PATH),
                "-o",
                str(cls.reaper),
            ],
            check=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_process_identity_and_exit_status(self) -> None:
        process = subprocess.Popen(
            [
                self.reaper,
                "SteamLaunch",
                "AppId=4321",
                "--",
                "/bin/sh",
                "-c",
                "sleep 1; exit 7",
            ]
        )
        try:
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                if Path(f"/proc/{process.pid}/comm").read_text().strip() == "reaper":
                    break
                time.sleep(0.01)
            self.assertEqual(
                Path(f"/proc/{process.pid}/comm").read_text().strip(), "reaper"
            )
            command_line = Path(f"/proc/{process.pid}/cmdline").read_bytes()
            self.assertIn(b"SteamLaunch\0AppId=4321\0--\0", command_line)
            self.assertEqual(process.wait(timeout=3), 7)
        finally:
            if process.poll() is None:
                process.kill()

    def test_termination_is_forwarded(self) -> None:
        process = subprocess.Popen(
            [
                self.reaper,
                "SteamLaunch",
                "AppId=4321",
                "--",
                "/bin/sh",
                "-c",
                "sleep 30",
            ]
        )
        try:
            time.sleep(0.05)
            process.send_signal(signal.SIGTERM)
            self.assertEqual(process.wait(timeout=3), 128 + signal.SIGTERM)
        finally:
            if process.poll() is None:
                process.kill()


if __name__ == "__main__":
    unittest.main()
