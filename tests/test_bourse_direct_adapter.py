import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "bourse_direct_adapter", ROOT / "playwright/bourse_direct/bourse_direct_adapter.py"
)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class FakeApi:
    months = ((2026, 1),)

    def __init__(self):
        self.offered_count = 0
        self.saved = []

    def call(self, name):
        return """<select id='nc'><option value='42' selected>Holder (Compte PEA)</option></select>
        <a href="javascript:MoisPrecedent('RO',42,1,2026)">Previous</a>
        <a class='linkE' href="javascript:ouvrePopup('/priv/new/releveOpe.php?nc=42&amp;type=RO&amp;year=2026&amp;month=1&amp;day=4&amp;trash=/avis.pdf')">4</a>"""

    def offered(self, count):
        self.offered_count += count

    def read(self, url):
        return b"<a href='/priv/new/releveOpe.php?nc=42&amp;type=RO&amp;year=2026&amp;month=1&amp;day=4&amp;trash=/avis.pdf&amp;pdf=1'>Format PDF</a>"

    def save_original(self, url, filename):
        self.saved.append((url, filename))


class BourseDirectAdapterTests(unittest.TestCase):
    def test_offered_identity_and_original_link_are_checked(self):
        api = FakeApi()
        adapter.collect(api, {"account_type": "PEA", "max_months": 13, "max_items": 100, "timeout_ms": 1000})
        self.assertEqual(api.offered_count, 1)
        self.assertEqual(len(api.saved), 1)
        self.assertTrue(api.saved[0][1].endswith("2026-01-04.pdf"))

    def test_wrong_source_path_fails_closed(self):
        with self.assertRaises(ValueError):
            adapter._target("https://www.boursedirect.fr/other?nc=42&type=RO&year=2026&month=1&day=4&trash=/avis.pdf", "42", (2026, 1))
