#!/usr/bin/python3
"""Exercise bootstrap with fake AppImages, without launching a user session."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


LAUNCHER = Path(os.environ.get("ANATASE_EPIC_LAUNCHER", "anatase-epic-games-launcher"))
SEED_PATH = "/app/share/epic-games-launcher/EpicGamesLauncher-x86_64.AppImage"


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="epic-bootstrap-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.seed = self.root / "seed.AppImage"
        self.seed.write_text(
            "#!/usr/bin/python3\n"
            "import json, os, sys\n"
            "print(json.dumps({'args': sys.argv[1:], 'image': sys.argv[0], "
            "'extract': os.environ.get('APPIMAGE_EXTRACT_AND_RUN'), "
            "'tmp': os.environ.get('TMPDIR'), 'cleanup': os.environ.get('NO_CLEANUP')}))\n"
            "sys.exit(int(os.environ.get('TEST_EXIT', '0')))\n"
        )
        self.seed.chmod(0o444)
        self.launcher = self.root / "launcher"
        self.launcher.write_text(LAUNCHER.read_text().replace(SEED_PATH, str(self.seed)))
        self.launcher.chmod(0o755)
        self.env = os.environ | {
            "XDG_DATA_HOME": str(self.root / "private data"),
            "XDG_CACHE_HOME": str(self.root / "private cache"),
            "APPIMAGE_EXTRACT_AND_RUN": "0",
            "NO_CLEANUP": "1",
            "TMPDIR": "/must-not-be-used",
        }
        self.image = Path(self.env["XDG_DATA_HOME"]) / "epic-games-launcher" / "EpicGamesLauncher-x86_64.AppImage"

    def run_launcher(self, *args, **env):
        return subprocess.run(
            [str(self.launcher), *args], env=self.env | env,
            capture_output=True, text=True, timeout=15,
        )

    def test_bootstrap_arguments_environment_and_exit_status(self):
        args = ["com.epicgames.launcher://example?value=a b", "--flag", ""]
        result = self.run_launcher(*args, TEST_EXIT="23")
        self.assertEqual(result.returncode, 23, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["args"], args)
        self.assertEqual(output["image"], str(self.image))
        self.assertEqual(output["extract"], "1")
        self.assertIsNone(output["cleanup"])
        self.assertEqual(output["tmp"], str(Path(self.env["XDG_CACHE_HOME"]) / "epic-games-launcher/tmp"))
        self.assertEqual(self.image.read_bytes(), self.seed.read_bytes())
        self.assertEqual(self.image.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.seed.stat().st_mode & 0o777, 0o444)

    def test_preserves_self_updated_copy_and_flatpak_seed_changes(self):
        self.assertEqual(self.run_launcher().returncode, 0)
        self.image.write_text("#!/bin/sh\nprintf 'updated application\\n'\n")
        updated = self.image.read_bytes()
        self.seed.chmod(0o644)
        self.seed.write_text("new Flatpak bootstrap must not replace a private app")
        self.seed.chmod(0o444)
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "updated application\n")
        self.assertEqual(self.image.read_bytes(), updated)

    def test_scrubs_steam_ids_but_preserves_display_and_controller_environment(self):
        self.seed.chmod(0o644)
        self.seed.write_text(
            "#!/usr/bin/python3\n"
            "import json, os\n"
            "print(json.dumps(dict(os.environ)))\n"
        )
        self.seed.chmod(0o444)
        removed = {
            "SteamAppId": "3403903578",
            "SteamGameId": "14619654546280939520",
            "SteamOverlayGameId": "14619654546280939520",
            "STEAM_COMPAT_APP_ID": "3403903578",
        }
        preserved = {
            "SteamVirtualGamepadInfo": "/run/user/1000/steam-gamepad-info",
            "SDL_GAMECONTROLLERCONFIG": "test-controller-mapping",
            "DISPLAY": ":1",
            "STEAM_MULTIPLE_XWAYLANDS": "1",
        }
        for inherited in (removed, dict.fromkeys(removed, "")):
            with self.subTest(inherited=inherited):
                result = self.run_launcher(**inherited, **preserved)
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                for key in removed:
                    self.assertNotIn(key, output)
                for key, value in preserved.items():
                    self.assertEqual(output.get(key), value, key)

    def test_concurrent_first_launches_publish_one_complete_copy(self):
        processes = [subprocess.Popen(
            [str(self.launcher), str(i)], env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        ) for i in range(8)]
        for i, process in enumerate(processes):
            stdout, stderr = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)["args"], [str(i)])
        self.assertEqual(self.image.read_bytes(), self.seed.read_bytes())

    def test_failed_copy_retries_without_exposing_partial_image(self):
        bindir = self.root / "bin"
        bindir.mkdir()
        fake_cp = bindir / "cp"
        fake_cp.write_text('#!/bin/bash\nprintf partial > "${@: -1}"\nexit 1\n')
        fake_cp.chmod(0o755)
        result = self.run_launcher(PATH=f"{bindir}:{self.env['PATH']}")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.image.exists())
        self.assertFalse((self.image.parent / ".initialized").exists())
        self.assertEqual(list(self.image.parent.glob(".bootstrap.??????")), [])
        self.assertEqual(self.run_launcher().returncode, 0)

    def test_completed_copy_survives_interrupted_marker_creation(self):
        self.image.parent.mkdir(parents=True)
        self.image.write_bytes(self.seed.read_bytes())
        self.image.chmod(0o700)
        self.seed.unlink()
        self.assertEqual(self.run_launcher().returncode, 0)
        self.assertTrue((self.image.parent / ".initialized").is_file())

    def test_missing_initialized_image_does_not_restore_old_seed(self):
        self.assertEqual(self.run_launcher().returncode, 0)
        self.image.unlink()
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertIn("initialized AppImage is missing", result.stderr)
        self.assertFalse(self.image.exists())

    def test_bootstrap_lock_is_not_inherited_by_application(self):
        self.assertEqual(self.run_launcher().returncode, 0)
        self.image.write_text(
            '#!/bin/bash\nflock -n "${XDG_DATA_HOME}/epic-games-launcher/.bootstrap.lock" /bin/true\n'
        )
        self.assertEqual(self.run_launcher().returncode, 0)


if __name__ == "__main__":
    unittest.main()
