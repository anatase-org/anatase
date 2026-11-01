"""Run with python3 -m unittest discover -s scripts/iso-test -v."""

import argparse
import base64
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

import host
from protocol import Channel, ProtocolError
from firmware import console_nodes


spec = importlib.util.spec_from_file_location("iso_guest", Path(__file__).with_name("guest.py"))
guest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guest)


class Channels(unittest.TestCase):
    def setUp(self):
        cache = host.ROOT / "cache/iso-test-unit"
        cache.mkdir(parents=True, exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=cache)
        self.path = str(Path(self.directory.name, "rpc.sock"))
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(self.path)
        self.listener.listen()
        self.errors = []

    def serve(self, handler):
        def target():
            try:
                handler()
            except BaseException as exc:
                self.errors.append(exc)
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        self.thread = thread

    def tearDown(self):
        self.listener.close()
        if hasattr(self, "thread"):
            self.thread.join(timeout=3)
            self.assertFalse(self.thread.is_alive(), "RPC server did not finish")
        self.directory.cleanup()
        if self.errors:
            raise self.errors[0]

    def test_qmp_events_errors_and_reconnection(self):
        def server():
            for iteration in range(2):
                connection, _ = self.listener.accept()
                with connection, connection.makefile("rb") as stream:
                    connection.sendall(b'{"QMP": {}}\n')
                    capabilities = json.loads(stream.readline())
                    connection.sendall(json.dumps({"return": {}, "id": capabilities["id"]}).encode() + b'\n')
                    request = json.loads(stream.readline())
                    connection.sendall(b'{"event":"RESET"}\n')
                    reply = {"id": request["id"]}
                    reply.update({"error": {"desc": "injected"}} if iteration == 0 else {"return": {"status": "running"}})
                    connection.sendall(json.dumps(reply).encode() + b'\n')
        self.serve(server)
        channel = Channel(self.path, timeout=2)
        with self.assertRaisesRegex(ProtocolError, "injected"):
            channel.call("query-status")
        self.assertEqual(channel.call("query-status"), {"status": "running"})
        channel.close()

    def test_agent_resynchronizes_after_reboot_and_captures_exit(self):
        def server():
            for _ in range(2):
                connection, _ = self.listener.accept()
                with connection, connection.makefile("rb") as stream:
                    sync = json.loads(stream.readline().lstrip(b'\xff'))
                    connection.sendall(b'stale response\n\xff' + json.dumps({"return": sync["arguments"]["id"]}).encode() + b'\n')
                    request = json.loads(stream.readline())
                    self.assertEqual(request["execute"], "guest-exec")
                    connection.sendall(b'{"return":{"pid":17}}\n')
                    json.loads(stream.readline())
                    reply = {"return": {"exited": True, "exitcode": 7,
                                        "err-data": base64.b64encode(b"app failed").decode()}}
                    connection.sendall(json.dumps(reply).encode() + b'\n')
        self.serve(server)
        channel = Channel(self.path, agent=True, timeout=2)
        for _ in range(2):
            result = channel.execute(["/bin/false"])
            self.assertEqual(result["code"], 7)
            self.assertEqual(result["stderr"], "app failed")
            channel.close()


class Acceptance(unittest.TestCase):
    def make_harness(self, *, arm=False, accel="kvm"):
        cache = host.ROOT / "cache/iso-test-unit"
        cache.mkdir(parents=True, exist_ok=True)
        directory = tempfile.TemporaryDirectory(dir=cache)
        self.addCleanup(directory.cleanup)
        return host.Harness(argparse.Namespace(arm=arm, iso=Path("test.iso")),
                            {"base": Path(directory.name), "accel": accel})

    def test_arm_pflash_allows_native_kvm_without_trustzone(self):
        for overrides in ({}, {"QEMU_ACCEL": "kvm"}):
            with self.subTest(overrides=overrides), patch.dict("os.environ", overrides, clear=True), \
                    patch.object(host, "firmware", return_value=(Path("code.fd"), Path("vars.fd"))), \
                    patch.object(host.platform, "machine", return_value="aarch64"), \
                    patch.object(host.os, "access", return_value=True), \
                    patch.object(host.shutil, "which", return_value="available"), \
                    patch.object(host.shutil, "disk_usage", return_value=Mock(free=30 * 1024**3)), \
                    patch.object(host, "run", side_effect=["eng", '{"filesystems":[{"fstype":"ext4"}]}']):
                config = host.preflight(argparse.Namespace(arm=True, iso=Path(__file__)))
                self.assertEqual(config["accel"], "kvm")

    def test_qemu_cpu_and_secure_boot_firmware_configuration(self):
        cases = [(True, "tcg", ".fd", {}, "neoverse-n1"),
                 (True, "kvm", ".fd", {}, "host"),
                 (True, "tcg", ".json", {}, "neoverse-n1"),
                 (True, "kvm", ".json", {}, "host"),
                 (False, "tcg", ".fd", {}, "max"),
                 (False, "kvm", ".fd", {}, "host"),
                 (True, "tcg", ".fd", {"QEMU_CPU": "cortex-a57", "QEMU_MACHINE": "virt,gic-version=3"},
                  "cortex-a57")]
        for arm, accel, suffix, overrides, cpu in cases:
            with self.subTest(arm=arm, accel=accel, suffix=suffix, overrides=overrides), \
                    patch.dict("os.environ", overrides, clear=True):
                h = self.make_harness(arm=arm, accel=accel)
                template = h.directory / ("template" + suffix)
                template.write_text("fresh enrolled firmware variables")
                h.config.update(binary="qemu", image_binary="qemu-img", firmware=Path("secure-boot.fd"),
                                template=template)
                h.wait = Mock()
                process = Mock()
                process.poll.return_value = 0
                self.addCleanup(h.cleanup)
                with patch.object(host, "run"), patch.object(host.subprocess, "Popen", return_value=process):
                    h.launch_vm()
                argv = json.loads((h.directory / "qemu-command.json").read_text())
                self.assertEqual(argv[argv.index("-cpu") + 1], cpu)
                machine = argv[argv.index("-machine") + 1]
                self.assertNotIn("secure=on", machine)
                if arm:
                    self.assertEqual(machine, overrides.get("QEMU_MACHINE", "virt"))
                else:
                    self.assertIn("smm=on", machine)
                    self.assertIn("driver=cfi.pflash01,property=secure,value=on", argv)
                variables = h.directory / ("vars" + suffix)
                self.assertEqual(variables.read_text(), template.read_text())
                if suffix == ".fd":
                    self.assertIn("if=pflash,format=raw,unit=0,readonly=on,file=secure-boot.fd", argv)
                    self.assertIn(f"if=pflash,format=raw,unit=1,file={variables}", argv)
                else:
                    self.assertIn(f"uefi-vars-sysbus,jsonfile={variables}", argv)

    def test_failure_report_survives_diagnostics_failure(self):
        h = self.make_harness()
        h.diagnostics = Mock(side_effect=RuntimeError("diagnostics failed too"))
        output = io.StringIO()
        with redirect_stdout(output):
            h.stage("injected installation failure", Mock(side_effect=RuntimeError("installer failed")), fatal=False)
        report = json.loads((h.directory / "results.json").read_text())
        self.assertEqual(report["stages"][0]["status"], "failed")
        self.assertIn("installer failed", report["stages"][0]["error"])
        self.assertIn("installer failed", output.getvalue())
        self.assertIn("diagnostics failed too", output.getvalue())

    def test_failed_health_keeps_structured_check_results(self):
        h = self.make_harness()
        h.diagnostics = Mock()
        details = {"checks": {"btrfs": {"filesystems": ["scrubbed"]}}, "errors": ["crash"]}
        h.agent.execute = Mock(return_value={"code": 1, "truncated": False, "stderr": "",
                                            "stdout": json.dumps({"error": "crash", "details": details})})
        output = io.StringIO()
        with redirect_stdout(output):
            h.stage("health", lambda: h.guest("health"), fatal=False)
        report = json.loads((h.directory / "results.json").read_text())
        self.assertEqual(report["stages"][0]["result"], details)
        self.assertEqual(report["stages"][0]["error"], "Guest health: crash")
        self.assertIn('"crash"', output.getvalue())
        self.assertNotIn("scrubbed", output.getvalue())

    def test_failed_app_prints_screen_and_guest_logs_to_console(self):
        h = self.make_harness()
        h.helper_ready = True
        h.ui.capture = Mock(return_value="Okular: fixture.pdf could not be opened")
        h.guest = Mock(return_value={"journal": "application crashed", "coredumps": "Stack trace: portal",
                                     "/home/isotest/.local/state/anatase-iso-test/launch.log": "flatpak: launch error"})
        (h.directory / "qemu.log").write_text("QEMU diagnostic")
        (h.directory / "serial.log").write_text("firmware diagnostic")
        output = io.StringIO()
        with redirect_stdout(output):
            h.stage("live: org.anatase.DocumentViewer",
                    Mock(side_effect=TimeoutError("waiting for visible window")), fatal=False)
        for expected in ("FAILED: live: org.anatase.DocumentViewer", "waiting for visible window",
                         "fixture.pdf could not be opened", "application crashed", "Stack trace: portal",
                         "flatpak: launch error", "QEMU diagnostic", "firmware diagnostic"):
            if expected in ("Stack trace: portal", "QEMU diagnostic", "firmware diagnostic"):
                self.assertNotIn(expected, output.getvalue())
            else:
                self.assertIn(expected, output.getvalue())

    def test_status_is_printed_without_allowed_coredump_details(self):
        h = self.make_harness()
        h.guest = Mock(return_value={"coredumps": [{"allowed": True, "exe": "portal", "pid": 123,
                                                    "user": "plasmalogin", "sig": 6}],
                                     "coredump_info": "Stack trace: known greeter abort"})
        output = io.StringIO()
        with redirect_stdout(output):
            result = h.stage("Installed health", h.collect_health)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(output.getvalue(), "==> Installed health\n")
        self.assertTrue(result["result"]["coredumps"][0]["allowed"])
        self.assertIn("Stack trace: known greeter abort", result["result"]["coredump_info"])

    def test_health_failure_only_prints_errors_and_unexpected_crashes(self):
        h = self.make_harness()
        h.diagnostics = Mock()
        details = {"checks": {"plasmalogin.service": "active", "btrfs": {"scrub": "healthy filesystem"},
                              "coredumps": [{"allowed": True, "exe": "allowed-portal", "pid": 123},
                                            {"allowed": False, "exe": "/usr/bin/kate", "user": "isotest", "pid": 456, "sig": 11}],
                              "coredump_info": "Module libunrelated.so\nStack trace: kate"},
                   "errors": ["Guest coredumps detected"]}
        output = io.StringIO()
        with redirect_stdout(output):
            h.stage("Installed health", Mock(side_effect=host.GuestFailure(
                "health", {"error": "Guest coredumps detected", "details": details})), fatal=False)
        self.assertIn("/usr/bin/kate user=isotest pid=456 signal=11", output.getvalue())
        for omitted in ("allowed-portal", "healthy filesystem", "libunrelated.so", "plasmalogin.service"):
            self.assertNotIn(omitted, output.getvalue())
        self.assertEqual(h.records[0]["result"], details)
        h.diagnostics.assert_called_once_with("Installed health", console=False)

    def test_success_diagnostics_failures_do_not_print(self):
        h = self.make_harness()
        h.helper_ready = True
        h.ui.capture = Mock(side_effect=RuntimeError("screen unavailable"))
        h.guest = Mock(side_effect=RuntimeError("agent unavailable"))
        output = io.StringIO()
        with redirect_stdout(output):
            h.diagnostics("final")
        self.assertEqual(output.getvalue(), "")

    def test_console_log_tails_are_labeled_and_cannot_inject_actions_commands(self):
        h = self.make_harness()
        output = io.StringIO()
        with redirect_stdout(output):
            h.console_details("log", "first\nsecond\n::error::guest output", tail=2)
        self.assertIn("last 2 of 3 lines", output.getvalue())
        self.assertNotIn("first", output.getvalue())
        self.assertIn("\n    ::error::guest output", output.getvalue())

    def test_missing_app_does_not_pass_installed_inventory(self):
        h = self.make_harness()
        h.expected = ["app/org.anatase.Calculator/x86_64/stable"]
        h.guest = Mock(return_value={"refs": [], "snapshot": []})
        with self.assertRaisesRegex(RuntimeError, "missing bundled"):
            h.flatpak_suite("installed")

    def test_early_exiting_app_has_no_successful_window(self):
        h = self.make_harness()
        h.app_timeout = 0.02
        h.guest = Mock(return_value="")
        with patch("host.time.sleep"):
            with self.assertRaises(TimeoutError):
                h.app("org.anatase.Calculator", "isotest", "/home/isotest/Documents/test")

    def test_taskbar_button_does_not_count_as_a_rendered_application_window(self):
        h = self.make_harness()
        h.ui.nodes = [{"app": "plasmashell", "role": "button", "name": "Text Editor (Kate)",
                       "visible": True, "rect": [0, 700, 100, 30]}]
        self.assertFalse(h.ui.application_window_visible(r"Kate|fixture.txt"))
        h.ui.nodes.append({"app": "kate", "role": "frame", "name": "fixture.txt — Kate",
                           "visible": True, "rect": [100, 100, 800, 600]})
        self.assertTrue(h.ui.application_window_visible(r"Kate|fixture.txt"))

    def test_live_bootstrap_accepts_wrapped_desktop_icon_caption(self):
        for caption in (("Anatase Installer",), ("Anatase", "Installer")):
            with self.subTest(caption=caption):
                h = self.make_harness()
                h.agent.execute = Mock(side_effect=[{"stdout": "system_u:system_r:virt_qemu_ga_t:s0"},
                                                    {"stdout": "system_u:system_r:unconfined_service_t:s0"}])
                h.wait_session = Mock()
                h.install_helper = Mock()
                h.ui.capture = Mock()
                h.ui.words = [{"name": text, "rect": [30, 80 + 17 * i, 99, 11], "ocr": True}
                              for i, text in enumerate(caption)]
                h.ui.wait = Mock()
                h.ui.key = Mock()
                h.ui.type = Mock()
                h.bootstrap_agent()
                h.ui.key.assert_called_once_with("ctrl", "alt", "t")
                self.assertIn("--bootstrap-agent", h.ui.type.call_args_list[0].args[0])

    def test_screenshot_preserves_pixels_after_gtk_resize_to_unaligned_width(self):
        from PIL import Image
        h = self.make_harness()
        expected = Image.new("RGB", (1049, 80))
        for row in range(expected.height):
            expected.paste((row, 90, 120), (0, row, expected.width, row + 1))

        def screendump(command, arguments):
            self.assertEqual(command, "screendump")
            if arguments.get("format") == "png":
                expected.save(arguments["filename"], format="PNG")
            else:
                # QEMU's default PPM export writes an aligned stride, while
                # PPM readers expect packed RGB rows. 1049 pixels adds 3 bytes.
                rows = expected.tobytes()
                stride = expected.width * 3
                payload = b"".join(rows[y * stride:(y + 1) * stride] + b"\0" * 3
                                   for y in range(expected.height))
                Path(arguments["filename"]).write_bytes(b"P6\n1049 80\n255\n" + payload)

        h.qmp.call = Mock(side_effect=screendump)
        with patch("host.subprocess.run", return_value=Mock(returncode=0, stdout=b"", stderr=b"")):
            h.ui.capture("resized", accessibility=False)
        with Image.open(h.ui.last_image) as actual:
            self.assertEqual(actual.size, expected.size)
            self.assertEqual(actual.tobytes(), expected.tobytes())

    def test_ocr_timeout_retries_within_ui_deadline_and_preserves_evidence(self):
        from PIL import Image

        h = self.make_harness()
        h.qmp.call = Mock(side_effect=lambda command, arguments:
                          Image.new("RGB", (32, 32)).save(arguments["filename"]))
        frames = 0

        def ready():
            nonlocal frames
            h.ui.capture("ocr-retry", accessibility=False)
            frames += 1
            return True

        with patch("host.subprocess.run", side_effect=[subprocess.TimeoutExpired("tesseract", 30),
                   Mock(returncode=0, stdout=b"", stderr=b"")]) as ocr, patch("host.time.sleep"):
            h.wait(ready, 5, "control after a slow frame")
        self.assertEqual(frames, 1)
        self.assertEqual(ocr.call_count, 2)
        self.assertEqual(ocr.call_args.kwargs["env"]["OMP_THREAD_LIMIT"], "1")
        evidence = json.loads((h.directory / "00001-ocr-retry.json").read_text())
        self.assertIn("timed out", evidence["ocr_error"])
        self.assertTrue((h.directory / "00001-ocr-retry.png").is_file())

    def test_live_boot_polls_agent_without_ocr_of_linux_console_after_enrollment(self):
        h = self.make_harness(arm=True, accel="tcg")
        h.enrollment_seen = True
        (h.directory / "serial.log").write_text("Starting dracut-initqueue.service - dracut initqueue hook...\n")
        h.install_helper = Mock(side_effect=[TimeoutError("agent not ready"), True])
        h.bootstrap_agent = Mock()
        h.wait_session = Mock()
        boot = {"time": "2026-11-01", "cmdline": "rd.live.image"}
        h.guest = Mock(side_effect=[{"enabled": True}, boot])
        h.ui.capture = Mock()
        with patch("host.time.sleep"):
            self.assertEqual(h.boot_live(), boot)
        self.assertEqual(h.install_helper.call_count, 2)
        h.ui.capture.assert_called_once_with("live-desktop")
        self.assertEqual(h.report["secure_boot"], {"enabled": True})

    def test_remaining_apps_are_checked_after_one_fails(self):
        h = self.make_harness()
        refs = ["app/org.anatase.Calculator/x86_64/stable", "app/org.anatase.TextEditor/x86_64/stable"]
        h.guest = Mock(side_effect=lambda action, **kwargs: {"refs": refs, "snapshot": refs}
                       if action == "inventory" else "/home/isotest/Documents/test")
        h.app = Mock(side_effect=[RuntimeError("early exit"), {"passed": True}])
        h.diagnostics = Mock()
        h.flatpak_suite("installed")
        self.assertEqual(h.app.call_count, 2)
        self.assertEqual([x["status"] for x in h.records], ["failed", "passed"])

    def test_unknown_app_fails_without_launching(self):
        h = self.make_harness()
        h.guest = Mock()
        with self.assertRaisesRegex(RuntimeError, "refusing to skip"):
            h.app("org.example.Unknown", "isotest", "/home/isotest/Documents/test")
        h.guest.assert_not_called()

    def test_cleanup_only_terminates_owned_qemu(self):
        h = self.make_harness()
        h.process = Mock()
        h.process.poll.return_value = None
        h.cleanup()
        h.process.terminate.assert_called_once()
        h.process.wait.assert_called_once_with(timeout=10)

    def test_stage_timeout_fails_run_and_terminates_owned_vm(self):
        h = self.make_harness()
        h.process = Mock()
        h.process.poll.return_value = None
        h.launch_vm = Mock(return_value={"pid": 123})
        h.diagnostics = Mock()
        h.deadline = time.monotonic() - 1
        h.boot_live = lambda: h.wait(lambda: False, 10, "guest boot")
        self.assertEqual(h.execute(), 1)
        report = json.loads((h.directory / "results.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertIn("Timed out", report["error"])
        h.process.terminate.assert_called_once()

    def test_existing_vm_overrides_are_rejected_before_allocation(self):
        with patch.dict("os.environ", {"VM_DISK": str(host.ROOT / "cache/vm.raw")}):
            with self.assertRaisesRegex(RuntimeError, "must be fresh"):
                host.preflight(argparse.Namespace(arm=False, iso=Path(__file__)))

    def test_firmware_selection_uses_highlight_and_visual_order(self):
        h = self.make_harness()
        nodes = {"first": {"rect": [0, 10, 30, 10], "dark_background": False},
                 "second": {"rect": [0, 30, 30, 10], "dark_background": True}}
        h.ui.find = nodes.get
        h.ui.key = Mock()
        h.firmware_select("first", ["second", "first"])
        self.assertEqual(h.ui.key.call_args_list, [unittest.mock.call("up"), unittest.mock.call("ret")])

    def test_disabled_button_is_not_reactivated_by_ocr(self):
        h = self.make_harness()
        h.ui.nodes = [{"name": "Install", "role": "button", "visible": True, "enabled": False,
                       "rect": [10, 10, 100, 30]}]
        h.ui.words = [{"name": "Install", "rect": [10, 10, 100, 30], "ocr": True}]
        self.assertIsNone(h.ui.find(r"^Install$"))

    def test_qt_password_placeholder_identifies_unnamed_input(self):
        h = self.make_harness()
        field = {"path": [0, 1], "name": "", "role": "password text",
                 "rect": [10, 20, 200, 30], "visible": True, "enabled": True}
        h.ui.nodes = [field, {"path": [0, 1, 0], "name": "Password", "role": "label",
                             "visible": True, "enabled": False}]
        self.assertIs(h.ui.find(r"^Password$", roles=("password text",)), field)

    def test_unnamed_result_field_is_checked_by_visible_text(self):
        h = self.make_harness()
        field = {"name": "", "text": "42", "role": "text", "visible": True, "enabled": True,
                 "rect": [10, 10, 100, 30]}
        h.ui.nodes = [field]
        self.assertIs(h.ui.find(r"^42$"), field)

    def test_wayland_buttons_use_accessible_action_not_wrong_global_coordinates(self):
        h = self.make_harness()
        h.ui.user = "isotest"
        h.guest = Mock(return_value="activated")
        node = {"path": [1, 0], "name": "Next", "role": "button", "rect": [0, 0, 100, 30]}
        h.ui.click_node(node)
        h.guest.assert_called_once_with("a11y-action", user="isotest", node=node, mode="activate")

    def test_already_focused_document_does_not_need_unsupported_refocus(self):
        node = Mock()
        node.name = "fixture.txt"
        node.getRoleName.return_value = "text"
        node.getState.return_value.contains.return_value = True
        node.queryComponent.side_effect = AssertionError("KTextEditor cannot grabFocus")
        api = Mock()
        api.Registry.getDesktop.return_value = node
        request = {"mode": "focus", "node": {"name": "fixture.txt", "role": "text", "path": []}}
        with patch.dict(sys.modules, {"pyatspi": api}):
            self.assertEqual(guest.accessible_action(request), "focused")
        node.queryComponent.assert_not_called()

    def test_firmware_ocr_spacing_and_button_borders(self):
        h = self.make_harness()
        h.ui.words = [{"name": "Cont inue", "rect": [10, 10, 100, 30]},
                      {"name": "| Test interaction |", "rect": [10, 50, 100, 30]}]
        self.assertIsNotNone(h.ui.find(r"^Continue$"))
        self.assertIsNotNone(h.ui.find(r"^Test interaction$"))

    def test_interrupt_is_recorded_and_never_continues_app_suite(self):
        h = self.make_harness()
        h.diagnostics = Mock()
        with self.assertRaises(KeyboardInterrupt):
            h.stage("interrupted app", Mock(side_effect=KeyboardInterrupt()), fatal=False)
        self.assertEqual(h.records[-1]["status"], "failed")
        h.diagnostics.assert_not_called()

    def test_rendered_fixture_tolerates_unrelated_desktop_icon_pixels(self):
        from PIL import Image, ImageDraw
        h = self.make_harness()
        image = Image.new("RGB", (500, 300), "white")
        draw = ImageDraw.Draw(image)
        for left, color in ((30, "#d23456"), (180, "#42b883"), (330, "#2255aa")):
            draw.rectangle((left, 60, left + 70, 130), fill=color)
        image.putpixel((490, 290), (210, 52, 86))
        image.putpixel((0, 0), (34, 85, 170))
        path = h.directory / "rendered.png"
        image.save(path)
        self.assertTrue(host.image_fixture_visible(path))
        Image.new("RGB", image.size, "white").save(path)
        self.assertFalse(host.image_fixture_visible(path))

    def test_reboot_detection_does_not_depend_on_helper_in_run(self):
        h = self.make_harness()
        h.agent.execute = Mock(side_effect=[{"code": 0, "stdout": "old\n"}, {"code": 0, "stdout": "new\n"}])
        h.guest = Mock(side_effect=RuntimeError("helper absent after reboot"))
        with patch("host.time.sleep"):
            h.wait_new_boot("old")
        h.guest.assert_not_called()

    def test_ejection_removes_medium_rather_than_only_opening_tray(self):
        h = self.make_harness()
        h.qmp.call = Mock(side_effect=[{"status": "shutdown"}, {}, {}, [{"device": "installer_iso", "removable": True}]])
        h.eject_iso()
        self.assertEqual(h.qmp.call.call_args_list[2],
                         unittest.mock.call("blockdev-remove-medium", {"id": "installer_cd"}))
        self.assertTrue(h.report["iso_ejected"])

    def test_ejection_fails_if_medium_remains_inserted(self):
        h = self.make_harness()
        h.qmp.call = Mock(side_effect=[{"status": "shutdown"}, {}, {}, [{"device": "installer_iso", "inserted": {"file": "test.iso"}}]])
        with self.assertRaisesRegex(RuntimeError, "still inserted"):
            h.eject_iso()

    def test_live_iso_cannot_be_removed_while_guest_is_running(self):
        h = self.make_harness()
        h.qmp.call = Mock(return_value={"status": "running"})
        with self.assertRaisesRegex(RuntimeError, "complete shutdown"):
            h.eject_iso()
        h.qmp.call.assert_called_once_with("query-status")


class FirmwareFiles(unittest.TestCase):
    def test_ubuntu_secure_boot_code_symlinks_use_target_sizes(self):
        cache = host.ROOT / "cache/iso-test-unit"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            root = Path(directory)
            for arm, code_size, vars_size in ((False, 3653632, 540672), (True, 64 * 1024**2, 64 * 1024**2)):
                with self.subTest(arm=arm):
                    code = root / f"code-{arm}.secboot.fd"
                    variables = root / f"vars-{arm}.ms.fd"
                    # Sparse fixtures stay on disk and match Ubuntu's flash sizes.
                    for path, size in ((code, code_size), (variables, vars_size)):
                        with path.open("wb") as stream:
                            stream.truncate(size)
                    alias = root / f"code-{arm}.ms.fd"
                    alias.symlink_to(code.name)
                    with patch.dict("os.environ", {"QEMU_OVMF_CODE": str(alias),
                                                   "QEMU_OVMF_VARS_TEMPLATE": str(variables)}):
                        self.assertEqual(host.firmware(arm), (code.resolve(), variables.resolve()))


class FilesystemHealth(unittest.TestCase):
    def test_coredump_exception_is_limited_to_setup_and_greeter_portal_sigabrt(self):
        entries = [
            {"exe": "/usr/libexec/xdg-desktop-portal-kde", "uid": 978, "sig": 6},
            {"exe": "/usr/libexec/xdg-desktop-portal-kde", "uid": 1000, "sig": 6},
            {"exe": "/usr/libexec/xdg-desktop-portal-kde", "uid": 978, "sig": 11},
            {"exe": "/usr/bin/plasmashell", "uid": 978, "sig": 6},
            {"exe": "/usr/libexec/xdg-desktop-portal-kde", "uid": 999, "sig": 6},
        ]
        for user in ("plasmalogin", "plasma-setup"):
            def account(uid):
                if uid == 999:
                    raise KeyError(uid)
                return Mock(pw_name=user if uid == 978 else "isotest")
            with self.subTest(user=user), \
                 patch.object(guest.subprocess, "run", return_value=Mock(returncode=0, stdout=json.dumps(entries))), \
                 patch.object(guest.pwd, "getpwuid", side_effect=account):
                crashes = guest.coredumps("today")
            self.assertEqual([c["allowed"] for c in crashes], [True, False, False, False, False])
            self.assertEqual(crashes[0]["user"], user)
            self.assertTrue(crashes[0]["allow_reason"])

    def test_allowed_coredumps_keep_evidence_without_failing_health(self):
        allowed = {"exe": "/usr/libexec/xdg-desktop-portal-kde", "allowed": True}
        for unexpected in (False, True):
            with self.subTest(unexpected=unexpected), \
                 patch.object(guest, "command", return_value="stack trace and service state"), \
                 patch.object(guest, "as_user", return_value="active"), \
                 patch.object(guest, "coredumps", return_value=[allowed] + ([{"allowed": False}] if unexpected else [])), \
                 patch.object(guest, "btrfs_health", return_value={"filesystems": ["checked"]}):
                if unexpected:
                    with self.assertRaisesRegex(guest.CheckFailure, "Guest coredumps detected"):
                        guest.health({"user": "isotest", "since": "today"})
                else:
                    result = guest.health({"user": "isotest", "since": "today"})
                    self.assertEqual(result["coredumps"], [allowed])
                    self.assertIn("stack trace", result["coredump_info"])

    def test_crashes_do_not_prevent_filesystem_checks(self):
        with patch.object(guest, "command", return_value="active"), \
             patch.object(guest, "as_user", return_value="active"), \
             patch.object(guest, "coredumps", return_value=[{"exe": "portal", "sig": 6}]), \
             patch.object(guest, "btrfs_health", return_value={"filesystems": ["checked"]}) as scrub:
            with self.assertRaises(RuntimeError) as caught:
                guest.health({"user": "isotest", "since": "today"})
        scrub.assert_called_once()
        details = caught.exception.details
        self.assertEqual(details["checks"]["btrfs"]["filesystems"], ["checked"])
        self.assertIn("Guest coredumps detected", details["errors"])

    def test_coredump_query_errors_are_not_treated_as_no_crashes(self):
        with patch.object(guest.subprocess, "run", return_value=Mock(returncode=1, stdout="", stderr="Permission denied")):
            with self.assertRaisesRegex(RuntimeError, "Permission denied"):
                guest.coredumps("today")
        with patch.object(guest.subprocess, "run", return_value=Mock(returncode=1, stdout="", stderr="No coredumps found.\n")):
            self.assertEqual(guest.coredumps("today"), [])

    def test_error_on_one_filesystem_does_not_skip_other_filesystems(self):
        calls = []
        def command(argv, **kwargs):
            calls.append(argv)
            if argv[0] == "findmnt":
                return '{"filesystems":[{"target":"/var","uuid":"a"},{"target":"/data","uuid":"b"}]}'
            if argv[:3] == ["btrfs", "scrub", "start"] and argv[-1] == "/var":
                raise RuntimeError("scrub error")
            return ""
        with patch.object(guest, "command", side_effect=command):
            with self.assertRaisesRegex(RuntimeError, "scrub error"):
                guest.btrfs_health()
        self.assertIn(["btrfs", "device", "stats", "-c", "/var"], calls)
        self.assertIn(["btrfs", "scrub", "start", "-B", "-r", "/data"], calls)

    def test_device_errors_fail_without_resetting_counters(self):
        def command(argv, **kwargs):
            if argv[0] == "findmnt":
                return '{"filesystems":[{"target":"/var","uuid":"abc"}]}'
            if argv[:3] == ["btrfs", "device", "stats"]:
                self.assertIn("-c", argv)
                self.assertNotIn("-z", argv)
                raise RuntimeError("corruption_errs 1")
            return "scrub done"
        with patch.object(guest, "command", side_effect=command):
            with self.assertRaisesRegex(RuntimeError, "corruption_errs"):
                guest.btrfs_health()


    def test_scrub_is_readonly_and_deduplicates_subvolumes(self):
        calls = []
        def command(argv, **kwargs):
            calls.append(argv)
            if argv[0] == "findmnt":
                return '{"filesystems":[{"target":"/var","uuid":"abc","children":[{"target":"/var/home","uuid":"abc"}]}]}'
            return ""
        with patch.object(guest, "command", side_effect=command):
            result = guest.btrfs_health()
        self.assertEqual(len(result["filesystems"]), 1)
        self.assertIn(["btrfs", "scrub", "start", "-B", "-r", "/var"], calls)

    def test_kernel_corruption_fails_even_with_clean_counters(self):
        def command(argv, **kwargs):
            if argv[0] == "findmnt":
                return '{"filesystems":[{"target":"/var","uuid":"abc"}]}'
            return "BTRFS error (device vda3): corrupt leaf" if argv[0] == "journalctl" else ""
        with patch.object(guest, "command", side_effect=command):
            with self.assertRaisesRegex(RuntimeError, "corrupt leaf"):
                guest.btrfs_health()

    def test_no_btrfs_is_allowed_only_in_live_environment(self):
        with patch.object(guest, "command", return_value=""):
            self.assertTrue(guest.btrfs_health(live=True)["live_has_no_btrfs"])
            with self.assertRaisesRegex(RuntimeError, "no mounted Btrfs"):
                guest.btrfs_health()


class FirmwareConsole(unittest.TestCase):
    def test_current_screen_and_selected_row(self):
        screen = "\x1b[8;25;80t\x1b[2J\x1b[1;1HEnroll the key(s)?"
        screen += "\x1b[40m\x1b[10;30HNo\x1b[44m\x1b[11;30HYes"
        nodes = console_nodes(screen)
        self.assertEqual([node["name"] for node in nodes], ["Enroll the key(s)?", "No", "Yes"])
        self.assertEqual([node["dark_background"] for node in nodes], [False, True, False])

    def test_clear_discards_previous_enrollment_screen(self):
        screen = "\x1b[1;1HEnroll MOK\x1b[2J\x1b[1;1HPerform MOK management\x1b[40m\x1b[10;30HReboot"
        self.assertEqual([node["name"] for node in console_nodes(screen)], ["Perform MOK management", "Reboot"])

    def test_wrapped_box_drawing_does_not_change_names(self):
        nodes = console_nodes("\x1b[1;1H│  ANATASE-KEY-ENROLLME.der │")
        self.assertEqual(nodes[0]["name"], "ANATASE-KEY-ENROLLME.der")

    def test_arm_ascii_boxes_preserve_directory_names_and_highlight(self):
        screen = "\x1b[1;1H/----------------\\\x1b[2;1H|  \x1b[40m| EFI/ |\x1b[44m  |"
        screen += "\x1b[3;1H|  | ANATASE-KEY-ENROLLME.der |  |\x1b[4;1H\\----------------/"
        nodes = console_nodes(screen)
        self.assertEqual([node["name"] for node in nodes], ["EFI/", "ANATASE-KEY-ENROLLME.der"])
        self.assertTrue(nodes[0]["dark_background"])
        self.assertFalse(nodes[1]["dark_background"])


@unittest.skipUnless(shutil.which("qemu-system-x86_64"), "QEMU is not installed")
class QEMURebootIntegration(unittest.TestCase):
    def test_real_guest_reset_pauses_and_can_be_resumed(self):
        cache = host.ROOT / "cache/iso-test-unit"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            h = host.Harness(argparse.Namespace(arm=False, iso=Path("unused.iso")),
                             {"base": Path(directory), "accel": "tcg"})
            boot = h.directory / "reset.bin"
            # 16-bit boot sector: ask the emulated keyboard controller to reset.
            boot.write_bytes(bytes.fromhex("b0fee664f4ebfd") + bytes(503) + bytes.fromhex("55aa"))
            args = ["qemu-system-x86_64", "-accel", "tcg", "-m", "64", "-display", "none",
                    "-no-reboot", "-no-shutdown", "-drive", f"file={boot},format=raw",
                    "-qmp", f"unix:{h.directory / 'qmp.sock'},server=on,wait=off",
                    "-monitor", "none", "-serial", "none"]
            h.process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                h.wait(lambda: h.qmp.call("query-status")["status"] == "shutdown", 10, "test guest reset")
                h.resume_boot()
                h.wait(lambda: h.qmp.call("query-status")["status"] == "shutdown", 10, "second test guest reset")
                h.qmp.call("quit")
                self.assertEqual(h.process.wait(timeout=5), 0)
            finally:
                h.cleanup()


if __name__ == "__main__":
    unittest.main()
