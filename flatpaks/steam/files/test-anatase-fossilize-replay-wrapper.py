#!/usr/bin/python3

import os
import shutil
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
SMT_TOPOLOGY = "# Socket,Core\n" + "0,0\n0,1\n0,2\n0,3\n0,4\n0,5\n0,6\n0,7\n" * 2
MEMINFO = "MemTotal: 33554432 kB\nMemAvailable: 1048576 kB\nSwapTotal: 67108864 kB\n"


class FossilizeReplayWrapperTests(unittest.TestCase):
    def run_wrapper(
        self,
        *arguments: str,
        timeout: str | None = None,
        topology: str = SMT_TOPOLOGY,
        meminfo: str = MEMINFO,
        cpu_status: int = 0,
        memory_status: int = 0,
        original_status: int = 0,
        helpers_missing: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "topology").write_text(topology, encoding="utf-8")
            (directory / "meminfo").write_text(meminfo, encoding="utf-8")
            lscpu = directory / "lscpu"
            lscpu.write_text(
                "#!/bin/bash\n"
                '[[ $LC_ALL = C && $# = 2 && $1 = --online && '
                '$2 = --parse=SOCKET,CORE ]] || exit 2\n'
                'cat "$TEST_TOPOLOGY"\n'
                'exit "$TEST_CPU_STATUS"\n',
                encoding="utf-8",
            )
            lscpu.chmod(0o755)
            awk = directory / "awk"
            awk.write_text(
                "#!/bin/bash\n"
                "arguments=()\n"
                'for argument in "$@"; do\n'
                '    if [[ $argument = /proc/meminfo ]]; then\n'
                '        (( TEST_MEMORY_STATUS == 0 )) || exit "$TEST_MEMORY_STATUS"\n'
                '        argument=$TEST_MEMINFO\n'
                "    fi\n"
                '    arguments+=("$argument")\n'
                "done\n"
                'exec "$TEST_REAL_AWK" "${arguments[@]}"\n',
                encoding="utf-8",
            )
            awk.chmod(0o755)
            original = Path(temporary) / "fossilize-replay"
            original.write_text(
                "#!/bin/bash\n"
                "printf 'wrapper=%s\\n' \"${FOSSILIZE_REPLAY_WRAPPER-unset}\"\n"
                "printf 'original=%s\\n' \"${FOSSILIZE_REPLAY_WRAPPER_ORIGINAL_APP-unset}\"\n"
                "printf '<%s>\\n' \"$@\"\n"
                'exit "$TEST_ORIGINAL_STATUS"\n',
                encoding="utf-8",
            )
            original.chmod(0o755)

            environment = os.environ.copy()
            environment.update(
                {
                    "FOSSILIZE_REPLAY_WRAPPER": str(WRAPPER_PATH),
                    "FOSSILIZE_REPLAY_WRAPPER_ORIGINAL_APP": str(original),
                    "PATH": f"{directory}:{environment.get('PATH', os.defpath)}",
                    "TEST_REAL_AWK": shutil.which("awk") or "/usr/bin/awk",
                    "TEST_TOPOLOGY": str(directory / "topology"),
                    "TEST_MEMINFO": str(directory / "meminfo"),
                    "TEST_CPU_STATUS": str(cpu_status),
                    "TEST_MEMORY_STATUS": str(memory_status),
                    "TEST_ORIGINAL_STATUS": str(original_status),
                }
            )
            if helpers_missing:
                environment["PATH"] = str(directory / "missing")
            if timeout is not None:
                environment["ANATASE_FOSSILIZE_REPLAY_TIMEOUT_SECONDS"] = timeout
            else:
                environment.pop(
                    "ANATASE_FOSSILIZE_REPLAY_TIMEOUT_SECONDS", None
                )

            completed = subprocess.run(
                [WRAPPER_PATH, *arguments],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(completed.returncode, original_status, completed.stderr)
            return completed

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
                "<30>",
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
        self.assertIn("<30>", completed.stdout.splitlines())
        self.assertIn("using 30 seconds", completed.stderr)

    def test_leaves_invocation_without_timeout_unchanged(self) -> None:
        completed = self.run_wrapper("cache.foz", "--progress")
        self.assertEqual(
            completed.stdout.splitlines()[-2:],
            ["<cache.foz>", "<--progress>"],
        )
        self.assertEqual(completed.stderr, "")

    def test_caps_at_physical_cores_instead_of_smt_threads(self) -> None:
        completed = self.run_wrapper("cache.foz", "--num-threads", "16")
        self.assertEqual(completed.stdout.splitlines()[-2:], ["<--num-threads>", "<8>"])
        self.assertEqual(
            completed.stderr,
            "anatase-fossilize-replay-wrapper: reducing --num-threads from 16 to 8\n",
        )

    def test_counts_repeated_core_ids_on_distinct_sockets(self) -> None:
        completed = self.run_wrapper(
            "--num-threads", "16",
            topology="# Socket,Core\n0,0\n0,1\n1,0\n1,1\n" * 2,
        )
        self.assertEqual(completed.stdout.splitlines()[-1], "<4>")
        self.assertIn("from 16 to 4", completed.stderr)

    def test_caps_by_total_ram_and_rounds_down_fractional_gib(self) -> None:
        completed = self.run_wrapper(
            "--num-threads", "15",
            meminfo="MemTotal: 11848908 kB\nMemAvailable: 524288 kB\nSwapTotal: 67108864 kB\n",
        )
        self.assertEqual(completed.stdout.splitlines()[-1], "<3>")
        self.assertIn("from 15 to 3", completed.stderr)

    def test_minimum_cap_is_one_worker(self) -> None:
        completed = self.run_wrapper(
            "--num-threads", "8", meminfo="MemTotal: 1048576 kB\n"
        )
        self.assertEqual(completed.stdout.splitlines()[-1], "<1>")
        self.assertIn("from 8 to 1", completed.stderr)

    def test_preserves_requested_counts_at_or_below_cap(self) -> None:
        for count in ("0", "2", "8", "0002", "0008"):
            with self.subTest(count=count):
                completed = self.run_wrapper("--num-threads", count)
                self.assertEqual(completed.stdout.splitlines()[-1], f"<{count}>")
                self.assertEqual(completed.stderr, "")

    def test_caps_decimal_counts_without_overflow_or_octal_parsing(self) -> None:
        for count in ("0009", "18446744073709551616"):
            with self.subTest(count=count):
                completed = self.run_wrapper("--num-threads", count)
                self.assertEqual(completed.stdout.splitlines()[-1], "<8>")
                self.assertIn(f"from {count} to 8", completed.stderr)

    def test_preserves_missing_or_malformed_worker_counts(self) -> None:
        for arguments in (
            ("--num-threads",),
            ("--num-threads", ""),
            ("--num-threads", "-1"),
            ("--num-threads", "1.5"),
            ("--num-threads", "auto"),
        ):
            with self.subTest(arguments=arguments):
                completed = self.run_wrapper(*arguments)
                self.assertEqual(
                    completed.stdout.splitlines()[2:],
                    [f"<{argument}>" for argument in arguments],
                )
                self.assertEqual(completed.stderr, "")

    def test_preserves_worker_count_if_detection_fails(self) -> None:
        for resources in (
            {"cpu_status": 1},
            {"memory_status": 1},
            {"cpu_status": 127},
            {"memory_status": 127},
            {"topology": "# Socket,Core\n"},
            {"topology": "0,0\n-,1\n"},
            {"meminfo": "MemAvailable: 33554432 kB\n"},
            {"meminfo": "MemTotal: invalid kB\n"},
            {"meminfo": "MemTotal: 0 kB\n"},
        ):
            with self.subTest(resources=resources):
                completed = self.run_wrapper("--num-threads", "8", **resources)
                self.assertEqual(completed.stdout.splitlines()[-1], "<8>")
                self.assertEqual(completed.stderr, "")

    def test_preserves_runner_exit_status_even_when_detection_fails(self) -> None:
        for cpu_status in (0, 1):
            with self.subTest(cpu_status=cpu_status):
                completed = self.run_wrapper(
                    "--num-threads", "16", cpu_status=cpu_status, original_status=37
                )
                self.assertEqual(completed.stdout.splitlines()[:2], ["wrapper=unset", "original=unset"])

    def test_starts_runner_without_resource_detection_tools(self) -> None:
        completed = self.run_wrapper(
            "--num-threads", "16", "--timeout-seconds", "10", helpers_missing=True
        )
        self.assertEqual(
            completed.stdout.splitlines(),
            ["wrapper=unset", "original=unset", "<--num-threads>", "<16>",
             "<--timeout-seconds>", "<30>"],
        )
        self.assertEqual(completed.stderr, "")

    def test_combines_worker_cap_with_timeout_and_preserves_other_arguments(self) -> None:
        completed = self.run_wrapper(
            "cache with spaces.foz", "--master-process",
            "--num-threads", "16", "--timeout-seconds", "10", "--quiet-slave",
            "--num-threads", "2",
        )
        self.assertEqual(
            completed.stdout.splitlines(),
            [
                "wrapper=unset", "original=unset", "<cache with spaces.foz>",
                "<--master-process>", "<--num-threads>", "<8>",
                "<--timeout-seconds>", "<30>", "<--quiet-slave>",
                "<--num-threads>", "<2>",
            ],
        )
        self.assertEqual(completed.stderr.count("reducing --num-threads"), 1)


if __name__ == "__main__":
    unittest.main()
