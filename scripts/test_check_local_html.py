import tempfile
import unittest
from pathlib import Path

from check_local_html import check


class LocalHtmlCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "assets").mkdir()
        (self.root / "assets" / "site.css").write_text("body {}", encoding="utf-8")
        (self.root / "index.html").write_text(
            '<html id="top"><link href="assets/site.css"><a href="pages/about.html#about">About</a></html>',
            encoding="utf-8",
        )
        (self.root / "pages").mkdir()
        (self.root / "pages" / "about.html").write_text('<html><h1 id="about">About</h1></html>', encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_local_file_and_fragment_pass(self):
        _, failures, checked = check(self.root)
        self.assertEqual([], failures)
        self.assertEqual(2, len(checked))

    def test_missing_file_is_reported(self):
        (self.root / "index.html").write_text('<a href="missing.html">Missing</a>', encoding="utf-8")
        _, failures, _ = check(self.root)
        self.assertEqual(1, len(failures))
        self.assertIn("missing local target", failures[0])

    def test_missing_fragment_is_reported(self):
        (self.root / "index.html").write_text('<a href="pages/about.html#missing">Missing</a>', encoding="utf-8")
        _, failures, _ = check(self.root)
        self.assertEqual(1, len(failures))
        self.assertIn("missing fragment", failures[0])


if __name__ == "__main__":
    unittest.main()
