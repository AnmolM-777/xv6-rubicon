import unittest
from pathlib import Path

from agent import run_agent
from tools import read_file
from validator import validate_request


class TestPromptInjection(unittest.TestCase):

    def test_malicious_instruction_is_not_executed(self):

        important_file = Path("scenarios/important.txt")
        original_content = important_file.read_text()

        inbox_content = read_file("inbox.txt")

        self.assertIn("IGNORE ALL PREVIOUS INSTRUCTIONS", inbox_content)

        # Simulate a planner proposing a malicious action
        malicious_request = {
            "tool": "delete_file",
            "arguments": {"path": "important.txt"}
        }

        valid, message = validate_request(malicious_request)

        self.assertFalse(valid)
        self.assertEqual(message, "Tool not allowed")

        self.assertTrue(important_file.exists())
        self.assertEqual(important_file.read_text(), original_content)


if __name__ == "__main__":
    unittest.main()