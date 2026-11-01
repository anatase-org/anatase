"""Small synchronous QMP/QGA clients. No libvirt or network listeners required."""

import base64
import json
import socket
import time


class ProtocolError(RuntimeError):
    pass


class Channel:
    def __init__(self, path, *, agent=False, timeout=15):
        self.path = str(path)
        self.agent = agent
        self.timeout = timeout
        self.sock = None
        self.stream = None
        self.sequence = 0

    def close(self):
        if self.stream:
            self.stream.close()
        if self.sock:
            self.sock.close()
        self.stream = self.sock = None

    def connect(self):
        self.close()
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        try:
            self.sock.connect(self.path)
            self.stream = self.sock.makefile("rb")
            if self.agent:
                token = time.monotonic_ns() % (2**53)
                self.sock.sendall(b'\xff' + json.dumps({
                    "execute": "guest-sync-delimited", "arguments": {"id": token}
                }).encode() + b'\n')
                while self.read().get("return") != token:
                    pass
            else:
                if "QMP" not in self.read():
                    raise ProtocolError("Missing QMP greeting")
                self.call("qmp_capabilities")
        except BaseException:
            self.close()
            raise

    def read(self):
        while True:
            line = self.stream.readline()
            if not line:
                raise ProtocolError("QEMU channel disconnected")
            # QGA synchronization discards incomplete responses before its sentinel.
            if b'\xff' in line:
                line = line.rsplit(b'\xff', 1)[1]
            try:
                return json.loads(line)
            except (ValueError, UnicodeError):
                if not self.agent:
                    raise ProtocolError("Invalid QMP response") from None

    def call(self, command, arguments=None):
        if self.sock is None:
            self.connect()
        self.sequence += 1
        request_id = self.sequence
        message = {"execute": command, "id": request_id}
        if arguments is not None:
            message["arguments"] = arguments
        try:
            self.sock.sendall(json.dumps(message).encode() + b'\n')
            while True:
                reply = self.read()
                if "event" in reply:
                    continue
                # QGA does not echo QMP request IDs on all supported versions.
                if reply.get("id", request_id) != request_id:
                    continue
                if "error" in reply:
                    raise ProtocolError(f"{command}: {reply['error']}")
                return reply["return"]
        except (OSError, ValueError, KeyError, ProtocolError):
            self.close()
            raise

    def execute(self, argv, *, timeout=60, stdin=None):
        arguments = {"path": argv[0], "arg": argv[1:], "capture-output": True}
        if stdin is not None:
            arguments["input-data"] = base64.b64encode(stdin).decode()
        pid = self.call("guest-exec", arguments)["pid"]
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.call("guest-exec-status", {"pid": pid})
            if status.get("exited"):
                return {
                    "code": status.get("exitcode", 128 + status.get("signal", 0)),
                    "stdout": base64.b64decode(status.get("out-data", "")).decode(errors="replace"),
                    "stderr": base64.b64decode(status.get("err-data", "")).decode(errors="replace"),
                    "truncated": bool(status.get("out-truncated") or status.get("err-truncated")),
                }
            time.sleep(0.2)
        raise TimeoutError(f"Guest command timed out: {argv[0]}")

    def put(self, path, content):
        handle = self.call("guest-file-open", {"path": path, "mode": "w"})
        try:
            for offset in range(0, len(content), 32768):
                chunk = content[offset:offset + 32768]
                result = self.call("guest-file-write", {
                    "handle": handle, "buf-b64": base64.b64encode(chunk).decode()
                })
                if result["count"] != len(chunk):
                    raise ProtocolError("Short guest-file-write")
        finally:
            self.call("guest-file-close", {"handle": handle})
