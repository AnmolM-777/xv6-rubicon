import unittest
from pathlib import Path

from validator import validate_request
from tools import get_safe_path


class TestValidator(unittest.TestCase):

    def test_valid_request(self):
        request = {
            "tool": "read_file",
            "arguments": {"path": "report.txt"}
        }

        valid, message = validate_request(request)
        self.assertTrue(valid)

    def test_unknown_tool(self):
        request = {
            "tool": "delete_file",
            "arguments": {"path": "important.txt"}
        }

        valid, message = validate_request(request)
        self.assertFalse(valid)

    def test_invalid_type(self):
        request = {
            "tool": "read_file",
            "arguments": {"path": 123}
        }

        valid, message = validate_request(request)
        self.assertFalse(valid)

    def test_missing_argument(self):
        request = {
            "tool": "read_file",
            "arguments": {}
        }

        valid, message = validate_request(request)
        self.assertFalse(valid)

    def test_extra_argument(self):
        request = {
            "tool": "read_file",
            "arguments": {
                "path": "report.txt",
                "command": "delete"
            }
        }

        valid, message = validate_request(request)
        self.assertFalse(valid)

    def test_path_traversal(self):
        request = {
            "tool": "read_file",
            "arguments": {"path": "../../secret.txt"}
        }

        valid, message = validate_request(request)
        self.assertFalse(valid)

    def test_symbolic_link_escape(self):

        base = Path("scenarios").resolve()
        link = base / "outside_link"

        try:
            link.symlink_to(Path("/etc/passwd"))

            with self.assertRaises(ValueError):
                get_safe_path("outside_link")

        finally:
            if link.is_symlink():
                link.unlink()


if __name__ == "__main__":
    unittest.main()
