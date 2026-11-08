import unittest
from planner import plan_request


class TestPlanner(unittest.TestCase):

    def test_list_request(self):
        result = plan_request("list")
        self.assertEqual(result["tool"], "list_files")
        self.assertEqual(result["arguments"], {})

    def test_read_request(self):
        result = plan_request("read report.txt")
        self.assertEqual(result["tool"], "read_file")
        self.assertEqual(result["arguments"]["path"], "report.txt")

    def test_summarize_request(self):
        result = plan_request("summarize Operating systems manage memory")
        self.assertEqual(result["tool"], "summarize")
        self.assertEqual(
            result["arguments"]["text"],
            "Operating systems manage memory"
        )

    def test_unsupported_request(self):
        self.assertIsNone(plan_request("delete important.txt"))

    def test_empty_request(self):
        self.assertIsNone(plan_request(""))


if __name__ == "__main__":
    unittest.main()
