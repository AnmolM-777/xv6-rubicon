import socket
import time


class XV6Bridge:

    def __init__(self, host="127.0.0.1", port=5555, timeout=5):
        self.timeout = timeout
        self.sock = socket.create_connection(
            (host, port),
            timeout=timeout
        )
        self.sock.settimeout(0.2)

        try:
            # Send Enter to get the xv6 shell prompt
            self.sock.sendall(b"\n")
            self._read_until_prompt()
        except Exception:
            self.close()
            raise

    def _read_until_prompt(self):
        output = b""
        start = time.monotonic()

        while time.monotonic() - start < self.timeout:
            try:
                data = self.sock.recv(4096)

                if not data:
                    raise ConnectionError("xv6 connection closed")

                output += data

                if output.endswith(b"$ "):
                    return output.decode(errors="replace")

            except socket.timeout:
                continue

        raise TimeoutError("xv6 command timed out")

    def execute(self, command):
        if not isinstance(command, str) or not command.strip():
            raise ValueError("Invalid command")

        self.sock.sendall((command + "\n").encode())
        return self._read_until_prompt()

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None
