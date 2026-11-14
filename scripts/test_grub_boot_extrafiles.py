"""Run inside a disposable Fedora container; uses its /boot and /usr/lib paths.

podman run --rm --security-opt label=disable -v "$PWD:/repo:ro" \
    localhost/orchestrator:f45-x86_64-3a248727-20261109 \
    python3 /repo/scripts/test_grub_boot_extrafiles.py
"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
MOCK = r'''#!/bin/bash
set -eu
command=${0##*/}
case "$command" in
    mountpoint)
        test "${TEST_MOUNTED:-yes}" = yes
        ;;
    grep)
        if [ "${!#}" = /proc/mounts ]; then
            test "$(cat "$TEST_STATE")" = ro
        else
            exec /usr/bin/grep "$@"
        fi
        ;;
    mount)
        echo "$*" >> "$TEST_LOG"
        echo "${2#remount,}" > "$TEST_STATE"
        ;;
    cp)
        if [ "${TEST_FAIL:-}" = cp ] && [[ "${!#}" = /boot/efi/rpi-u-boot.bin.* ]]; then
            echo partial > "${!#}"
            exit 1
        fi
        exec /usr/bin/cp "$@"
        ;;
    sync|mv)
        echo "$command $*" >> "$TEST_LOG"
        if [ "${TEST_FAIL:-}" = "$command" ]; then
            exit 1
        fi
        exec "/usr/bin/$command" "$@"
        ;;
esac
'''


class ExtraFilesTests(unittest.TestCase):
    def setUp(self):
        if not Path('/run/.containerenv').exists():
            self.fail('Run this test in a disposable Podman container, as documented above.')
        self.payload = Path('/usr/lib/ludos/efi')
        self.esp = Path('/boot/efi')
        for path in (self.payload, self.esp):
            shutil.rmtree(path, ignore_errors=True)
            path.mkdir(parents=True)
        self.work = tempfile.TemporaryDirectory(prefix='efi-test-', dir='/var/tmp')
        self.addCleanup(self.work.cleanup)
        work = Path(self.work.name)
        self.log = work / 'operations'
        self.log.touch()
        self.state = work / 'mount-state'
        self.state.write_text('ro\n')
        for command in ('mountpoint', 'grep', 'mount', 'cp', 'sync', 'mv'):
            wrapper = work / command
            wrapper.write_text(MOCK)
            wrapper.chmod(0o755)
        Path('/usr/libexec').mkdir(exist_ok=True)
        shutil.copyfile(REPO / 'cards/base/grub/grub-boot-remount',
                        '/usr/libexec/grub-boot-remount')
        self.env = dict(os.environ, PATH=f'{work}:/usr/bin:/bin',
                        TEST_LOG=str(self.log), TEST_STATE=str(self.state))

    def write(self, root, name, data):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def run_service(self, success=True):
        result = subprocess.run(['bash', str(REPO / 'cards/base/grub/grub-boot-extrafiles')],
                                env=self.env, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.state.read_text(), 'ro\n')
        self.assertEqual(list(self.esp.glob('rpi-u-boot.bin.*')), [])

    def test_missing_payload_files_and_directories(self):
        self.write(self.payload, 'rpi-u-boot.bin', b'new')
        for name in ('ANATASE-KEY-ENROLLME.der', 'overlays/a file.dtbo'):
            self.write(self.payload, name, name.encode())
        self.run_service()
        for source in self.payload.rglob('*'):
            if source.is_file() and source.name != 'rpi-u-boot.bin':
                self.assertEqual((self.esp / source.relative_to(self.payload)).read_bytes(),
                                 source.read_bytes())
        self.assertFalse((self.esp / 'rpi-u-boot.bin').exists())
        self.assertIn('-o remount,rw /boot/efi', self.log.read_text())
        self.assertTrue(self.log.read_text().endswith('-o remount,ro /boot/efi\n'))

    def test_unchanged_payload_does_not_remount_or_write(self):
        for name in ('rpi-u-boot.bin', 'ANATASE-KEY-ENROLLME.der'):
            self.write(self.payload, name, b'same')
            self.write(self.esp, name, b'same')
        self.run_service()
        self.assertEqual(self.log.read_text(), '')

    def test_changed_uboot_preserves_configuration_and_other_files(self):
        self.write(self.payload, 'rpi-u-boot.bin', b'new')
        self.write(self.esp, 'rpi-u-boot.bin', b'old')
        for name in ('config.txt', 'ANATASE-KEY-ENROLLME.der', 'overlays/existing.dtbo'):
            self.write(self.payload, name, b'default')
            self.write(self.esp, name, b'custom')
        self.write(self.esp, 'unrelated.efi', b'keep')
        self.run_service()
        self.assertEqual((self.esp / 'rpi-u-boot.bin').read_bytes(), b'new')
        for name in ('config.txt', 'ANATASE-KEY-ENROLLME.der', 'overlays/existing.dtbo'):
            self.assertEqual((self.esp / name).read_bytes(), b'custom')
        self.assertEqual((self.esp / 'unrelated.efi').read_bytes(), b'keep')
        operations = self.log.read_text().splitlines()
        self.assertTrue(operations[1].startswith('sync /boot/efi/rpi-u-boot.bin.'))
        self.assertTrue(operations[2].startswith('mv -fT -- /boot/efi/rpi-u-boot.bin.'))
        self.assertEqual(operations[3], 'sync /boot/efi')

    def test_failures_preserve_old_bootloader_and_restore_readonly(self):
        self.write(self.payload, 'rpi-u-boot.bin', b'new')
        for failure in ('cp', 'sync', 'mv'):
            with self.subTest(failure=failure):
                self.write(self.esp, 'rpi-u-boot.bin', b'old')
                self.env['TEST_FAIL'] = failure
                self.run_service(success=False)
                self.assertEqual((self.esp / 'rpi-u-boot.bin').read_bytes(), b'old')
                self.assertTrue(self.log.read_text().endswith('-o remount,ro /boot/efi\n'))

    def test_bootloader_is_not_added_to_conventional_efi_installs(self):
        self.write(self.payload, 'rpi-u-boot.bin', b'new')
        self.run_service()
        self.assertFalse((self.esp / 'rpi-u-boot.bin').exists())
        self.assertEqual(self.log.read_text(), '')

    def test_unmounted_esp_is_rejected_without_writes(self):
        self.write(self.payload, 'rpi-u-boot.bin', b'new')
        self.env['TEST_MOUNTED'] = 'no'
        self.run_service(success=False)
        self.assertEqual(list(self.esp.iterdir()), [])
        self.assertEqual(self.log.read_text(), '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
