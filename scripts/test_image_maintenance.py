"""Run inside a disposable Anatase container; replaces its os-release and tools.

podman run --rm --network=none --security-opt label=disable -v "$PWD:/repo:ro" \
    --entrypoint=python3 i.anatase.org/anatase:rolling \
    /repo/scripts/test_image_maintenance.py
"""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / 'cards/base/atomic/anatase-image-maintenance'
COMMANDS = ['appstreamcli refresh --force', 'mandb -q']
MOCK = r'''#!/bin/bash
set -eu
command=${0##*/}
printf '%s\n' "$command $*" >> "$TEST_LOG"
touch "$TEST_EVENTS/$command.started"
if [ "${TEST_PARALLEL:-}" = yes ]; then
    if [ "$command" = appstreamcli ]; then
        other=mandb
    else
        other=appstreamcli
    fi
    for ((i=0; i<200; i++)); do
        [ ! -f "$TEST_EVENTS/$other.started" ] || break
        sleep 0.01
    done
    [ -f "$TEST_EVENTS/$other.started" ] || exit 8
fi
if [ "${TEST_FAIL:-}" = "$command" ]; then
    exit 7
fi
if [ "${TEST_DELAY:-}" = "$command" ]; then
    sleep 0.1
fi
touch "$TEST_EVENTS/$command.finished"
'''


class ImageMaintenanceTests(unittest.TestCase):
    def setUp(self):
        if not Path('/run/.containerenv').exists():
            self.fail('Run this test in a disposable Podman container, as documented above.')
        self.work = tempfile.TemporaryDirectory(prefix='maintenance-test-', dir='/var/tmp')
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.log = self.root / 'operations'
        self.events = self.root / 'events'
        self.events.mkdir()
        self.marker = self.root / 'image-version'
        self.env = dict(os.environ, TEST_LOG=str(self.log), TEST_EVENTS=str(self.events),
                        STATE_DIRECTORY=str(self.root))
        for command in ('appstreamcli', 'mandb'):
            path = Path('/usr/bin') / command
            path.unlink(missing_ok=True)
            path.write_text(MOCK)
            path.chmod(0o755)
        self.version('image-1')

    def version(self, value):
        Path('/usr/lib/os-release').write_text(f'BUILD_ID="{value}"\n')

    def run_service(self, fail='', **extra_env):
        for path in self.events.iterdir():
            path.unlink()
        result = subprocess.run(
            ['bash', str(HELPER)],
            env=dict(self.env, TEST_FAIL=fail, **extra_env),
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 7 if fail else 0, result.stderr)
        self.assertEqual(list(self.root.glob('image-version.*')), [])

    def assert_calls(self, runs):
        calls = self.log.read_text().splitlines() if self.log.exists() else []
        self.assertCountEqual(calls, COMMANDS * runs)

    def test_first_boot_runs_both_and_unchanged_image_skips(self):
        self.run_service()
        self.assertEqual(self.marker.read_text(), 'image-1\n')
        self.run_service()
        self.assert_calls(1)

    def test_upgrade_and_rollback_each_refresh_shared_caches(self):
        self.run_service()
        self.version('image-2')
        self.run_service()
        self.run_service()
        self.assertEqual(self.marker.read_text(), 'image-2\n')
        self.version('image-1')
        self.run_service()
        self.run_service()
        self.assertEqual(self.marker.read_text(), 'image-1\n')
        self.assert_calls(3)

    def test_both_commands_run_in_parallel(self):
        self.run_service(TEST_PARALLEL='yes')
        self.assert_calls(1)
        for command in ('appstreamcli', 'mandb'):
            self.assertTrue((self.events / f'{command}.finished').exists())
        self.assertEqual(self.marker.read_text(), 'image-1\n')

    def test_either_failure_retries_both_and_waits_for_other_job(self):
        for failed, delayed in (('appstreamcli', 'mandb'), ('mandb', 'appstreamcli')):
            with self.subTest(failed=failed):
                self.marker.unlink(missing_ok=True)
                self.log.unlink(missing_ok=True)
                self.run_service(fail=failed, TEST_DELAY=delayed)
                self.assertFalse(self.marker.exists())
                self.assertTrue((self.events / f'{delayed}.finished').exists())
                self.run_service()
                self.assertEqual(self.marker.read_text(), 'image-1\n')
                self.assert_calls(2)

    def test_failed_upgrade_invalidates_marker_and_retries(self):
        self.run_service()
        self.version('image-2')
        self.run_service(fail='mandb')
        self.assertFalse(self.marker.exists())
        self.run_service()
        self.assertEqual(self.marker.read_text(), 'image-2\n')
        self.assert_calls(3)

    def test_rollback_after_failed_upgrade_repairs_previous_caches(self):
        self.run_service()
        self.version('image-2')
        self.run_service(fail='mandb')
        self.version('image-1')
        self.run_service()
        self.assertEqual(self.marker.read_text(), 'image-1\n')
        self.assert_calls(3)

    def test_missing_version_runs_without_recording_success(self):
        self.run_service()
        for contents in ('BUILD_ID=""\n', 'NAME="Anatase"\n'):
            with self.subTest(contents=contents):
                Path('/usr/lib/os-release').write_text(contents)
                self.run_service()
                self.run_service()
                self.assertFalse(self.marker.exists())
        self.assert_calls(5)


if __name__ == '__main__':
    unittest.main()
