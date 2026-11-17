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
    find)
        if [ "$1" = /usr/lib/ludos/sd ]; then
            echo "scan sd payload" >> "$TEST_LOG"
            if [ "${TEST_FAIL:-}" = find ]; then
                exit 1
            fi
        fi
        exec /usr/bin/find "$@"
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
        self.sd_payload = Path('/usr/lib/ludos/sd')
        self.esp = Path('/boot/efi')
        for path in (self.payload, self.sd_payload, self.esp):
            shutil.rmtree(path, ignore_errors=True)
            path.mkdir(parents=True)
        self.work = tempfile.TemporaryDirectory(prefix='efi-test-', dir='/var/tmp')
        self.addCleanup(self.work.cleanup)
        work = Path(self.work.name)
        self.log = work / 'operations'
        self.log.touch()
        self.state = work / 'mount-state'
        self.state.write_text('ro\n')
        for command in ('mountpoint', 'grep', 'mount', 'cp', 'sync', 'mv', 'find'):
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
        for name in ('rpi-u-boot.bin', 'version.txt'):
            self.assertEqual(list(self.esp.glob(f'{name}.*')), [])

    def test_missing_payload_files_and_directories(self):
        for name in ('ANATASE-KEY-ENROLLME.der', 'EFI/anatase/tool.efi'):
            self.write(self.payload, name, name.encode())
        for name in ('config.txt', 'rpi-u-boot.bin', 'overlays/a file.dtbo'):
            self.write(self.sd_payload, name, b'sd only')
        self.run_service()
        for source in self.payload.rglob('*'):
            if source.is_file():
                self.assertEqual((self.esp / source.relative_to(self.payload)).read_bytes(),
                                 source.read_bytes())
        for source in self.sd_payload.rglob('*'):
            self.assertFalse((self.esp / source.relative_to(self.sd_payload)).exists())
        self.assertIn('-o remount,rw /boot/efi', self.log.read_text())
        self.assertTrue(self.log.read_text().endswith('-o remount,ro /boot/efi\n'))

    def test_unchanged_payload_does_not_remount_or_write(self):
        self.write(self.payload, 'ANATASE-KEY-ENROLLME.der', b'same')
        self.write(self.esp, 'ANATASE-KEY-ENROLLME.der', b'same')
        for name in ('config.txt', 'rpi-u-boot.bin', 'bcm2712-rpi-500.dtb', 'version.txt'):
            self.write(self.sd_payload, name, b'same')
            self.write(self.esp, name, b'same')
        self.run_service()
        self.assertEqual(self.log.read_text(), '')

    def test_matching_sd_version_skips_scan_but_still_updates_efi_key(self):
        self.write(self.sd_payload, 'version.txt', b'version\n')
        self.write(self.esp, 'version.txt', b'version\n')
        self.write(self.sd_payload, 'rpi-u-boot.bin', b'new')
        self.write(self.esp, 'rpi-u-boot.bin', b'old')
        self.write(self.esp, 'config.txt', b'custom')
        self.write(self.payload, 'ANATASE-KEY-ENROLLME.der', b'new key')
        self.run_service()
        self.assertNotIn('scan sd payload', self.log.read_text())
        self.assertEqual((self.esp / 'rpi-u-boot.bin').read_bytes(), b'old')
        self.assertEqual((self.esp / 'ANATASE-KEY-ENROLLME.der').read_bytes(), b'new key')

    def test_sd_updates_bootloader_dtbs_and_firmware_but_preserves_config(self):
        managed = ('rpi-u-boot.bin', 'bcm2712-rpi-500.dtb',
                   'overlays/existing.dtbo', 'start4.elf')
        for name in managed:
            self.write(self.sd_payload, name, b'new')
            self.write(self.esp, name, b'old')
        self.write(self.sd_payload, 'overlays/a new file.dtbo', b'added')
        # Create the marker before config.txt to ensure it is explicitly copied last.
        self.write(self.sd_payload, 'version.txt', b'new version\n')
        self.write(self.esp, 'version.txt', b'old version\n')
        self.write(self.sd_payload, 'config.txt', b'default')
        self.write(self.esp, 'config.txt', b'custom')
        self.write(self.payload, 'ANATASE-KEY-ENROLLME.der', b'default')
        self.write(self.esp, 'ANATASE-KEY-ENROLLME.der', b'custom')
        self.write(self.esp, 'unrelated.efi', b'keep')
        self.run_service()
        for name in managed:
            self.assertEqual((self.esp / name).read_bytes(), b'new')
        self.assertEqual((self.esp / 'overlays/a new file.dtbo').read_bytes(), b'added')
        self.assertEqual((self.esp / 'config.txt').read_bytes(), b'custom')
        self.assertEqual((self.esp / 'ANATASE-KEY-ENROLLME.der').read_bytes(), b'default')
        self.assertEqual((self.esp / 'unrelated.efi').read_bytes(), b'keep')
        self.assertEqual((self.esp / 'version.txt').read_bytes(), b'new version\n')
        operations = self.log.read_text().splitlines()
        move_index = next(i for i, op in enumerate(operations)
                          if op.startswith('mv -fT -- /boot/efi/rpi-u-boot.bin.'))
        self.assertTrue(operations[move_index - 1].startswith('sync /boot/efi/rpi-u-boot.bin.'))
        self.assertEqual(operations[move_index + 1], 'sync /boot/efi')
        moves = [op for op in operations if op.startswith('mv ')]
        self.assertTrue(moves[-1].endswith(' /boot/efi/version.txt'))

    def test_changed_efi_files_update_without_sd_config(self):
        for name in ('ANATASE-KEY-ENROLLME.der', 'EFI/anatase/tool.efi'):
            self.write(self.payload, name, b'new')
            self.write(self.esp, name, b'old')
        self.run_service()
        for name in ('ANATASE-KEY-ENROLLME.der', 'EFI/anatase/tool.efi'):
            self.assertEqual((self.esp / name).read_bytes(), b'new')

    def test_failures_preserve_old_bootloader_and_restore_readonly(self):
        self.write(self.sd_payload, 'version.txt', b'new version\n')
        self.write(self.esp, 'version.txt', b'old version\n')
        self.write(self.sd_payload, 'rpi-u-boot.bin', b'new')
        self.write(self.esp, 'config.txt', b'custom')
        for failure in ('cp', 'sync', 'mv'):
            with self.subTest(failure=failure):
                self.write(self.esp, 'rpi-u-boot.bin', b'old')
                self.env['TEST_FAIL'] = failure
                self.run_service(success=False)
                self.assertEqual((self.esp / 'rpi-u-boot.bin').read_bytes(), b'old')
                self.assertEqual((self.esp / 'version.txt').read_bytes(), b'old version\n')
                self.assertTrue(self.log.read_text().endswith('-o remount,ro /boot/efi\n'))

    def test_failed_sd_scan_does_not_publish_version(self):
        self.write(self.sd_payload, 'version.txt', b'new version\n')
        self.write(self.esp, 'version.txt', b'old version\n')
        self.write(self.esp, 'config.txt', b'custom')
        self.env['TEST_FAIL'] = 'find'
        self.run_service(success=False)
        self.assertEqual((self.esp / 'version.txt').read_bytes(), b'old version\n')

    def test_missing_sd_version_is_installed_after_payload(self):
        self.write(self.sd_payload, 'version.txt', b'new version\n')
        self.write(self.sd_payload, 'rpi-u-boot.bin', b'new')
        self.write(self.esp, 'config.txt', b'custom')
        self.run_service()
        self.assertEqual((self.esp / 'rpi-u-boot.bin').read_bytes(), b'new')
        self.assertEqual((self.esp / 'version.txt').read_bytes(), b'new version\n')

    def test_bootloader_is_not_added_to_conventional_efi_installs(self):
        self.write(self.sd_payload, 'rpi-u-boot.bin', b'new')
        self.write(self.sd_payload, 'config.txt', b'default')
        self.run_service()
        self.assertFalse((self.esp / 'config.txt').exists())
        self.assertFalse((self.esp / 'rpi-u-boot.bin').exists())
        self.assertEqual(self.log.read_text(), '')

    def test_sd_payload_is_skipped_without_config_even_if_bootloader_exists(self):
        self.write(self.sd_payload, 'rpi-u-boot.bin', b'new')
        self.write(self.sd_payload, 'bcm2712-rpi-500.dtb', b'new')
        self.write(self.esp, 'rpi-u-boot.bin', b'old')
        self.run_service()
        self.assertEqual((self.esp / 'rpi-u-boot.bin').read_bytes(), b'old')
        self.assertFalse((self.esp / 'bcm2712-rpi-500.dtb').exists())
        self.assertEqual(self.log.read_text(), '')

    def test_sd_only_payload_adds_missing_bootloader_when_config_exists(self):
        shutil.rmtree(self.payload)
        self.write(self.sd_payload, 'rpi-u-boot.bin', b'new')
        self.write(self.esp, 'config.txt', b'custom')
        self.run_service()
        self.assertEqual((self.esp / 'rpi-u-boot.bin').read_bytes(), b'new')
        self.assertEqual((self.esp / 'config.txt').read_bytes(), b'custom')

    def test_unmounted_esp_is_rejected_without_writes(self):
        self.write(self.sd_payload, 'rpi-u-boot.bin', b'new')
        self.env['TEST_MOUNTED'] = 'no'
        self.run_service(success=False)
        self.assertEqual(list(self.esp.iterdir()), [])
        self.assertEqual(self.log.read_text(), '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
