#!/usr/bin/env python3
"""Headless ISO acceptance test. All writable VM state belongs to one run."""

import argparse
import csv
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import signal
import subprocess
import sys
import time

from protocol import Channel, ProtocolError
from firmware import console_nodes


ROOT = Path(__file__).resolve().parents[2]
HELPER = Path(__file__).with_name("guest.py")
GUEST_HELPER = "/run/anatase-iso-test.py"
TARGET_SERIAL = "ANATASE-ISO-TEST"  # virtio-blk serials are limited to 20 bytes.
DISPLAY_RESOLUTION = (1280, 800)


class BootFailure(Exception):
    """A recognized firmware rejection cannot be fixed by waiting longer."""


class GuestFailure(RuntimeError):
    def __init__(self, action, payload):
        super().__init__(f"Guest {action}: {payload['error']}")
        self.details = payload.get("details")


def image_fixture_visible(path):
    from PIL import Image, ImageChops

    with Image.open(path) as source:
        screen = source.convert("RGB")
    centers = []
    for color in ("#d23456", "#42b883", "#2255aa"):
        difference = ImageChops.difference(screen, Image.new("RGB", screen.size, color))
        channels = difference.split()
        maximum = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
        mask = maximum.point(lambda value: 255 if value <= 12 else 0)
        box = mask.getbbox()
        if not box or mask.histogram()[255] < 500 or min(box[2] - box[0], box[3] - box[1]) < 20:
            return False
        # Sparse matching pixels in desktop icons must not move a square's center.
        pixels = [index for index, value in enumerate(mask.tobytes()) if value]
        centers.append((sum(index % screen.width for index in pixels) / len(pixels),
                        sum(index // screen.width for index in pixels) / len(pixels)))
    return centers[0][0] < centers[1][0] < centers[2][0] and max(y for _, y in centers) - min(y for _, y in centers) < 30


def firmware_menu(image):
    """Find shim's black selection bar; remove its enclosing box for OCR."""
    from PIL import ImageOps, ImageDraw

    width, height = image.size
    mask = ImageOps.grayscale(image).point(lambda pixel: 0 if pixel < 8 else 255).tobytes()
    candidates = []

    def blue(x, y):
        red, green, value = image.getpixel((max(0, min(width - 1, x)), y))
        return value > max(red, green) + 60

    for y in range(20, height - 20):
        for match in re.finditer(b"\x00{20,}", mask[y * width:(y + 1) * width]):
            left, right = match.span()
            if right - left < width * 0.75 and blue(left - 10, y) and blue(right + 10, y):
                candidates.append((left, right, y))
    if not candidates:
        return None
    left, right, row = max(candidates, key=lambda item: item[1] - item[0])
    rows = [y for start, end, y in candidates if abs(start - left) < 4 and abs(end - right) < 4]
    top, bottom = min(rows), max(rows) + 1
    line_height = max(16, bottom - top)
    box = (left + 6, max(0, top - line_height * 8), right - 2, min(height, bottom + line_height * 8))
    menu = ImageOps.grayscale(image.crop(box)).point(lambda pixel: 0 if pixel > 65 else 255)
    draw = ImageDraw.Draw(menu)
    data = menu.tobytes()
    for y in range(menu.height):
        if data[y * menu.width:(y + 1) * menu.width].count(0) > menu.width * 0.7:
            draw.line((0, y, menu.width, y), fill=255)
    return menu, box[:2]


def run(argv, **kwargs):
    result = subprocess.run([str(arg) for arg in argv], capture_output=True, text=True,
                            timeout=kwargs.pop("timeout", 30), **kwargs)
    if result.returncode:
        raise RuntimeError(f"{argv[0]} failed: {result.stderr or result.stdout}")
    return result.stdout


def setting(name, default):
    return os.environ.get(name, str(default))


def firmware(arm):
    code = setting("QEMU_OVMF_CODE", "")
    template = setting("QEMU_OVMF_VARS_TEMPLATE", "")
    if arm:
        if not code and Path("/usr/share/edk2/aarch64/QEMU_EFI.qemuvars.fd").is_file():
            code = "/usr/share/edk2/aarch64/QEMU_EFI.qemuvars.fd"
            template = template or "/usr/share/edk2/aarch64/vars.secboot.json"
        if not code:
            for directory in ("/usr/share/AAVMF", "/usr/share/qemu-efi-aarch64"):
                for suffix in (".ms", ".secboot"):
                    candidate = Path(directory, f"AAVMF_CODE{suffix}.fd")
                    variables = Path(directory, f"AAVMF_VARS{suffix}.fd")
                    if candidate.is_file() and variables.is_file():
                        code, template = str(candidate), template or str(variables)
                        break
                if code:
                    break
    else:
        output = run(["bash", "-c", '''set -euo pipefail
file_size() { stat -L -c '%s' "$1"; }
source "$1/scripts/ovmf.sh"
ovmf_select_firmware 1 "$2" "$3"
printf '%s\\n%s\\n' "$ovmf_code" "$ovmf_template"
''', "iso-test", ROOT, code, template])
        code, template = output.splitlines()
    for label, path in (("Secure Boot firmware", code), ("enrolled variables template", template)):
        if not path or not Path(path).is_file() or not os.access(path, os.R_OK):
            raise RuntimeError(f"Missing {label}: {path!r}; set QEMU_OVMF_CODE and QEMU_OVMF_VARS_TEMPLATE")
    if not template.endswith(".json"):
        try:
            run(["bash", "-c", '''set -euo pipefail
file_size() { stat -L -c '%s' "$1"; }
source "$1/scripts/ovmf.sh"
ovmf_vars_matches_code "$2" "$3" "$4"
''', "iso-test", ROOT, code, template, "1" if arm else "0"])
        except RuntimeError as exc:
            raise RuntimeError("Firmware code and variables template do not match; set both QEMU_OVMF overrides") from exc
    return Path(code).resolve(), Path(template).resolve()


def preflight(args):
    from PIL import Image  # Ubuntu: python3-pil

    if not args.iso.is_file() or not os.access(args.iso, os.R_OK):
        raise RuntimeError(f"ISO is not a readable file: {args.iso}")
    if setting("BIOS", 0) != "0" or setting("VM_SECURE_BOOT", 1) != "1":
        raise RuntimeError("This acceptance test requires UEFI Secure Boot (BIOS=0 VM_SECURE_BOOT=1)")
    # Never accept overrides that could redirect writes to the developer's VM.
    for name in ("VM_DISK", "VM_OVMF_VARS", "VM_RESET_DISK", "SIMULATE_WINDOWS"):
        if name in os.environ:
            raise RuntimeError(f"{name} is not supported: test disks and firmware stores must be fresh")
    binary = setting("QEMU_BIN", "qemu-system-aarch64" if args.arm else "qemu-system-x86_64")
    image_binary = setting("QEMU_IMG", "qemu-img")
    for executable in (binary, image_binary, "tesseract"):
        if not shutil.which(executable):
            raise RuntimeError(f"Required command not found: {executable}; see scripts/iso-test/README.md")
    if "eng" not in run(["tesseract", "--list-langs"]):
        raise RuntimeError("Tesseract English language data is missing")
    code, template = firmware(args.arm)
    native = platform.machine() == ("aarch64" if args.arm else "x86_64")
    kvm = native and os.access("/dev/kvm", os.R_OK | os.W_OK)
    accel = setting("QEMU_ACCEL", "kvm" if kvm else "tcg")
    if accel not in ("kvm", "tcg"):
        raise RuntimeError("QEMU_ACCEL must be kvm or tcg")
    if accel == "kvm" and not kvm:
        raise RuntimeError("KVM is unavailable for this architecture; use QEMU_ACCEL=tcg")
    base = Path(setting("ISO_TEST_OUTPUT", ROOT / "cache/iso-tests")).resolve()
    # Inspect the nearest existing ancestor before creating anything.
    ancestor = base
    while not ancestor.exists():
        ancestor = ancestor.parent
    if shutil.disk_usage(ancestor).free < int(setting("ISO_TEST_MIN_FREE_GIB", 20)) * 1024**3:
        raise RuntimeError("Insufficient free space for the test disk (default minimum: 20 GiB)")
    mounts = json.loads(run(["findmnt", "--json", "-T", ancestor, "-o", "FSTYPE"]))
    if mounts["filesystems"][0]["fstype"] in ("tmpfs", "ramfs"):
        raise RuntimeError("ISO_TEST_OUTPUT must be on disk, not a memory filesystem")
    if base == Path("/tmp") or Path("/tmp") in base.parents:
        raise RuntimeError("ISO_TEST_OUTPUT must not be under /tmp")
    return {"binary": binary, "image_binary": image_binary,
            "firmware": code, "template": template, "accel": accel, "base": base}


class UI:
    def __init__(self, harness):
        self.h = harness
        self.user = None
        self.nodes = []
        self.words = []
        self.size = DISPLAY_RESOLUTION
        self.index = 0

    def capture(self, label="screen", accessibility=True):
        from PIL import Image, ImageOps, ImageStat

        self.index += 1
        prefix = self.h.directory / f"{self.index:05d}-{re.sub('[^a-zA-Z0-9_-]', '-', label)[:70]}"
        screenshot = prefix.with_suffix(".png")
        # QEMU's PPM writer includes pixman row padding at unaligned widths.
        # PNG encodes the actual pixel width, including after GTK resizes.
        self.h.qmp.call("screendump", {"filename": str(screenshot), "format": "png"})
        with Image.open(screenshot) as image:
            self.size = image.size
            self.last_image = screenshot
            original = image.convert("RGB")
            # Upscaling also recovers the low-contrast selected row in shim's menus.
            sample = original.getpixel((image.width // 2, image.height // 3))
            firmware_screen = sample[2] > max(sample[:2]) + 60 and max(sample[:2]) < 40
            enhanced = ImageOps.grayscale(image)
            if firmware_screen:
                enhanced = enhanced.point(lambda pixel: 0 if pixel > 65 else 255)
            enhanced = enhanced.resize((image.width * 2, image.height * 2))
            buffer = io.BytesIO()
            enhanced.save(buffer, format="PNG")
            raw = buffer.getvalue()
        self.words = []
        passes = [(raw, (0, 0), "6" if firmware_screen else "11")]
        menu = firmware_menu(original) if firmware_screen else None
        if menu:
            cropped, offset = menu
            buffer = io.BytesIO()
            cropped.resize((cropped.width * 2, cropped.height * 2)).save(buffer, format="PNG")
            passes.append((buffer.getvalue(), offset, "6"))
        for raw, offset, psm in passes:
            output = subprocess.run(["tesseract", "stdin", "stdout", "-l", "eng", "--psm", psm, "tsv"],
                                    input=raw, capture_output=True, timeout=30)
            if output.returncode:
                raise RuntimeError(f"OCR failed: {output.stderr.decode(errors='replace')}")
            lines = {}
            for item in csv.DictReader(io.StringIO(output.stdout.decode()), delimiter="\t", quoting=csv.QUOTE_NONE):
                if not item.get("text", "").strip() or float(item["conf"]) < 25:
                    continue
                key = tuple(item[name] for name in ("block_num", "par_num", "line_num"))
                lines.setdefault(key, []).append(item)
            for items in lines.values():
                left = min(int(x["left"]) for x in items) // 2 + offset[0]
                top = min(int(x["top"]) for x in items) // 2 + offset[1]
                right = max(int(x["left"]) + int(x["width"]) for x in items) // 2 + offset[0]
                bottom = max(int(x["top"]) + int(x["height"]) for x in items) // 2 + offset[1]
                median = ImageStat.Stat(original.crop((max(0, left - 4), max(0, top - 2),
                                                       min(original.width, max(right + 4, left + 1)),
                                                       min(original.height, max(bottom + 2, top + 1))))).median
                self.words.append({"name": " ".join(x["text"] for x in items),
                                   "rect": [left, top, right - left, bottom - top], "ocr": True,
                                   "dark_background": max(median) < 40})
        self.nodes = []
        accessibility_error = None
        if self.user and accessibility:
            try:
                self.nodes = self.h.guest("a11y", user=self.user,
                                         timeout=15 if self.h.config["accel"] == "kvm" else 90)
            except (RuntimeError, OSError, TimeoutError) as exc:
                accessibility_error = str(exc)
        if firmware_screen:
            serial = self.h.directory / "serial.log"
            if serial.is_file():
                console = console_nodes(serial.read_text(errors="replace"))
                if any(re.search(r"MOK|Select Key|Verification failed|key management|select boot device",
                                 node["name"], re.I) for node in console):
                    self.words = console
        prefix.with_suffix(".json").write_text(json.dumps({"a11y": self.nodes, "ocr": self.words,
                                                          "accessibility_error": accessibility_error}, indent=2))
        return "\n".join([*(str(x.get("name", "")) + " " + x.get("text", "") for x in self.nodes
                             if x.get("visible")), *(x["name"] for x in self.words)])

    def find(self, pattern, roles=None):
        def matches(name):
            name = name.strip(" |[]{}<>_~`'\"")
            return re.search(pattern, name, re.I) or re.search(pattern.replace(" ", ""), re.sub(r"\s+", "", name), re.I)

        disabled = False
        for node in self.nodes:
            if not node.get("visible") or not node.get("rect"):
                continue
            if roles and node.get("role") not in roles:
                continue
            names = [node.get("name", ""), node.get("text", ""), *node.get("labels", [])]
            if node.get("role") in ("text", "entry", "password text") and "path" in node:
                # Qt Quick exposes placeholder labels as children of unnamed inputs.
                names.extend(child.get("name", "") for child in self.nodes
                             if child.get("visible") and child.get("role") == "label"
                             and child.get("path", [])[:-1] == node["path"])
            if any(matches(name) for name in names):
                if node.get("enabled"):
                    return node
                disabled = True
        if disabled:
            return None
        # OCR has no semantic role, so fallback patterns must name visible controls precisely.
        return next((x for x in self.words if matches(x["name"])), None)

    def application_window_visible(self, pattern):
        windows = [node for node in self.nodes if node.get("visible") and node.get("rect")
                   and node.get("role") in ("frame", "dialog", "window")
                   and node.get("app") != "plasmashell"]
        # A taskbar button appears before the application's window is ready.
        return any(re.search(pattern, node.get("name", ""), re.I) for node in windows) or any(
            re.search(pattern, word["name"], re.I) for word in self.words)

    def wait(self, pattern, *, timeout=None, roles=None, label="wait"):
        def locate():
            self.capture(label)
            return self.find(pattern, roles)
        return self.h.wait(locate, timeout or self.h.ui_timeout, f"visible control {pattern}")

    def click_node(self, node):
        if "path" in node and self.user:
            mode = "focus" if node.get("role") in ("text", "entry", "password text") else "activate"
            result = self.h.guest("a11y-action", user=self.user, node=node, mode=mode)
            if mode == "activate" and result == "focused":
                self.key("spc")
            return
        x, y, width, height = node["rect"]
        x, y = x + width / 2, y + height / 2
        if width <= 0 or height <= 0 or not (0 <= x < self.size[0] and 0 <= y < self.size[1]):
            raise RuntimeError(f"Control is outside the visible screen: {node}")
        self.h.qmp.call("input-send-event", {"events": [
            {"type": "abs", "data": {"axis": "x", "value": int(x * 32767 / self.size[0])}},
            {"type": "abs", "data": {"axis": "y", "value": int(y * 32767 / self.size[1])}},
            {"type": "btn", "data": {"down": True, "button": "left"}},
        ]})
        # USB input reports can coalesce a press/release in the same QMP batch.
        time.sleep(0.1)
        self.h.qmp.call("input-send-event", {"events": [
            {"type": "btn", "data": {"down": False, "button": "left"}},
        ]})

    def click(self, pattern, **kwargs):
        self.click_node(self.wait(pattern, **kwargs))

    def key(self, *keys):
        self.h.qmp.call("send-key", {"keys": [{"type": "qcode", "data": key} for key in keys], "hold-time": 50})
        time.sleep(0.1)

    def type(self, text):
        punctuation = {" ": "spc", ".": "dot", "/": "slash", "-": "minus", "=": "equal",
                       "\n": "ret", "_": ("shift", "minus"), ":": ("shift", "semicolon"),
                       "+": ("shift", "equal"), "!": ("shift", "1"),
                       "'": "apostrophe", '"': ("shift", "apostrophe"), ";": "semicolon",
                       "(": ("shift", "9"), ")": ("shift", "0"), ",": "comma",
                       "[": "bracket_left", "]": "bracket_right", "\\": "backslash",
                       "<": ("shift", "comma"), ">": ("shift", "dot"), "|": ("shift", "backslash"),
                       "$": ("shift", "4"), "?": ("shift", "slash"), "&": ("shift", "7")}
        for character in text:
            if character in punctuation:
                keys = punctuation[character]
                self.key(*(keys if isinstance(keys, tuple) else (keys,)))
            elif character.isascii() and character.isalnum():
                self.key(*(("shift", character.lower()) if character.isupper() else (character,)))
            else:
                raise ValueError(f"Unsupported keyboard character {character!r}")

    def fill(self, pattern, text, *, secret=False):
        node = self.wait(pattern, roles=("text", "entry", "password text"))
        if node.get("ocr"):
            # Form labels are normally immediately left of their entry field.
            # Prefer a11y; without a matching entry this must be calibrated, never guessed.
            raise RuntimeError(f"No accessible input for {pattern}; see captured form")
        self.click_node(node)
        self.key("ctrl", "a")
        self.type(text)


class Harness:
    def __init__(self, args, config):
        self.args, self.config = args, config
        self.directory = config["base"] / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3))
        self.directory.mkdir(parents=True, mode=0o700)
        if len(str(self.directory / "agent.sock").encode()) >= 104:
            raise RuntimeError("Run directory is too long for a Unix socket; set a shorter ISO_TEST_OUTPUT")
        self.qmp = Channel(self.directory / "qmp.sock")
        self.agent = Channel(self.directory / "agent.sock", agent=True, timeout=5)
        self.process = None
        self.ui = UI(self)
        self.ui_timeout = int(setting("ISO_TEST_UI_TIMEOUT", 180 if config["accel"] == "kvm" else 600))
        self.boot_timeout = int(setting("ISO_TEST_BOOT_TIMEOUT", 600 if config["accel"] == "kvm" else 2400))
        self.install_timeout = int(setting("ISO_TEST_INSTALL_TIMEOUT", 1800 if config["accel"] == "kvm" else 7200))
        self.app_timeout = int(setting("ISO_TEST_APP_TIMEOUT", 120 if config["accel"] == "kvm" else 600))
        self.scrub_timeout = int(setting("ISO_TEST_SCRUB_TIMEOUT", 900))
        self.deadline = time.monotonic() + int(setting("ISO_TEST_TIMEOUT", 7200 if config["accel"] == "kvm" else 21600))
        self.user = "isotest"
        self.password = "IsoTest-" + secrets.token_hex(8)
        self.expected = []
        self.live_boot = None
        self.installed_boot = None
        self.since = None
        self.records = []
        self.sequence = 0
        self.enrollment_seen = False
        self.helper_ready = False
        self.report = {"status": "running", "iso": str(args.iso.resolve()), "arch": "aarch64" if args.arm else "x86_64",
                       "accel": config["accel"], "directory": str(self.directory), "stages": self.records}
        self.save()

    def log(self, message):
        print(f"==> {message}", flush=True)

    def console_details(self, label, value, *, tail=None):
        text = value if isinstance(value, str) else json.dumps(value, indent=2)
        lines = text.splitlines()
        if tail and len(lines) > tail:
            lines = [f"[showing last {tail} of {len(lines)} lines; full output retained in artifacts]", *lines[-tail:]]
        self.log(label)
        # Prefix guest output so it cannot be interpreted as Actions commands.
        print("\n".join("    " + line for line in lines) or "    (empty)", flush=True)

    def save(self):
        path = self.directory / "results.json"
        temporary = path.with_suffix(".new")
        temporary.write_text(json.dumps(self.report, indent=2))
        temporary.replace(path)

    def wait(self, predicate, timeout, description):
        deadline = min(time.monotonic() + timeout, self.deadline)
        error = None
        while time.monotonic() < deadline:
            if self.process and self.process.poll() is not None:
                raise RuntimeError(f"QEMU exited ({self.process.returncode}) while waiting for {description}")
            try:
                value = predicate()
                if value:
                    return value
            except (OSError, ProtocolError, TimeoutError, RuntimeError) as exc:
                error = str(exc)
            time.sleep(1)
        raise TimeoutError(f"Timed out waiting for {description}" + (f": {error}" if error else ""))

    def stage(self, name, operation, *, fatal=True):
        self.log(name)
        record = {"name": name, "status": "running", "started": datetime.now(timezone.utc).isoformat()}
        self.records.append(record)
        self.save()
        start = time.monotonic()
        try:
            record["result"] = operation()
            record["status"] = "passed"
        except (Exception, KeyboardInterrupt) as exc:
            record.update(status="failed", error=str(exc) or "Interrupted")
            if getattr(exc, "details", None) is not None:
                record["result"] = exc.details
            self.log(f"FAILED: {name}: {exc}")
            structured_checks = isinstance(record.get("result"), dict) and "checks" in record["result"]
            if "result" in record:
                details = record["result"]
                if structured_checks:
                    # The report retains all checks; the console only needs
                    # the errors and unexpected crashes, not healthy services
                    # and successful scrub output.
                    self.console_details("Check failures", details.get("errors", []))
                    crashes = details["checks"].get("coredumps", [])
                    if isinstance(crashes, list):
                        for crash in crashes:
                            if not crash.get("allowed", False):
                                self.log(f"Coredump: {crash.get('exe')} user={crash.get('user')} "
                                         f"pid={crash.get('pid')} signal={crash.get('sig')}")
                else:
                    self.console_details(f"{name}: failed check details", details, tail=30)
            if not isinstance(exc, KeyboardInterrupt):
                try:
                    self.diagnostics(name, console=not structured_checks)
                except Exception as diagnostic_error:
                    self.log(f"Failure diagnostics unavailable: {diagnostic_error}")
            if fatal or isinstance(exc, KeyboardInterrupt):
                raise
        finally:
            record["seconds"] = round(time.monotonic() - start, 2)
            self.save()
        return record

    def guest(self, action, *, timeout=60, **kwargs):
        request = {"action": action, **kwargs}
        result = self.agent.execute(["/usr/bin/python3", GUEST_HELPER, json.dumps(request)], timeout=timeout)
        self.sequence += 1
        (self.directory / f"guest-{self.sequence:05d}-{action}.json").write_text(json.dumps(result, indent=2))
        if result["code"] or result["truncated"]:
            if not result["truncated"]:
                try:
                    payload = json.loads(result["stdout"])
                except (ValueError, TypeError):
                    payload = None
                if isinstance(payload, dict) and "error" in payload:
                    raise GuestFailure(action, payload)
            raise RuntimeError(f"Guest {action}: {result['stdout']} {result['stderr']}")
        return json.loads(result["stdout"])

    def install_helper(self):
        self.agent.call("guest-ping")
        self.agent.put(GUEST_HELPER, HELPER.read_bytes())
        self.helper_ready = True
        return True

    def launch_vm(self):
        config = self.config
        self.report["firmware"] = {"code": str(config["firmware"]), "template": str(config["template"])}
        disk = self.directory / "disk.raw"
        run([config["image_binary"], "create", "-f", "raw", "-o", "preallocation=off", disk,
             setting("VM_DISK_SIZE", "40G")])
        variables = self.directory / ("vars.json" if str(config["template"]).endswith(".json") else "vars.fd")
        shutil.copyfile(config["template"], variables)
        machine = setting("QEMU_MACHINE", "virt" if self.args.arm else "q35")
        if variables.suffix == ".json":
            firmware_args = ["-bios", str(config["firmware"]), "-device",
                             f"{'uefi-vars-sysbus' if self.args.arm else 'uefi-vars-x64'},jsonfile={variables}"]
        else:
            firmware_args = ["-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={config['firmware']}",
                             "-drive", f"if=pflash,format=raw,unit=1,file={variables}"]
            # ARM UEFI Secure Boot uses the enrolled variable store, without
            # TrustZone: Ubuntu's AAVMF firmware cannot enter from EL3.
            if not self.args.arm:
                if "smm=" not in machine:
                    machine += ",smm=on"
                firmware_args += ["-global", "driver=cfi.pflash01,property=secure,value=on"]
        vga = setting("QEMU_VGA", "virtio")
        gl = setting("QEMU_GL", 0) == "1" and vga == "virtio"
        display = setting("QEMU_DISPLAY", "egl-headless" if gl else "none")
        # GTK otherwise enables zoom-to-fit automatically for Virtio, keeping
        # a small host window even when firmware switches to 1280x800.
        if display.split(",")[0] == "gtk" and not any(option.startswith("zoom-to-fit=") for option in display.split(",")[1:]):
            display += ",zoom-to-fit=off"
        if gl:
            device = "virtio-gpu-gl-pci" if self.args.arm else "virtio-vga-gl"
            device += f",blob=on,hostmem={setting('QEMU_GPU_HOSTMEM', '1G')}"
            if setting("QEMU_VENUS", 1) == "1":
                device += ",venus=on"
        else:
            device = "virtio-gpu-pci" if self.args.arm else "virtio-vga"
        width, height = DISPLAY_RESOLUTION
        graphics = (["-device", f"{device},edid=on,xres={width},yres={height}"]
                    if vga == "virtio" else ["-vga", vga])
        # Ubuntu's edk2 2025.11 hangs with the LPA2 exposed by ARM's max CPU.
        cpu = "host" if config["accel"] == "kvm" else ("neoverse-n1" if self.args.arm else "max")
        args = [config["binary"], "-name", "anatase-iso-test", "-machine", machine,
                "-accel", config["accel"], "-cpu", setting("QEMU_CPU", cpu),
                "-m", setting("VM_MEMORY", 8192), "-smp", setting("VM_CPUS", 4), *firmware_args,
                "-drive", f"if=none,id=install0,file={disk},format=raw,cache=writeback,discard=unmap,detect-zeroes=unmap",
                "-device", f"virtio-blk-pci,drive=install0,serial={TARGET_SERIAL},bootindex=2",
                "-drive", f"if=none,id=installer_iso,file={self.args.iso.resolve()},format=raw,media=cdrom,readonly=on",
                "-device", "virtio-scsi-pci,id=installer_scsi", "-device",
                "scsi-cd,bus=installer_scsi.0,drive=installer_iso,bootindex=1,id=installer_cd",
                # Boot from the ISO/disk, without an optional PXE ROM dependency.
                "-netdev", "user,id=net0", "-device", "virtio-net-pci,netdev=net0,romfile=",
                "-device", "qemu-xhci", "-device", "usb-kbd", "-device", "usb-tablet",
                *graphics, "-display", display,
                "-device", "virtio-serial-pci", "-chardev",
                f"socket,id=agent,path={self.directory / 'agent.sock'},server=on,wait=off",
                "-device", "virtserialport,chardev=agent,name=org.qemu.guest_agent.0",
                "-qmp", f"unix:{self.directory / 'qmp.sock'},server=on,wait=off",
                "-serial", f"file:{self.directory / 'serial.log'}", "-monitor", "none",
                "-no-shutdown"]
        (self.directory / "qemu-command.json").write_text(json.dumps(args, indent=2))
        self.qemu_log = (self.directory / "qemu.log").open("wb")
        self.process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=self.qemu_log,
                                        stderr=subprocess.STDOUT, start_new_session=True)
        self.log(f"{self.report['arch']} using {config['accel']}; artifacts: {self.directory}")
        if config.get("accel_reason"):
            self.report["accel_reason"] = config["accel_reason"]
            self.log(config["accel_reason"])
        self.wait(lambda: self.qmp.call("query-status"), 30, "QMP")
        return {"pid": self.process.pid, "disk": str(disk), "variables": str(variables)}

    def diagnostics(self, label, *, console=False):
        try:
            screen = self.ui.capture("failure-" + label)
            if console:
                self.console_details("Visible screen text", screen, tail=30)
        except Exception as exc:
            if console:
                self.log(f"Screen diagnostics unavailable: {exc}")
        if console and not self.helper_ready:
            for name in ("qemu.log", "serial.log"):
                path = self.directory / name
                if path.is_file():
                    # Seek a bounded tail; serial logs can be large.
                    with path.open("rb") as stream:
                        stream.seek(max(0, path.stat().st_size - 32768))
                        output = stream.read().decode(errors="replace")
                        if output.strip():
                            self.console_details(name, output, tail=20)
        if self.helper_ready:
            try:
                logs = self.guest("diagnostics", since=self.since, timeout=60)
                (self.directory / f"diagnostics-{len(self.records):03d}.json").write_text(json.dumps(logs, indent=2))
                if console:
                    errors = "\n".join(line for line in logs.get("journal", "").splitlines()
                                       if re.search(r"\b(error|failed|failure|fatal|crashed|segfault|corrupt|exception)\b", line, re.I))
                    if errors:
                        self.console_details("Guest journal errors", errors, tail=20)
                    for source, output in logs.items():
                        if source.endswith("/launch.log") or ("install" in label.lower() and "anaconda" in source):
                            if str(output).strip():
                                self.console_details(f"Guest {source}", output, tail=30)
            except Exception as exc:
                if console:
                    self.log(f"Guest diagnostics unavailable: {exc}")
        elif console:
            self.log("Guest diagnostics unavailable: helper has not connected")

    def cleanup(self):
        self.agent.close()
        self.qmp.close()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        if hasattr(self, "qemu_log"):
            self.qemu_log.close()

    def firmware_select(self, target, options):
        visible = [(pattern, self.ui.find(pattern)) for pattern in options]
        visible = [(pattern, node) for pattern, node in visible if node]
        visible.sort(key=lambda pair: pair[1]["rect"][1])
        index = next((i for i, (pattern, _) in enumerate(visible) if pattern == target), None)
        if index is None:
            raise RuntimeError(f"Unrecognized firmware menu for {target}")
        # Find the black selection bar on shim's blue menu. Do not assume arrows
        # clamp at the ends: some firmware versions wrap around.
        selected = [i for i, (_, node) in enumerate(visible) if node.get("dark_background")]
        if len(selected) != 1:
            raise RuntimeError(f"Cannot identify selected firmware row: {visible}")
        current = selected[0]
        for _ in range(abs(index - current)):
            self.ui.key("down" if index > current else "up")
        self.ui.key("ret")

    def boot_live(self):
        last_action = None

        def progress():
            nonlocal last_action
            try:
                self.agent.timeout = 1
                self.install_helper()
                return True
            except (OSError, RuntimeError, TimeoutError):
                self.agent.close()
            text = self.ui.capture("enrollment", accessibility=False)
            if not self.enrollment_seen and self.ui.find(r"select boot device"):
                serial = (self.directory / "serial.log").read_text(errors="replace")
                if "Security Violation" in serial:
                    raise BootFailure("UEFI rejected the ISO's Secure Boot chain before MokManager enrollment; inspect serial.log")
            if re.search(r"Verification failed|Security Violation", text, re.I):
                self.ui.key("ret")
                last_action = None
            elif re.search(r"Press any key", text, re.I):
                self.ui.key("ret")
                last_action = None
            elif self.ui.find(r"^Reboot$"):
                self.firmware_select(r"^Reboot$", [r"^Reboot$", r"Enroll key from disk", r"Enroll hash from disk"])
                last_action = None
            elif self.ui.find(r"Enroll key from disk"):
                self.enrollment_seen = True
                target = r"Enroll key from disk"
                self.firmware_select(target, [r"Continue boot", r"Enroll MOK$", target, r"Enroll hash from disk"])
                last_action = None
            elif self.ui.find(r"^ANATASE[_-]KEY$") and re.search(r"Select Key", text, re.I):
                self.enrollment_seen = True
                self.ui.key("ret")
                last_action = None
            elif self.ui.find(r"ANATASE.*(?:ENROLLME|[. ]der)"):
                self.enrollment_seen = True
                # A directory browser also contains ../ and sometimes unrelated files.
                items = sorted(self.ui.words, key=lambda x: x["rect"][1])
                entries = [x for x in items if re.search(r"\.\./|[. ]der|\.efi|\.cfg|^EFI/?$|^BOOT/?$", x["name"], re.I)]
                names = [re.escape(x["name"]) for x in entries]
                chosen = next(re.escape(x["name"]) for x in entries if re.search(r"ANATASE.*(?:ENROLLME|[. ]der)", x["name"], re.I))
                self.firmware_select(chosen, names)
                last_action = None
            elif self.ui.find(r"Enroll.*key|Enroll.*MOK") and self.ui.find(r"^Continue$"):
                self.firmware_select(r"^Continue$", [r"View key", r"^Continue$"])
                last_action = None
            elif self.ui.find(r"Enroll.*key|Enroll.*MOK|Is this.*key") and self.ui.find(r"^Yes$"):
                self.firmware_select(r"^Yes$", [r"^No$", r"^Yes$"])
                last_action = None
            elif re.search(r"Select.*(?:volume|file|key)|Choose.*(?:volume|file)", text, re.I):
                # The only optical filesystem exposed to this VM is the supplied ISO.
                # Firmware names vary; require a recognizable CD/EFI filesystem label.
                target = self.ui.find(r"CDROM|CD\(|ISO9660|ANATASE|^EFI/?$|^BOOT/?$")
                if target and target["name"] != last_action:
                    self.ui.key("down")
                    self.ui.key("ret")
                    last_action = target["name"]
            return False

        self.wait(progress, self.boot_timeout, "live guest agent after MOK enrollment")
        self.agent.timeout = 10
        if not self.enrollment_seen:
            raise RuntimeError("Guest booted without exercising Anatase MOK enrollment; template may already trust the key")
        self.bootstrap_agent()
        self.report["secure_boot"] = self.guest("secure-boot")
        self.live_boot = self.guest("boot")
        self.since = self.live_boot["time"]
        if "rd.live.image" not in self.live_boot["cmdline"]:
            raise RuntimeError("Expected the live ISO environment")
        self.wait_session("anatase")
        self.ui.capture("live-desktop")
        return self.live_boot

    def bootstrap_agent(self):
        """Bootstrap only the diagnostics service through the real live user session.

        Fedora confines QGA enough to forbid runuser, systemd control and keyring
        access. Keep SELinux enforcing, and relax only this disposable VM's agent.
        """
        context = self.agent.execute(["/usr/bin/id", "-Z"])["stdout"]
        if "virt_qemu_ga_t" not in context:
            self.report["agent_context"] = context.strip()
            return
        self.wait_session("anatase", require_desktop=False)
        self.ui.user = None
        def desktop_ready():
            self.ui.capture("live-desktop-before-bootstrap", accessibility=False)
            # Plasma wraps the desktop icon caption at some display sizes.
            return self.ui.find(r"^Anatase Installer$") or (
                self.ui.find(r"^Anatase$") and self.ui.find(r"^Installer$"))

        self.wait(desktop_ready, self.boot_timeout, "rendered live desktop installer icon")
        self.ui.key("ctrl", "alt", "t")
        self.ui.wait(r"Konsole", timeout=30, label="agent-bootstrap-terminal")
        self.ui.type(f"pkexec /usr/bin/python3 {GUEST_HELPER} --bootstrap-agent\n")
        self.agent.close()

        def ready():
            context = self.agent.execute(["/usr/bin/id", "-Z"])["stdout"].strip()
            if "unconfined_service_t" not in context:
                self.ui.capture("agent-bootstrap", accessibility=False)
                return False
            self.report["agent_context"] = context
            return True

        self.wait(ready, self.ui_timeout, "test-only guest agent SELinux context")
        self.report["instrumentation"] = "Only QEMU Guest Agent is unconfined; desktop/Flatpak SELinux remains enforcing"
        self.install_helper()
        self.ui.type("exit\n")

    def wait_session(self, user, *, require_desktop=True):
        def ready():
            candidates = self.guest("sessions")
            matches = [x for x in candidates if x.get("Name") == user and x.get("Active") == "yes"
                       and x.get("Remote") == "no" and x.get("Type") == "wayland"]
            if not matches:
                return False
            if require_desktop:
                self.guest("user-command", user=user, argv=["systemctl", "--user", "is-active",
                                                          "plasma-kwin_wayland.service", "plasma-plasmashell.service"])
            self.ui.user = user
            if require_desktop:
                self.guest("enable-a11y", user=user)
            return matches[0]
        return self.wait(ready, self.boot_timeout, f"active Wayland session for {user}")

    def collect_health(self, live=False):
        return self.guest("health", user="anatase" if live else self.user, live=live, since=self.since,
                          scrub_timeout=self.scrub_timeout, timeout=self.scrub_timeout + 60)

    def installed_boot_check(self):
        self.helper_ready = False
        self.agent.close()
        self.wait(self.install_helper, self.boot_timeout, "installed guest agent")
        cmdline = self.agent.execute(["/usr/bin/cat", "/proc/cmdline"])
        if "rd.live.image" in cmdline["stdout"]:
            raise RuntimeError("The guest rebooted into the live ISO instead of its installed disk")
        boot = self.guest("boot")
        if boot["id"] == self.live_boot["id"] or "rd.live.image" in boot["cmdline"]:
            raise RuntimeError("Guest did not boot the installed disk")
        if "*" not in boot["ostree"] or not boot["boot_mount"]:
            raise RuntimeError("No booted OSTree deployment or installed /boot mount")
        secure_boot = self.guest("secure-boot")
        if self.report.get("secure_boot") and secure_boot["certificate_sha256"] != self.report["secure_boot"]["certificate_sha256"]:
            raise RuntimeError("Installed system's signing certificate differs from the ISO")
        return boot

    def eject_iso(self):
        if self.qmp.call("query-status")["status"] != "shutdown":
            raise RuntimeError("The live guest must complete shutdown before its ISO can be removed")
        self.qmp.call("blockdev-open-tray", {"id": "installer_cd", "force": True})
        # Opening the tray alone leaves the ISO inserted: firmware can close it
        # again on reset and silently boot the live system a second time.
        self.qmp.call("blockdev-remove-medium", {"id": "installer_cd"})
        devices = self.qmp.call("query-block")
        if any(device.get("inserted") for device in devices if device.get("device") == "installer_iso"):
            raise RuntimeError("Installer ISO is still inserted after ejection")
        self.report["iso_ejected"] = True
        (self.directory / "block-devices-after-eject.json").write_text(json.dumps(devices, indent=2))

    def wait_shutdown(self):
        # reboot=shutdown plus -no-shutdown pauses after the guest shuts down.
        # QMP stays connected, allowing safe media removal before firmware runs.
        self.wait(lambda: self.qmp.call("query-status")["status"] == "shutdown",
                  self.ui_timeout, "guest shutdown boundary")

    def resume_boot(self):
        self.agent.close()
        # -no-reboot also applies to host-requested resets. Permit this reset,
        # then restore the guest shutdown boundary before starting the CPUs.
        self.qmp.call("set-action", {"reboot": "reset"})
        self.qmp.call("system_reset")
        self.wait(lambda: self.qmp.call("query-status")["status"] != "shutdown", 30, "QEMU reset")
        self.qmp.call("set-action", {"reboot": "shutdown"})
        self.qmp.call("cont")

    def wait_new_boot(self, old_id):
        def changed():
            # /run and the copied helper disappear on reboot. QGA itself is
            # activated by the virtio port and can read this before reinjection.
            result = self.agent.execute(["/usr/bin/cat", "/proc/sys/kernel/random/boot_id"], timeout=10)
            boot_id = result["stdout"].strip()
            return result["code"] == 0 and bool(boot_id) and boot_id != old_id
        self.wait(changed, self.boot_timeout, "new guest boot ID")

    def installer_language(self):
        english = r"^English\s*\(United States\)$"
        if not self.ui.find(english):
            search = self.ui.find(r"^Search for a language$", roles=("text", "entry", "combo box"))
            if search and not search.get("ocr"):
                self.ui.click_node(search)
            else:
                label = self.ui.find(r"^Language$")
                icons = [node for node in self.ui.words if node.get("ocr") and node["name"] == "Q"
                         and abs(node["rect"][1] - label["rect"][1]) < label["rect"][3] * 2]
                if len(icons) != 1:
                    raise RuntimeError("Cannot identify Anaconda's language search field")
                # The magnifier is inside the search field; click the adjacent
                # editable area, anchored to the detected icon, not screen pixels.
                x, y, width, height = icons[0]["rect"]
                self.ui.click_node({"ocr": True, "rect": [x + 2 * width, y, width, height]})
            self.ui.key("ctrl", "a")
            self.ui.type("English")
        self.ui.click(english)
        self.ui.wait(r"^us$", timeout=self.ui_timeout, label="installer-us-keyboard")
        self.report["installer_language"] = "en_US.UTF-8"
        self.ui.capture("installer-language-selected")

    def install(self):
        # Firmware/MokManager reboots remain normal during enrollment. Pause
        # guest reboots only now, so installation can hand off its boot media.
        self.qmp.call("set-action", {"reboot": "shutdown"})
        disk = self.agent.execute(["/usr/bin/lsblk", "--json", "-o", "NAME,SERIAL,TYPE"])
        if disk["code"]:
            raise RuntimeError(disk["stderr"])
        (self.directory / "installation-disks.json").write_text(disk["stdout"])
        disks = [x for x in json.loads(disk["stdout"])["blockdevices"] if x["type"] == "disk"
                 and not x["name"].startswith(("zram", "ram"))]
        if len(disks) != 1 or disks[0].get("serial") != TARGET_SERIAL:
            raise RuntimeError(f"Unexpected installation disks: {disks}")
        self.guest("launch", user="anatase", argv=["liveinst"])
        deadline = time.monotonic() + self.install_timeout
        previous = None
        submitted = False
        install_started = False
        last_action = time.monotonic()
        selected = set()
        language_selected = False
        while time.monotonic() < min(deadline, self.deadline):
            text = self.ui.capture("installer")
            if re.search(r"Installation failed|Installation of the system failed", text, re.I):
                raise RuntimeError("Anaconda reported installation failure")
            if self.ui.find(r"^Language$") and not language_selected:
                self.installer_language()
                language_selected = True
                last_action = time.monotonic()
                continue
            if re.search(r"Successfully installed|Installation complete", text, re.I):
                self.diagnostics("installation-complete")
                self.report["installed_agent_override"] = self.guest("instrument-installed-agent")
                self.ui.click(r"^Reboot$")
                self.wait_shutdown()
                self.eject_iso()
                self.resume_boot()
                # A disconnect alone is insufficient; require a different boot ID.
                self.wait_new_boot(self.live_boot["id"])
                self.installed_boot = self.installed_boot_check()
                return self.installed_boot
            if submitted:
                if re.search(r"Installing|Storage configuration|Software installation|Finalizing", text, re.I):
                    install_started = True
                if not install_started and time.monotonic() - last_action > self.ui_timeout:
                    raise TimeoutError("Anaconda did not start installation after confirmation")
                time.sleep(2)
                continue
            # Match named controls, never absolute coordinates or a timed sequence of Tabs.
            choices = [r"^(?:[○@oO0]\s*)?Use (?:the )?entire (?:disk|drive)$", r"^I understand.*(?:erased|modified)",
                       r"^Erase.*(?:install|data)", r"^(?:Begin|Start) installation$",
                       r"^Install$", r"^Next$", r"^Continue$"]
            action = next(((pattern, self.ui.find(pattern)) for pattern in choices
                           if pattern not in selected and self.ui.find(pattern)), None)
            if action:
                pattern, node = action
                signature = (pattern, tuple(node["rect"]), text)
                if signature != previous:
                    self.ui.click_node(node)
                    last_action = time.monotonic()
                    previous = signature
                    if "Use " in pattern or pattern.startswith(r"^I understand"):
                        selected.add(pattern)
                    if re.search(r"Begin|Start|Erase|^\^Install", pattern):
                        submitted = True
            if time.monotonic() - last_action > self.ui_timeout:
                raise TimeoutError("Anaconda did not advance; inspect the last installer screen and accessibility dump")
            time.sleep(2)
        raise TimeoutError("Anaconda did not reach a successful installation state")

    def login(self):
        self.ui.user = None
        self.wait(lambda: any(x.get("Class") == "greeter" for x in self.guest("sessions")),
                  self.ui_timeout, "Plasma Login greeter")
        greeters = [x for x in self.guest("sessions") if x.get("Class") == "greeter"]
        self.ui.user = greeters[0]["Name"]
        self.guest("enable-a11y", user=self.ui.user)
        self.ui.capture("greeter")
        username = self.ui.find(r"^Username$", roles=("text", "entry"))
        if username and not username.get("ocr"):
            self.ui.fill(r"^Username$", self.user)
        else:
            name = self.ui.find(r"ISO Test|isotest")
            if name:
                self.ui.click_node(name)
        self.ui.fill(r"^Password$", self.password, secret=True)
        self.ui.key("ret")
        session = self.wait_session(self.user)
        self.ui.capture("logged-in")
        return session

    def setup(self):
        self.wait_session("plasma-setup", require_desktop=False)
        self.guest("enable-a11y", user="plasma-setup")
        self.ui.click(r"^Begin Setup$")
        deadline = min(time.monotonic() + self.ui_timeout, self.deadline)
        account_entered = False
        previous = None
        while time.monotonic() < deadline:
            text = self.ui.capture("plasma-setup")
            if self.ui.find(r"^Full Name$") and not account_entered:
                self.ui.fill(r"^Full Name$", "ISO Test")
                self.ui.fill(r"^Username$", self.user)
                self.ui.fill(r"^Password$", self.password, secret=True)
                self.ui.fill(r"^Confirm Password$", self.password, secret=True)
                account_entered = True
                self.ui.capture("account-filled")
            if self.ui.find(r"^Finish$"):
                if not account_entered:
                    raise RuntimeError("Setup reached Finish without creating the test user")
                self.ui.click(r"^Finish$")
                account = self.wait(lambda: self.guest("account", user=self.user), self.ui_timeout,
                                    "wizard-created administrator account")
                self.login()
                return account
            action = self.ui.find(r"^Skip$") or self.ui.find(r"^Next$")
            if action:
                signature = (text, tuple(action["rect"]))
                if signature != previous:
                    self.ui.click_node(action)
                    previous = signature
            time.sleep(1)
        raise TimeoutError("Plasma Setup did not finish")

    def reboot(self):
        old_id = self.guest("boot")["id"]
        try:
            result = self.agent.execute(["/usr/bin/systemctl", "reboot"], timeout=15)
            if result["code"]:
                raise RuntimeError(f"Guest rejected reboot: {result['stderr']}")
        except (OSError, ProtocolError):
            pass  # A successful reboot can disconnect QGA before its exit reply.
        self.wait_shutdown()
        self.resume_boot()
        self.wait_new_boot(old_id)
        boot = self.installed_boot_check()
        active = self.agent.execute(["/usr/bin/systemctl", "is-active", "plasma-setup.service"])
        if active["code"] == 0:
            raise RuntimeError("Plasma Setup ran again after completion")
        self.login()
        return boot

    def app(self, app_id, user, fixture_root):
        evidence = {"application": app_id}
        checks = {
            "org.anatase.Calculator": ([], r"Calculator|KCalc", "calculator"),
            "org.anatase.TextEditor": ([f"{fixture_root}/fixture.txt"], r"Text Editor|Kate|fixture.txt", "editor"),
            "org.anatase.ImageViewer": ([f"{fixture_root}/fixture.png"], r"Image Viewer|Gwenview|fixture.png", "image"),
            "org.anatase.DocumentViewer": ([f"{fixture_root}/fixture.pdf"], r"Document Viewer|Okular|fixture.pdf", "pdf"),
            "org.anatase.ArchiveManager": ([f"{fixture_root}/fixture.zip"], r"Archive Manager|Ark|fixture.zip", "archive"),
            "org.anatase.DiskUsageAnalyzer": ([fixture_root], r"Disk Usage Analyzer|Filelight|anatase-iso-test", "disk"),
            "org.anatase.Browser": ([f"file://{fixture_root}/page.html", "--force-renderer-accessibility"],
                                    r"Anatase ISO Test", "browser"),
        }
        if app_id not in checks:
            raise RuntimeError(f"Bundled application {app_id} needs a smoke-test interaction; refusing to skip it")
        arguments, window, kind = checks[app_id]
        self.ui.user = user
        self.guest("launch", user=user, argv=["flatpak", "run", app_id, *arguments])

        def ready():
            running = self.guest("user-command", user=user, argv=["flatpak", "ps", "--columns=application"])
            if app_id not in running.splitlines():
                return False
            text = self.ui.capture("app-" + app_id)
            return text if self.ui.application_window_visible(window) else False

        text = self.wait(ready, self.app_timeout, f"running Flatpak with visible window: {app_id}")
        if kind == "calculator":
            self.ui.key("esc")
            self.ui.type("12+30=")
            self.ui.wait(r"^42$", timeout=self.app_timeout, label="calculator-result")
        elif kind == "editor":
            document = self.ui.wait(r"Anatase ISO test fixture", roles=("text",),
                                    timeout=self.app_timeout, label="editor-document-loaded")
            self.ui.click_node(document)
            self.ui.key("ctrl", "end")
            self.ui.type("\nAnatase persistence passed\n")
            self.ui.key("ctrl", "s")
            self.wait(lambda: "Anatase persistence passed" in self.guest("read", path=f"{fixture_root}/fixture.txt"),
                      self.app_timeout, "text editor save")
        elif kind == "image":
            def rendered():
                self.ui.capture("image-rendered", accessibility=False)
                return image_fixture_visible(self.ui.last_image)
            self.wait(rendered, self.app_timeout, "rendered image fixture's three colored squares")
        elif kind == "pdf":
            self.ui.wait(r"Anatase ISO Test", timeout=self.app_timeout, label="fixture-rendered")
        elif kind == "archive":
            self.ui.wait(r"fixture\.txt", timeout=self.app_timeout, label="archive-contents")
        elif kind == "disk":
            def scanned():
                self.ui.capture("directory-scanned")
                expected = ("5 files shown", "fixture.png", "fixture.zip", "fixture.pdf", "page.html", "fixture.txt")
                return all(self.ui.find(r"^" + re.escape(name) + r"$") for name in expected)
            self.wait(scanned, self.app_timeout, "complete directory scan with all five fixture files")
        elif kind == "browser":
            self.ui.click(r"^Test interaction$")
            self.ui.wait(r"^Interaction passed$", timeout=self.app_timeout, label="browser-interaction")
            # Inspect the actual browser's extension page, not just files in the runtime.
            runtimes = self.guest("inventory")["refs"]
            extensions = [ref for ref in runtimes if ref.startswith("runtime/org.anatase.Browser.")]
            if extensions:
                self.ui.key("ctrl", "l")
                self.ui.type("chrome://extensions\n")
                self.ui.wait(r"uBlock Origin|uBlock|Adblock", timeout=self.app_timeout, label="browser-extension")
                toggle = self.ui.wait(r"^On.*extension enabled$", timeout=self.app_timeout,
                                      roles=("toggle button", "check box", "switch"), label="browser-extension-enabled")
                if "checked" in toggle and not toggle["checked"]:
                    raise RuntimeError("Bundled browser extension's enable switch is off")
                evidence["extension_enabled"] = toggle["name"]
                self.ui.capture("browser-extension-state")
                if re.search(r"(?:This extension is|extensions? (?:are|is)) (?:disabled|not supported)|"
                             r"could not be loaded", "\n".join(x.get("name", "") for x in self.ui.words), re.I):
                    raise RuntimeError("Bundled browser extension is disabled or failed to load")
        self.ui.capture("app-passed-" + app_id, accessibility=False)
        return {**evidence, "interaction": kind}

    def flatpak_suite(self, phase, live=False):
        user = "anatase" if live else self.user
        inventory = self.guest("inventory")
        (self.directory / f"flatpaks-{phase}.json").write_text(json.dumps(inventory, indent=2))
        if live:
            self.expected = inventory["snapshot"]
            if not any(ref.startswith("app/") for ref in self.expected):
                raise RuntimeError("ISO has no Flatpak installation snapshot")
        missing = sorted(set(self.expected) - set(inventory["refs"]))
        if missing:
            raise RuntimeError(f"{'Live' if live else 'Installed'} system is missing bundled Flatpak refs: {missing}")
        apps = sorted({ref.split("/")[1] for ref in inventory["refs"] if ref.startswith("app/")})
        if not apps:
            raise RuntimeError("No bundled Flatpak applications found")
        fixtures = self.guest("fixtures", user=user)
        for app_id in apps:
            try:
                self.stage(f"{phase}: {app_id}", lambda app_id=app_id: self.app(app_id, user, fixtures), fatal=False)
            finally:
                try:
                    self.guest("user-command", user=user, argv=["flatpak", "kill", app_id])
                except RuntimeError:
                    pass  # An early-exiting/crashed app was already recorded as failed.
        # Unknown extensions cannot disappear behind a successful application count.
        extensions = [ref for ref in inventory["refs"] if ref.startswith("runtime/org.anatase.")
                      and not ref.startswith("runtime/org.anatase.Platform/")]
        unknown = [ref for ref in extensions if not ref.startswith("runtime/org.anatase.Browser.Adblocker/")]
        if unknown:
            raise RuntimeError(f"Bundled extensions need consumer checks: {unknown}")
        return {"applications": apps, "extensions": extensions, "fixtures": fixtures}

    def persistence(self):
        home = self.guest("account", user=self.user)["home"]
        path = f"{home}/Documents/anatase-iso-test/fixture.txt"
        content = self.guest("read", path=path)
        if "Anatase persistence passed" not in content:
            raise RuntimeError("Text editor's saved file did not survive reboot")
        return {"path": path, "persisted": True}

    def shutdown(self):
        try:
            self.agent.execute(["/usr/bin/systemctl", "poweroff"], timeout=15)
        except (OSError, ProtocolError):
            pass  # The agent can disappear before returning the shutdown result.
        self.wait_shutdown()
        self.qmp.call("quit")
        self.process.wait(timeout=self.ui_timeout)
        if self.process.returncode:
            raise RuntimeError(f"QEMU exited {self.process.returncode} during shutdown")
        return {"clean_shutdown": True}

    def execute(self):
        try:
            self.stage("Launch isolated VM", self.launch_vm)
            self.stage("Secure Boot enrollment and live desktop", self.boot_live)
            self.stage("Live Flatpak suite", lambda: self.flatpak_suite("live", live=True))
            self.stage("Live health", lambda: self.collect_health(live=True), fatal=False)
            self.stage("Graphical installation and installed boot", self.install)
            self.stage("Plasma Setup and password login", self.setup)
            self.stage("Installed Flatpak suite", lambda: self.flatpak_suite("installed"))
            self.stage("Installed health", self.collect_health, fatal=False)
            self.stage("Reboot and password login", self.reboot)
            self.stage("Persistence", self.persistence, fatal=False)
            self.stage("Rebooted Flatpak suite", lambda: self.flatpak_suite("rebooted"))
            self.stage("Rebooted health", self.collect_health, fatal=False)
            self.diagnostics("final")
            self.stage("Clean shutdown", self.shutdown)
            self.report["status"] = "failed" if any(x["status"] != "passed" for x in self.records) else "passed"
        except (Exception, KeyboardInterrupt) as exc:
            self.report.update(status="failed", error=str(exc) or "Interrupted")
        finally:
            self.cleanup()
            self.save()
        self.log(f"{self.report['status'].upper()}: {self.directory / 'results.json'}")
        return 0 if self.report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(
        prog="scripts/test_iso.sh", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Ubuntu host dependencies:
  python3 python3-pil tesseract-ocr tesseract-ocr-eng
  qemu-system-x86 qemu-system-arm qemu-utils ovmf qemu-efi-aarch64

Fedora OCR/Python dependencies (QEMU and firmware must also be installed):
  sudo dnf install python3-pillow tesseract tesseract-langpack-eng

Defaults: headless software graphics at 1280x800, Secure Boot, 8 GiB RAM, 4 CPUs,
40 GiB sparse disk; KVM when usable, TCG otherwise. Each run owns fresh disk
and firmware state under cache/iso-tests/ and retains results.json and logs.
ARM uses neoverse-n1 under TCG to avoid Ubuntu's edk2 LPA2 firmware hang.
The live desktop authorizes test-only QEMU Guest Agent instrumentation via
pkexec; SELinux remains enforcing for the desktop and sandboxed applications.

Overrides: VM_MEMORY, VM_CPUS, VM_DISK_SIZE, QEMU_BIN, QEMU_IMG, QEMU_ACCEL,
QEMU_CPU, QEMU_MACHINE, QEMU_DISPLAY (gtk to watch), QEMU_VGA, QEMU_GL, QEMU_VENUS,
QEMU_GPU_HOSTMEM, QEMU_OVMF_CODE, QEMU_OVMF_VARS_TEMPLATE, ISO_TEST_OUTPUT,
ISO_TEST_MIN_FREE_GIB (20), ISO_TEST_TIMEOUT, ISO_TEST_BOOT_TIMEOUT,
ISO_TEST_UI_TIMEOUT, ISO_TEST_INSTALL_TIMEOUT, ISO_TEST_APP_TIMEOUT,
ISO_TEST_SCRUB_TIMEOUT (all timeouts in seconds).
Existing VM_DISK / VM_OVMF_VARS are rejected. VM disks stay off /tmp and tmpfs.
Unknown bundled apps/extensions require explicit interaction checks and fail.
Run unit checks: python3 -m unittest discover -s scripts/iso-test -v
""")
    parser.add_argument("--arm", action="store_true", help="Test an aarch64 ISO")
    parser.add_argument("iso", type=Path, help="Unmodified Anatase installer ISO")
    args = parser.parse_args()
    try:
        config = preflight(args)
        harness = Harness(args, config)
    except (RuntimeError, OSError, ValueError, ImportError) as exc:
        parser.exit(2, f"Preflight failed: {exc}\n")

    def interrupt(signum, frame):
        raise KeyboardInterrupt(f"Received signal {signum}")

    signal.signal(signal.SIGTERM, interrupt)
    return harness.execute()


if __name__ == "__main__":
    sys.exit(main())

