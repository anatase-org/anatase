#!/usr/bin/env python3
"""One-shot JSON helper copied to /run in the test guest, never into the ISO."""

import json
import hashlib
import os
from pathlib import Path
import pwd
import re
import secrets
import signal
import subprocess
import sys
import zipfile


CRASH_EXCEPTIONS = {
    ("/usr/libexec/xdg-desktop-portal-kde", "plasmalogin", signal.SIGABRT):
        "Known KDE portal abort in the Plasma Login greeter",
    ("/usr/libexec/xdg-desktop-portal-kde", "plasma-setup", signal.SIGABRT):
        "Known KDE portal abort in Plasma Setup",
}


class CheckFailure(RuntimeError):
    def __init__(self, errors, details):
        super().__init__("; ".join(errors))
        self.details = details


def command(argv, *, check=True, timeout=60, env=None):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env)
    if check and result.returncode:
        raise RuntimeError(f"{argv[0]} exited {result.returncode}: {result.stderr or result.stdout}")
    return result.stdout


def sessions():
    result = []
    for line in command(["loginctl", "list-sessions", "--no-legend", "--no-pager"]).splitlines():
        session_id = line.split()[0]
        data = command(["loginctl", "show-session", session_id,
                        "-p", "Name", "-p", "User", "-p", "Type", "-p", "Class",
                        "-p", "Active", "-p", "Remote", "-p", "State"])
        result.append(dict(item.split("=", 1) for item in data.splitlines() if "=" in item)
                      | {"Id": session_id})
    return result


def session_environment(user):
    account = pwd.getpwnam(user)
    env = {"PATH": os.defpath, "HOME": account.pw_dir, "USER": user, "LOGNAME": user,
           "XDG_RUNTIME_DIR": f"/run/user/{account.pw_uid}",
           "DBUS_SESSION_BUS_ADDRESS": f"unix:path=/run/user/{account.pw_uid}/bus"}
    # Get the real compositor's environment, including the display and a11y bus.
    processes = command(["ps", "-u", str(account.pw_uid), "-o", "pid=,comm="], check=False)
    for line in processes.splitlines():
        pid, name = line.split(None, 1)
        if name.strip() not in ("kwin_wayland", "plasmashell", "plasma-setup") and not name.strip().startswith("plasma-login-"):
            continue
        try:
            variables = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
            for variable in variables:
                key, sep, value = variable.partition(b"=")
                key = key.decode(errors="replace")
                if sep and key in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY", "AT_SPI_BUS_ADDRESS",
                                   "DBUS_SESSION_BUS_ADDRESS", "XDG_CURRENT_DESKTOP", "XDG_SESSION_TYPE"):
                    env[key] = value.decode()
        except (OSError, ValueError):
            continue
    env.update({"LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8", "QT_ACCESSIBILITY": "1",
                "QT_LINUX_ACCESSIBILITY_ALWAYS_ON": "1"})
    return env


def as_user(user, argv, *, wait=True):
    env = session_environment(user)
    args = ["runuser", "-u", user, "--", "env", *[f"{k}={v}" for k, v in env.items()], *argv]
    if wait:
        return command(args)
    # Do not inherit qemu-ga capture pipes: a long-lived child would hold them open.
    log = Path(pwd.getpwnam(user).pw_dir) / ".local/state/anatase-iso-test"
    log.mkdir(parents=True, exist_ok=True)
    os.chown(log, pwd.getpwnam(user).pw_uid, pwd.getpwnam(user).pw_gid)
    unit = "anatase-iso-test-" + secrets.token_hex(5)
    # Launch through the existing user's manager so applications inherit the
    # desktop user's SELinux context, not the diagnostics service's context.
    launch = ["systemd-run", "--user", "--collect", "--no-block", f"--unit={unit}",
              f"--property=StandardOutput=append:{log / 'launch.log'}",
              f"--property=StandardError=append:{log / 'launch.log'}",
              *[f"--setenv={key}={value}" for key, value in env.items()], "--", *argv]
    command([*args[:len(args) - len(argv)], *launch])
    return {"unit": unit, "log": str(log / "launch.log")}


def accessibility():
    import pyatspi

    desktop = pyatspi.Registry.getDesktop(0)
    nodes = []

    def walk(node, path, application, depth=0):
        if depth > 25 or len(nodes) >= 3000:
            return
        try:
            role = node.getRoleName()
            name = node.name or ""
            if role == "application":
                application = name
            state = node.getState()
            visible = state.contains(pyatspi.STATE_SHOWING)
            # Hidden menus and off-screen lists can contain thousands of nodes.
            # Selectors only target showing controls; keep the desktop/app roots.
            if not visible and role not in ("desktop frame", "application"):
                return
            text = ""
            if role in ("text", "entry", "label", "paragraph", "heading", "document text", "document web"):
                try:
                    text = node.queryText().getText(0, -1)[:4096]
                except NotImplementedError:
                    pass
            labels = []
            if role in ("text", "entry", "password text", "combo box"):
                for relation in node.getRelationSet():
                    if relation.getRelationType() == pyatspi.RELATION_LABELLED_BY:
                        labels.extend(relation.getTarget(i).name for i in range(relation.getNTargets()))
            rect = None
            if visible:
                try:
                    ext = node.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
                    rect = [ext.x, ext.y, ext.width, ext.height]
                except NotImplementedError:
                    pass
            nodes.append({"path": path, "app": application, "role": role, "name": name,
                          "labels": labels, "text": text, "rect": rect, "visible": visible,
                          "enabled": state.contains(pyatspi.STATE_ENABLED),
                          "checked": state.contains(pyatspi.STATE_CHECKED),
                          "selected": state.contains(pyatspi.STATE_SELECTED),
                          "focused": state.contains(pyatspi.STATE_FOCUSED)})
            for index in range(node.childCount):
                child = node.getChildAtIndex(index)
                if child:
                    walk(child, path + [index], application, depth + 1)
        except Exception as exc:
            # Stale accessible objects are normal while applications close.
            nodes.append({"path": path, "error": str(exc)[:200]})

    walk(desktop, [], "")
    return nodes


def accessible_action(request):
    import pyatspi

    node = pyatspi.Registry.getDesktop(0)
    for index in request["node"]["path"]:
        node = node.getChildAtIndex(index)
    expected = request["node"]
    if node.name != expected["name"] or node.getRoleName() != expected["role"]:
        raise RuntimeError("Accessible control changed before the action; refresh the screen")
    if request["mode"] == "activate":
        try:
            actions = node.queryAction()
            for index in range(actions.nActions):
                if actions.getName(index).lower() in ("click", "press", "activate", "toggle"):
                    if actions.doAction(index):
                        return "activated"
        except NotImplementedError:
            pass
    if node.getState().contains(pyatspi.STATE_FOCUSED) or node.queryComponent().grabFocus():
        return "focused"
    raise RuntimeError(f"Accessible control cannot perform {request['mode']}")


def flatpaks(root="/var/lib/flatpak"):
    refs = []
    for kind in ("app", "runtime"):
        for active in Path(root, kind).glob("*/*/*/active"):
            refs.append(str(active.relative_to(root).parent))
    return sorted(set(refs))


def fixtures(user):
    account = pwd.getpwnam(user)
    root = Path(account.pw_dir, "Documents/anatase-iso-test")
    root.mkdir(parents=True, exist_ok=True)
    (root / "fixture.txt").write_text("Anatase ISO test fixture\n")
    (root / "page.html").write_text('<!doctype html><title>Anatase ISO Test</title>'
                                  '<h1>Anatase ISO Test</h1><button onclick="this.textContent=\'Interaction passed\'">'
                                  'Test interaction</button>')
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (640, 400), "white")
    draw = ImageDraw.Draw(image)
    draw.text((30, 30), "Anatase ISO Test", fill="black", font_size=32)
    for left, color in ((30, "#d23456"), (230, "#42b883"), (430, "#2255aa")):
        draw.rectangle((left, 110, left + 160, 270), fill=color)
    image.save(root / "fixture.png")
    # A minimal PDF with searchable text, no external fixture generator required.
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 300] /Resources "
               b"<< /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    content = b"BT /F1 20 Tf 30 200 Td (Anatase ISO Test) Tj ET"
    objects.append(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream")
    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(pdf)
    pdf += b"xref\n0 6\n0000000000 65535 f \n"
    pdf += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    pdf += f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    (root / "fixture.pdf").write_bytes(pdf)
    with zipfile.ZipFile(root / "fixture.zip", "w") as archive:
        archive.write(root / "fixture.txt", "fixture.txt")
    for path in [root, *root.rglob("*")]:
        os.chown(path, account.pw_uid, account.pw_gid)
    return str(root)


def btrfs_health(live=False, timeout=900):
    mounts = json.loads(command(["findmnt", "--json", "-t", "btrfs", "-o", "TARGET,UUID"],
                               check=False) or '{"filesystems": []}')
    seen = set()
    checks = []
    errors = []

    def visit(items):
        for item in items:
            uuid = item.get("uuid")
            if not uuid:
                errors.append(f"Btrfs filesystem without UUID: {item}")
                continue
            if uuid not in seen:
                seen.add(uuid)
                mount = item["target"]
                check = {"uuid": uuid, "mount": mount}
                checks.append(check)
                for name, argv in (("scrub", ["btrfs", "scrub", "start", "-B", "-r", mount]),
                                   ("stats", ["btrfs", "device", "stats", "-c", mount])):
                    try:
                        check[name] = command(argv, timeout=timeout)
                    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
                        check[name] = {"error": str(exc)}
                        errors.append(f"{mount} {name}: {exc}")
            visit(item.get("children", []))

    visit(mounts.get("filesystems", []))
    if not live and not checks:
        errors.append("Installed system has no mounted Btrfs filesystem")
    kernel = command(["journalctl", "-k", "-b", "--no-pager", "-o", "cat"])
    errors.extend(line for line in kernel.splitlines() if re.search(
        r"BTRFS.*(?:error|critical|corrupt|csum failed|checksum.*(?:fail|mismatch))|"
        r"(?:I/O error|Buffer I/O error|blk_update_request.*error)", line, re.I))
    if errors:
        raise CheckFailure(errors, {"filesystems": checks, "errors": errors})
    return {"filesystems": checks, "live_has_no_btrfs": live and not checks}


def coredumps(since):
    result = subprocess.run(["coredumpctl", "--json=short", "--no-pager", "--since", since],
                            capture_output=True, text=True, timeout=60,
                            env={**os.environ, "LC_ALL": "C"})
    # coredumpctl exits 1 when there are no matching entries, as well as on errors.
    if result.returncode and not (result.returncode == 1 and re.fullmatch(r"No coredumps found\.?\s*", result.stderr)):
        raise RuntimeError(f"coredumpctl exited {result.returncode}: {result.stderr}")
    crashes = json.loads(result.stdout or "[]")
    for crash in crashes:
        try:
            crash["user"] = pwd.getpwuid(int(crash["uid"])).pw_name
        except (KeyError, TypeError, ValueError):
            crash["user"] = None
        reason = CRASH_EXCEPTIONS.get((crash.get("exe"), crash["user"], crash.get("sig")))
        crash["allowed"] = reason is not None
        if crash["allowed"]:
            crash["allow_reason"] = reason
    return crashes


def health(request):
    checks, errors = {}, []

    def collect(name, operation):
        try:
            checks[name] = operation()
        except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
            checks[name] = {"error": str(exc)}
            if hasattr(exc, "details"):
                checks[name]["details"] = exc.details
            errors.append(f"{name}: {exc}")

    for service in ("plasmalogin.service", "anatase-flatpaks.service", "anatase-flatpak-extensions.service"):
        collect(service, lambda service=service: command(["systemctl", "is-active", service]))
    for service in ("plasma-kwin_wayland.service", "plasma-plasmashell.service"):
        collect(service, lambda service=service: as_user(request["user"], ["systemctl", "--user", "is-active", service]))
    collect("coredumps", lambda: coredumps(request["since"]))
    if isinstance(checks["coredumps"], list) and checks["coredumps"]:
        if any(not crash.get("allowed", False) for crash in checks["coredumps"]):
            errors.append("Guest coredumps detected")
        collect("coredump_info", lambda: command(
            ["coredumpctl", "--no-pager", "--since", request["since"], "info"]))
    collect("btrfs", lambda: btrfs_health(request.get("live", False), request.get("scrub_timeout", 900)))
    if errors:
        raise CheckFailure(errors, {"checks": checks, "errors": errors})
    return checks


AGENT_OVERRIDE = """# Test instrumentation, only on this run's disposable VM.
[Service]
SELinuxContext=system_u:system_r:unconfined_service_t:s0
ExecStart=
ExecStart=/usr/bin/bash -c 'exec /usr/bin/qemu-ga --method=virtio-serial --path=/dev/virtio-ports/org.qemu.guest_agent.0'
"""


def instrument_agent(root, runtime=False):
    directory = Path(root) / ("run" if runtime else "etc") / "systemd/system/qemu-guest-agent.service.d"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "90-anatase-iso-test.conf"
    path.write_text(AGENT_OVERRIDE)
    if not runtime:
        command(["chcon", "-t", "systemd_unit_file_t", str(directory), str(path)])
    return str(path)


def dispatch(request):
    action = request["action"]
    if action == "sessions":
        return sessions()
    if action == "a11y":
        return json.loads(as_user(request["user"], ["python3", __file__, '{"action":"a11y-self"}']))
    if action == "a11y-self":
        return accessibility()
    if action == "a11y-action":
        payload = {**request, "action": "a11y-action-self"}
        return json.loads(as_user(request["user"], ["python3", __file__, json.dumps(payload)]))
    if action == "a11y-action-self":
        return accessible_action(request)
    if action == "enable-a11y":
        enabled = json.loads(as_user(request["user"], ["python3", __file__, '{"action":"enable-a11y-self"}']))
        # liveinst reconstructs its root frontend's environment from the user's
        # manager, so per-launch variables alone do not reach QtWebEngine.
        as_user(request["user"], ["systemctl", "--user", "set-environment", "QT_ACCESSIBILITY=1",
                                 "QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1",
                                 "QTWEBENGINE_CHROMIUM_FLAGS=--force-renderer-accessibility",
                                 "LANG=en_US.UTF-8", "LC_ALL=en_US.UTF-8", "LANGUAGE=en_US"])
        return enabled
    if action == "enable-a11y-self":
        import dbus
        status = dbus.SessionBus().get_object("org.a11y.Bus", "/org/a11y/bus")
        properties = dbus.Interface(status, "org.freedesktop.DBus.Properties")
        properties.Set("org.a11y.Status", "IsEnabled", dbus.Boolean(True))
        return True
    if action == "inventory":
        return {"refs": flatpaks(), "snapshot": flatpaks("/var/lib/flatpak-installer")}
    if action == "fixtures":
        return fixtures(request["user"])
    if action == "launch":
        return as_user(request["user"], request["argv"], wait=False)
    if action == "user-command":
        return as_user(request["user"], request["argv"])
    if action == "health":
        return health(request)
    if action == "secure-boot":
        certificate = Path("/usr/lib/ludos/efi/ANATASE-KEY-ENROLLME.der").read_bytes()
        enrolled = Path("/sys/firmware/efi/efivars/MokListRT-605dab50-e046-4300-abb6-3dd810dd8b23").read_bytes()
        if certificate not in enrolled[4:]:
            raise RuntimeError("The ISO's exact Anatase certificate is absent from MokListRT")
        state = command(["mokutil", "--sb-state"])
        if "SecureBoot enabled" not in state or re.search(r"validation.*disabled", state, re.I):
            raise RuntimeError(f"Secure Boot is not enforced: {state}")
        return {"state": state, "certificate_sha256": hashlib.sha256(certificate).hexdigest()}
    if action == "instrument-installed-agent":
        repo = Path("/mnt/sysimage/ostree/repo")
        checksum = command(["ostree", f"--repo={repo}", "rev-parse", "ostree/0/1/0"]).strip()
        if not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise RuntimeError("Anaconda did not provide a valid installed deployment checksum")
        # /mnt/sysroot is mounted privately by Anaconda's payload service. Use
        # the physical deployment, as installer/anatase.ks does for Flatpaks.
        root = repo.parent / "deploy/anatase/deploy" / f"{checksum}.0"
        if not (root / "etc/fstab").is_file():
            raise RuntimeError(f"Anaconda target deployment is unavailable: {root}")
        return instrument_agent(root)
    if action == "boot":
        return {"id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                "cmdline": Path("/proc/cmdline").read_text(),
                "root": command(["findmnt", "--json", "/"]),
                "boot_mount": command(["findmnt", "--json", "/boot"], check=False),
                "ostree": command(["ostree", "admin", "status"], check=False),
                "time": command(["date", "--iso-8601=seconds"]).strip()}
    if action == "account":
        account = pwd.getpwnam(request["user"])
        groups = command(["id", "-nG", request["user"]]).split()
        if "wheel" not in groups or not Path("/etc/plasma-setup-done").is_file():
            raise RuntimeError("Setup did not finish with an administrator account")
        return {"uid": account.pw_uid, "home": account.pw_dir, "groups": groups}
    if action == "read":
        return Path(request["path"]).read_text()
    if action == "diagnostics":
        logs = {}
        # One unavailable diagnostic must not hide the other evidence.
        for name, argv in {
            "journal": ["journalctl", "-b", "--no-pager", "-n", "4000"],
            "kernel": ["journalctl", "-k", "-b", "--no-pager"],
            "failed": ["systemctl", "--failed", "--no-pager"],
            "coredumps": ["coredumpctl", "--no-pager", "--since", request.get("since") or "today", "info"],
        }.items():
            try:
                result = subprocess.run(argv, capture_output=True, text=True, timeout=5)
                logs[name] = result.stdout + result.stderr
                if result.returncode:
                    logs[name] += f"\nDiagnostic command exited {result.returncode}"
            except (OSError, subprocess.TimeoutExpired) as exc:
                logs[name] = f"Diagnostic unavailable: {exc}"
        try:
            logs["sessions"] = sessions()
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            logs["sessions"] = {"error": str(exc)}
        for path in [*Path("/tmp").glob("*anaconda*.log"), *Path("/var/log/anaconda").glob("*.log"),
                     *Path("/home").glob("*/.local/state/anatase-iso-test/launch.log"),
                     *Path("/var/home").glob("*/.local/state/anatase-iso-test/launch.log")]:
            try:
                logs[str(path)] = path.read_text(errors="replace")[-300000:]
            except OSError:
                pass
        return logs
    raise ValueError(f"Unknown guest action: {action}")


if __name__ == "__main__":
    try:
        if sys.argv[1] == "--bootstrap-agent":
            if os.getuid() != 0:
                raise RuntimeError("Agent instrumentation requires root via pkexec")
            instrument_agent("/", runtime=True)
            command(["systemctl", "daemon-reload"])
            command(["systemctl", "reset-failed", "qemu-guest-agent.service"])
            command(["systemctl", "restart", "qemu-guest-agent.service"])
            print("Test agent ready; desktop SELinux enforcement remains unchanged")
        else:
            print(json.dumps(dispatch(json.loads(sys.argv[1]))))
    except Exception as error:
        print(json.dumps({"error": str(error), **({"details": error.details} if hasattr(error, "details") else {})}))
        sys.exit(1)
