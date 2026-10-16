import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


WRAPPER = Path(os.environ.get(
    "ANATASE_PRESSURE_VESSEL_UNRUNTIME",
    Path(__file__).with_name("anatase-pressure-vessel-unruntime"),
)).resolve()


class PressureVesselTests(unittest.TestCase):
    def run_wrapper(self, options, arguments, machine="", delegate_arch="", steam=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prefix = "pressure-vessel" + (f"-{delegate_arch}" if delegate_arch else "")
            delegate = root / prefix / "bin/pressure-vessel-unruntime"
            delegate.parent.mkdir(parents=True)
            delegate.write_text(
                "#!/bin/bash\n"
                "while (( $# )) && [[ $1 != -- ]]; do shift; done\n"
                "shift\n"
                # Simulate pv-adverb replacing the caller's library path.
                "export LD_LIBRARY_PATH=/pressure-vessel/aliases\n"
                f"export ANATASE_TEST_DELEGATE={prefix}\n"
                'exec "$@"\n'
            )
            delegate.chmod(0o755)
            probe = root / "steamrt64/steam" if steam else root / "probe.py"
            probe.parent.mkdir(parents=True, exist_ok=True)
            probe.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "print(json.dumps([os.environ['LD_LIBRARY_PATH'], "
                "os.environ['ANATASE_TEST_DELEGATE'], sys.argv[1:]]))\n"
            )
            probe.chmod(0o755)
            command = [str(probe)] if steam else ["python3", str(probe)]
            result = subprocess.check_output(
                ["bash", str(WRAPPER), *options, "--", *command, *arguments],
                text=True,
                env={
                    **os.environ,
                    "LD_LIBRARY_PATH": "/discarded-caller-path",
                    "PRESSURE_VESSEL_RUNTIME_BASE": str(root),
                    "STEAM_COMPAT_MACHINE_ARCHITECTURE": machine,
                },
            )
            return json.loads(result)

    def test_client_paths_survive_adverb_and_preserve_payload_arguments(self):
        arguments = ["a path with spaces", "line one\nline two", "--flag"]
        library_path, delegate, actual = self.run_wrapper(
            ["--variable-dir=/some runtime", "--for-steam-client"], arguments
        )
        paths = library_path.split(":")
        self.assertEqual(paths[0], "/pressure-vessel/aliases")
        self.assertNotIn("/discarded-caller-path", paths)
        for tuple_name in ("x86_64-linux-gnu", "i386-linux-gnu", "aarch64-linux-gnu"):
            override = f"/usr/lib/pressure-vessel/overrides/lib/{tuple_name}"
            fallback = f"/usr/lib/{tuple_name}"
            self.assertIn(override, paths)
            self.assertIn(fallback, paths)
            self.assertLess(paths.index(override), paths.index(fallback))
        self.assertEqual(actual, arguments)
        self.assertEqual(delegate, "pressure-vessel")

    def test_game_payload_is_not_modified(self):
        library_path, _, arguments = self.run_wrapper([], ["--for-steam-client"])
        self.assertEqual(library_path, "/pressure-vessel/aliases")
        self.assertEqual(arguments, ["--for-steam-client"])

    def test_steam_bundled_libraries_precede_added_system_paths(self):
        library_path, _, _ = self.run_wrapper(["--for-steam-client"], [], steam=True)
        paths = library_path.split(":")
        self.assertEqual(paths[0], "/pressure-vessel/aliases")
        self.assertEqual(Path(paths[1]).name, "steamrt64")
        self.assertLess(
            1, paths.index("/usr/lib/pressure-vessel/overrides/lib/x86_64-linux-gnu")
        )

    def test_emulation_selects_native_pressure_vessel(self):
        _, delegate, _ = self.run_wrapper(
            ["--for-steam-client"], [], "aarch64-linux-gnu", "arm64"
        )
        self.assertEqual(delegate, "pressure-vessel-arm64")


if __name__ == "__main__":
    unittest.main()
