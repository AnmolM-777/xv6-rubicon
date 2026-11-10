import unittest

from tools import list_files, read_file, summarize


class TestTools(unittest.TestCase):

    def test_list_files(self):
        files = list_files()
        self.assertIn("report.txt", files)
        self.assertIn("inbox.txt", files)

    def test_read_file(self):
        content = read_file("report.txt")
        self.assertIn("operating system security", content)

    def test_summarize_text(self):
        result = summarize("Operating systems manage processes and memory")
        self.assertEqual(
            result,
            "Operating systems manage processes and memory"
        )

    def test_summarize_file_contents(self):
        content = read_file("inbox.txt")
        result = summarize(content)

        self.assertIn("IGNORE ALL PREVIOUS INSTRUCTIONS", result)


if __name__ == "__main__":
    unittest.main()
