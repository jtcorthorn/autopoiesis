"""Neutral regression cases. Fixtures are retained; no cleanup or live-instance writes."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
import unittest
from routecheck import observe

FIXTURES = None


class RouteChecks(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="route-test-", dir=FIXTURES))
        (self.root / "catalog").mkdir()
        (self.root / "MAPA.md").write_text("| Catalog | catalog/MAPA.md |\n", encoding="utf-8")
        (self.root / "catalog/MAPA.md").write_text("Machine source: `items.json`.\n", encoding="utf-8")
        (self.root / "catalog/items.json").write_text('{"items":[1,2]}', encoding="utf-8")
        self.manifest = {"version": 1, "routes": [{"id": "catalog", "entry": "MAPA.md",
                         "map": "catalog/MAPA.md", "registry": "catalog/items.json", "collections": ["items"]}]}

    def test_valid_read_only(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        report = observe(self.root, self.manifest)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["routes"][0]["counts"], {"items": 2})
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_generic_directory_is_not_route(self):
        (self.root / "MAPA.md").write_text("Catalog: catalog/\n", encoding="utf-8")
        self.assertEqual(observe(self.root, self.manifest)["status"], "GAP")

    def test_missing_machine_route(self):
        (self.root / "catalog/MAPA.md").write_text("Catalog exists.\n", encoding="utf-8")
        self.assertEqual(observe(self.root, self.manifest)["status"], "GAP")

    def test_example_is_not_route(self):
        (self.root / "MAPA.md").write_text("```\ncatalog/MAPA.md\n```\n", encoding="utf-8")
        self.assertEqual(observe(self.root, self.manifest)["status"], "GAP")

    def test_invalid_json_is_incomplete(self):
        (self.root / "catalog/items.json").write_text("{bad", encoding="utf-8")
        self.assertEqual(observe(self.root, self.manifest)["status"], "INCOMPLETE")

    def test_missing_source_is_incomplete(self):
        self.manifest["routes"][0]["registry"] = "catalog/absent.json"
        self.assertEqual(observe(self.root, self.manifest)["status"], "INCOMPLETE")

    def test_wrong_collection_is_incomplete(self):
        (self.root / "catalog/items.json").write_text('{"items":0}', encoding="utf-8")
        self.assertEqual(observe(self.root, self.manifest)["status"], "INCOMPLETE")

    def test_escape_and_absolute_rejected(self):
        for invalid in ("../outside.json", "C:/outside.json", "/outside.json", "a\\b.json"):
            with self.subTest(path=invalid):
                spec = copy.deepcopy(self.manifest)
                spec["routes"][0]["registry"] = invalid
                with self.assertRaises(ValueError):
                    observe(self.root, spec)

    def test_empty_coverage_rejected(self):
        with self.assertRaises(ValueError):
            observe(self.root, {"version": 1, "routes": []})

    def test_duplicate_identity_rejected(self):
        self.manifest["routes"].append(copy.deepcopy(self.manifest["routes"][0]))
        with self.assertRaises(ValueError):
            observe(self.root, self.manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", required=True)
    args, rest = parser.parse_known_args()
    FIXTURES = Path(args.fixtures).resolve(strict=True)
    unittest.main(argv=[__file__] + rest)
