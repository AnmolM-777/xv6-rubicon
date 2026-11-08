import unittest
import socket
from unittest.mock import patch

from bridge import XV6Bridge


class FakeSocket:

    def __init__(self, responses):
        self.responses = responses
        self.sent = []
        self.closed = False

    def settimeout(self, timeout):
        pass

    def sendall(self, data):
        self.sent.append(data)

    def recv(self, size):
        if not self.responses:
            raise socket.timeout()

        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response

    def close(self):
        self.closed = True


class TestBridge(unittest.TestCase):

    @patch("bridge.socket.create_connection")
    def test_connection(self, mock_connect):
        fake = FakeSocket([b"$ "])
        mock_connect.return_value = fake

        bridge = XV6Bridge(timeout=1)

        self.assertEqual(fake.sent, [b"\n"])
        bridge.close()

    @patch("bridge.socket.create_connection")
    def test_command_execution(self, mock_connect):
        fake = FakeSocket([b"$ ", b"report.txt\n$ "])
        mock_connect.return_value = fake

        bridge = XV6Bridge(timeout=1)
        result = bridge.execute("ls")

        self.assertIn("report.txt", result)
        self.assertEqual(fake.sent, [b"\n", b"ls\n"])
        bridge.close()

    @patch("bridge.socket.create_connection")
    def test_invalid_command(self, mock_connect):
        fake = FakeSocket([b"$ "])
        mock_connect.return_value = fake

        bridge = XV6Bridge(timeout=1)

        with self.assertRaises(ValueError):
            bridge.execute("")

        bridge.close()

    @patch("bridge.socket.create_connection")
    def test_connection_closed(self, mock_connect):
        fake = FakeSocket([b"$ ", b""])
        mock_connect.return_value = fake

        bridge = XV6Bridge(timeout=1)

        with self.assertRaises(ConnectionError):
            bridge.execute("ls")

        bridge.close()

    @patch("bridge.socket.create_connection")
    def test_timeout(self, mock_connect):
        fake = FakeSocket([b"$ "])
        mock_connect.return_value = fake

        bridge = XV6Bridge(timeout=0.1)

        with self.assertRaises(TimeoutError):
            bridge.execute("ls")

        bridge.close()

    @patch("bridge.socket.create_connection")
    def test_socket_cleanup(self, mock_connect):
        fake = FakeSocket([b"$ "])
        mock_connect.return_value = fake

        bridge = XV6Bridge(timeout=1)
        bridge.close()

        self.assertTrue(fake.closed)


if __name__ == "__main__":
    unittest.main()
