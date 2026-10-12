"""Tests for scripts/validate.py. Run: python3 -m unittest discover -s tests -v"""
import copy
import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate as v  # noqa: E402

GOOD = {
    "id": "python-lower-example",
    "title": "lower() turns İ into i + U+0307 in example",
    "language": "python",
    "library": "stdlib",
    "operation": "lower",
    "letters": ["İ", "i"],
    "locale_dependent": False,
    "input": "İ",
    "expected": "i",
    "actual": "i̇ (two code points)",
    "reproduction": {"command": "python3 -c 'print(len(\"İ\".lower()))'", "environment": "Python 3.13"},
    "upstream": {"url": "https://github.com/python/cpython/issues/61454", "status": "by-design"},
    "verification": {"status": "verified", "by": "halilunay", "date": "2026-10-12"},
}


class RecordRules(unittest.TestCase):
    def setUp(self):
        self.schema = v.load_schema()

    def check(self, data, name="python-lower-example.yml"):
        return v.validate_record(data, name, self.schema)

    def test_good_record_is_valid(self):
        self.assertEqual(self.check(GOOD), [])

    def test_every_required_field_is_enforced(self):
        for key in self.schema["required"]:
            bad = copy.deepcopy(GOOD)
            del bad[key]
            self.assertTrue(any(f"`{key}`" in p for p in self.check(bad)), key)

    def test_id_must_match_file_name(self):
        problems = self.check(GOOD, "something-else.yml")
        self.assertTrue(any("must equal the file name" in p for p in problems))

    def test_enums_are_enforced(self):
        bad = copy.deepcopy(GOOD)
        bad["operation"] = "shout"
        bad["letters"] = ["j"]
        bad["upstream"]["status"] = "maybe"
        problems = self.check(bad)
        self.assertEqual(len([p for p in problems if "not one of" in p]), 3, problems)

    def test_unknown_and_wrong_type_fields(self):
        bad = copy.deepcopy(GOOD)
        bad["locale_dependent"] = "no"
        bad["extra"] = 1
        bad["upstream"]["url"] = "http://insecure.example"
        problems = self.check(bad)
        self.assertTrue(any("true or false" in p for p in problems))
        self.assertTrue(any("unknown field `extra`" in p for p in problems))
        self.assertTrue(any("does not match" in p for p in problems))

    def test_expected_must_differ_from_actual(self):
        bad = copy.deepcopy(GOOD)
        bad["actual"] = "i"
        self.assertTrue(any("identical" in p for p in self.check(bad)))

    def test_unverified_needs_notes(self):
        bad = copy.deepcopy(GOOD)
        bad["verification"]["status"] = "unverified"
        self.assertTrue(any("verification.notes" in p for p in self.check(bad)))
        bad["verification"]["notes"] = "no Windows machine available"
        self.assertEqual(self.check(bad), [])

    def test_verifier_may_be_a_declared_ai_tool_with_a_reviewer(self):
        ai = copy.deepcopy(GOOD)
        ai["verification"]["by"] = "claude-code (AI), reviewed by halilunay"
        self.assertEqual(self.check(ai), [])
        blank = copy.deepcopy(GOOD)
        blank["verification"]["by"] = "  "
        self.assertTrue(any("verification.by: must not be empty" in p for p in self.check(blank)))

    def test_non_mapping_is_rejected(self):
        self.assertEqual(self.check(["list"]), ["top level must be a mapping"])


class Directory(unittest.TestCase):
    def write(self, folder, name, data):
        with open(os.path.join(folder, name), "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, allow_unicode=True)

    def test_template_is_skipped_and_duplicates_are_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "_template.yml", {"id": "broken"})
            self.write(tmp, "python-lower-example.yml", GOOD)
            dup = copy.deepcopy(GOOD)
            dup["id"] = "python-lower-twin"
            self.write(tmp, "python-lower-twin.yml", dup)
            failures = v.validate_dir(Path(tmp))
            self.assertEqual(list(failures), ["python-lower-twin.yml"])
            self.assertIn("duplicates python-lower-example.yml", failures["python-lower-twin.yml"][0])

    def test_empty_dir_and_parse_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(v.validate_dir(Path(tmp)), {"(records)": ["no records found"]})
            with open(os.path.join(tmp, "x-y-z.yml"), "w", encoding="utf-8") as fh:
                fh.write("id: [unclosed\n")
            failures = v.validate_dir(Path(tmp))
            self.assertIn("YAML parse error", failures["x-y-z.yml"][0])

    def test_shipped_records_are_valid(self):
        records = Path(__file__).resolve().parent.parent / "records"
        self.assertEqual(v.validate_dir(records), {})

    def test_main_exit_codes(self):
        records = Path(__file__).resolve().parent.parent / "records"
        self.assertEqual(v.main(["validate.py", str(records)]), 0)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(v.main(["validate.py", tmp]), 1)


if __name__ == "__main__":
    unittest.main()
