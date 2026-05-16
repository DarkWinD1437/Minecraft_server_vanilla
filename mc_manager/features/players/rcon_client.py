from __future__ import annotations

import socket
import struct


class RconClient:
    """Minimal RCON client using stdlib socket (no external dependencies)."""

    _REQ_AUTH = 3
    _REQ_CMD = 2
    _RESP_AUTH = 2
    _RESP_CMD = 0

    def __init__(self, host: str = "localhost", port: int = 25575, password: str = "") -> None:
        self._host = host
        self._port = port
        self._password = password
        self._sock: socket.socket | None = None
        self._req_id = 1

    def connect(self) -> tuple[bool, str]:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(5)
            self._sock.connect((self._host, self._port))
            return self._authenticate()
        except OSError as e:
            self._sock = None
            return False, str(e)

    def _authenticate(self) -> tuple[bool, str]:
        rid = self._next_id()
        self._send_packet(rid, self._REQ_AUTH, self._password)
        resp_id, resp_type, _ = self._recv_packet()
        if resp_id == -1:
            return False, "Contraseña RCON incorrecta"
        if resp_id != rid:
            return False, f"ID de respuesta inesperado: {resp_id}"
        return True, ""

    def send(self, command: str) -> tuple[str, str]:
        if self._sock is None:
            ok, err = self.connect()
            if not ok:
                return "", err
        try:
            rid = self._next_id()
            self._send_packet(rid, self._REQ_CMD, command)
            _, _, payload = self._recv_packet()
            return payload, ""
        except OSError as e:
            self._sock = None
            return "", str(e)

    def _send_packet(self, req_id: int, req_type: int, payload: str) -> None:
        payload_bytes = payload.encode("utf-8") + b"\x00\x00"
        length = 4 + 4 + len(payload_bytes)
        packet = struct.pack("<iii", length, req_id, req_type) + payload_bytes
        self._sock.sendall(packet)

    def _recv_packet(self) -> tuple[int, int, str]:
        def recv_exact(n: int) -> bytes:
            data = b""
            while len(data) < n:
                chunk = self._sock.recv(n - len(data))
                if not chunk:
                    raise OSError("Conexión cerrada por el servidor")
                data += chunk
            return data

        header = recv_exact(12)
        length, req_id, resp_type = struct.unpack("<iii", header)
        body = recv_exact(length - 8)
        payload = body[:-2].decode("utf-8", errors="replace")
        return req_id, resp_type, payload

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def __enter__(self) -> "RconClient":
        self.connect()
        return self

    def __exit__(self, *args) -> None:
        self.disconnect()
