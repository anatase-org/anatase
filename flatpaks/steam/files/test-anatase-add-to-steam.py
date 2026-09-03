#!/usr/bin/python3

import os
import subprocess
import tempfile
import unittest
import urllib.parse
from pathlib import Path


SCRIPT = Path(os.environ.get("ANATASE_ADD_TO_STEAM", "anatase-add-to-steam"))


class AddToSteamTests(unittest.TestCase):
    def test_creates_shortcut_for_uri_and_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            marker = root / "addnonsteamgamefile"
            runtime = root / "run"
            source = root / "My Game.desktop"
            source_contents = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=My Game\n"
                "Icon=my-game\n"
                "Exec=/usr/bin/example %U\n"
                "\n"
                "[Desktop Action Configure]\n"
                "Name=Configure\n"
                "Exec=/usr/bin/example --configure\n"
            )
            source.write_text(source_contents, encoding="utf-8")
            env = os.environ.copy()
            env.update(
                {
                    "ANATASE_ADD_TO_STEAM_MARKER": str(marker),
                    "ANATASE_STEAM_COMMAND": "/usr/bin/echo",
                    "XDG_RUNTIME_DIR": str(runtime),
                }
            )

            shortcut = runtime / "anatase-steam/add-to-steam/My Game.desktop"
            encoded_path = urllib.parse.quote_plus(str(shortcut))
            for argument in (source.as_uri(), str(source)):
                with self.subTest(argument=argument):
                    result = subprocess.run(
                        [SCRIPT, argument],
                        check=True,
                        capture_output=True,
                        env=env,
                        text=True,
                    )
                    self.assertEqual(
                        result.stdout.strip(),
                        f"steam://addnonsteamgame/{encoded_path}",
                    )
            self.assertTrue(marker.is_file())
            self.assertEqual(
                shortcut.read_text(encoding="utf-8"),
                source_contents.replace(
                    "Exec=/usr/bin/example %U",
                    "Exec=hrun /usr/bin/example %U",
                    1,
                ),
            )

    def test_rejects_missing_desktop_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = root / "run"
            runtime.mkdir()
            env = os.environ.copy()
            env["XDG_RUNTIME_DIR"] = str(runtime)

            result = subprocess.run(
                [SCRIPT, "file:///home/test/Missing.desktop"],
                capture_output=True,
                env=env,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("path does not identify a desktop file", result.stderr)

    def test_rejects_multiple_shortcuts(self) -> None:
        result = subprocess.run(
            [SCRIPT, "one.desktop", "two.desktop"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
