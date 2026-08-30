#!/usr/bin/python3

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


WRAPPER_PATH = Path(
    os.environ.get(
        "ANATASE_FOSSILIZE_REPLAY_WRAPPER",
        Path(__file__).with_name("anatase-fossilize-replay-wrapper"),
    )
)


class FossilizeReplayWrapperTests(unittest.TestCase):
    def run_wrapper(
        self, *arguments: str, timeout: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            original = Path(temporary) / "fossilize-replay"
            original.write_text(
                "#!/bin/bash\n"
                "printf 'wrapper=%s\\n' \"${FOSSILIZE_REPLAY_WRAPPER-unset}\"\n"
                "printf 'original=%s\\n' \"${FOSSILIZE_REPLAY_WRAPPER_ORIGINAL_APP-unset}\"\n"
                "printf '<%s>\\n' \"$@\"\n",
                encoding="utf-8",
            )
            original.chmod(0o755)

            environment = os.environ.copy()
            environment.update(
                {
                    "FOSSILIZE_REPLAY_WRAPPER": str(WRAPPER_PATH),
                    "FOSSILIZE_REPLAY_WRAPPER_ORIGINAL_APP": str(original),
                }
            )
            if timeout is not None:
                environment["ANATASE_FOSSILIZE_REPLAY_TIMEOUT_SECONDS"] = timeout
            else:
                environment.pop(
                    "ANATASE_FOSSILIZE_REPLAY_TIMEOUT_SECONDS", None
                )

            return subprocess.run(
                [WRAPPER_PATH, *arguments],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )

    def test_raises_steam_worker_timeout_and_clears_wrapper_hook(self) -> None:
        completed = self.run_wrapper(
            "cache with spaces.foz",
            "--master-process",
            "--timeout-seconds",
            "10",
            "--quiet-slave",
        )
        self.assertEqual(
            completed.stdout.splitlines(),
            [
                "wrapper=unset",
                "original=unset",
                "<cache with spaces.foz>",
                "<--master-process>",
                "<--timeout-seconds>",
                "<60>",
                "<--quiet-slave>",
            ],
        )
        self.assertEqual(completed.stderr, "")

    def test_timeout_can_be_overridden(self) -> None:
        completed = self.run_wrapper(
            "cache.foz", "--timeout-seconds", "10", timeout="120"
        )
        self.assertIn("<120>", completed.stdout.splitlines())
        self.assertEqual(completed.stderr, "")

    def test_invalid_override_falls_back_to_default(self) -> None:
        completed = self.run_wrapper(
            "cache.foz", "--timeout-seconds", "10", timeout="soon"
        )
        self.assertIn("<60>", completed.stdout.splitlines())
        self.assertIn("using 60 seconds", completed.stderr)

    def test_leaves_invocation_without_timeout_unchanged(self) -> None:
        completed = self.run_wrapper("cache.foz", "--progress")
        self.assertEqual(
            completed.stdout.splitlines()[-2:],
            ["<cache.foz>", "<--progress>"],
        )


if __name__ == "__main__":
    unittest.main()
