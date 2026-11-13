"""Regression tests for the deployed-site link checker."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_site import check_site


class SiteChecks(unittest.TestCase):
    def test_baseurl_unicode_anchor_and_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text('<a href="/notes/chapter.html#%E8%AF%84%E4%BC%B0">read</a>')
            (root / "chapter.html").write_text('<h2 id="评估">评估</h2><img src="image.png"><a href="https://example.org/missing">external</a>')
            (root / "image.png").write_bytes(b"fixture")
            (root / "search.json").write_text('[{"title":"Home","url":"/notes/"}]')
            errors, checked = check_site(root, "/notes")
            self.assertEqual(errors, [])
            self.assertEqual(checked, 2)

    def test_missing_anchor_asset_and_wrong_baseurl(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text('<a href="#missing">x</a><img src="gone.png"><a href="/wrong/">x</a>')
            (root / "search.json").write_text('[{"title":"Home","url":"/notes/"}]')
            errors, _ = check_site(root, "/notes")
            self.assertEqual(len(errors), 3)

    def test_invalid_search_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text('<h1>Home</h1>')
            (root / "search.json").write_text('[{"title":"Missing","url":"/notes/gone.html"}]')
            errors, _ = check_site(root, "/notes")
            self.assertEqual(len(errors), 1)

    def test_missing_search_index_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text('<h1>Home</h1>')
            errors, _ = check_site(root, "/notes")
            self.assertEqual(errors, ["missing search.json; the site search cannot work"])


if __name__ == "__main__":
    unittest.main()
