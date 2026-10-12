#!/usr/bin/env python3
"""Validate every record under records/ against the catalog rules.

Usage: python3 scripts/validate.py [RECORDS_DIR]
Exit code 0 = all records valid, 1 = at least one problem (printed as `<file>: <problem>`).

Only dependency: PyYAML (`pip install pyyaml`). The rules mirror schema/record.schema.json;
the JSON Schema file is the human/editor-facing contract, this script is the CI gate.
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "record.schema.json"
TEMPLATE_NAME = "_template.yml"


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _enum(schema: dict, *keys: str) -> list:
    node = schema["properties"]
    for key in keys[:-1]:
        node = node[key]["properties"]
    return node[keys[-1]]["enum"]


def _check_object(data: dict, spec: dict, prefix: str, problems: list[str]) -> None:
    """Check required keys, unknown keys, types, enums, patterns and min lengths for one object."""
    props = spec.get("properties", {})
    for key in spec.get("required", []):
        if key not in data:
            problems.append(f"{prefix}missing required field `{key}`")
    if not spec.get("additionalProperties", True):
        for key in data:
            if key not in props:
                problems.append(f"{prefix}unknown field `{key}`")
    for key, value in data.items():
        rule = props.get(key)
        if rule is None:
            continue
        name = f"{prefix}{key}"
        typ = rule.get("type")
        if typ == "string" and isinstance(value, datetime.date):
            value = value.isoformat()  # YAML parses an unquoted 2026-01-01 as a date; accept it
        if typ == "string":
            if not isinstance(value, str):
                problems.append(f"{name}: must be a string")
                continue
            if "enum" in rule and value not in rule["enum"]:
                problems.append(f"{name}: `{value}` not one of {rule['enum']}")
            if "pattern" in rule and not re.search(rule["pattern"], value):
                problems.append(f"{name}: `{value}` does not match {rule['pattern']}")
            if len(value.strip()) < rule.get("minLength", 0):
                problems.append(f"{name}: must not be empty")
            if len(value) > rule.get("maxLength", 10**9):
                problems.append(f"{name}: longer than {rule['maxLength']} characters")
        elif typ == "boolean":
            if not isinstance(value, bool):
                problems.append(f"{name}: must be true or false")
        elif typ == "array":
            if not isinstance(value, list):
                problems.append(f"{name}: must be a list")
                continue
            if len(value) < rule.get("minItems", 0):
                problems.append(f"{name}: must have at least {rule['minItems']} item(s)")
            if rule.get("uniqueItems") and len(set(map(str, value))) != len(value):
                problems.append(f"{name}: duplicate items")
            item_rule = rule.get("items", {})
            for item in value:
                if not isinstance(item, str):
                    problems.append(f"{name}: items must be strings")
                elif "enum" in item_rule and item not in item_rule["enum"]:
                    problems.append(f"{name}: `{item}` not one of {item_rule['enum']}")
                elif "pattern" in item_rule and not re.search(item_rule["pattern"], item):
                    problems.append(f"{name}: `{item}` does not match {item_rule['pattern']}")
        elif typ == "object":
            if not isinstance(value, dict):
                problems.append(f"{name}: must be a mapping")
                continue
            _check_object(value, rule, f"{name}.", problems)


def validate_record(data: object, file_name: str, schema: dict) -> list[str]:
    """Return a list of problems for one parsed record (empty list = valid)."""
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["top level must be a mapping"]
    _check_object(data, schema, "", problems)

    stem = file_name[:-4] if file_name.endswith(".yml") else file_name
    if isinstance(data.get("id"), str) and data["id"] != stem:
        problems.append(f"id: `{data['id']}` must equal the file name `{stem}`")
    expected, actual = data.get("expected"), data.get("actual")
    if isinstance(expected, str) and isinstance(actual, str) and expected.strip() == actual.strip():
        problems.append("expected and actual are identical; a record must show a difference")
    verification = data.get("verification")
    if isinstance(verification, dict) and verification.get("status") == "unverified":
        notes = verification.get("notes")
        if not isinstance(notes, str) or not notes.strip():
            problems.append("verification.notes: say why the reproduction could not be run (required when unverified)")
    return problems


def validate_dir(records_dir: Path, schema: dict | None = None) -> dict[str, list[str]]:
    """Validate every *.yml in records_dir except the template. Returns {file: [problems]} for failures only."""
    schema = schema or load_schema()
    failures: dict[str, list[str]] = {}
    seen_urls: dict[str, str] = {}
    files = sorted(p for p in records_dir.glob("*.yml") if p.name != TEMPLATE_NAME)
    if not files:
        failures["(records)"] = ["no records found"]
    for path in files:
        try:
            with path.open(encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            failures[path.name] = [f"YAML parse error: {exc}"]
            continue
        problems = validate_record(data, path.name, schema)
        if isinstance(data, dict) and isinstance(data.get("upstream"), dict):
            url = data["upstream"].get("url")
            op = data.get("operation")
            key = f"{url} {op}"
            if isinstance(url, str) and key in seen_urls:
                problems.append(f"upstream.url + operation duplicates {seen_urls[key]}")
            elif isinstance(url, str):
                seen_urls[key] = path.name
        if problems:
            failures[path.name] = problems
    return failures


def main(argv: list[str]) -> int:
    records_dir = Path(argv[1]) if len(argv) > 1 else ROOT / "records"
    failures = validate_dir(records_dir)
    total = len([p for p in records_dir.glob("*.yml") if p.name != TEMPLATE_NAME])
    for file_name, problems in failures.items():
        for problem in problems:
            print(f"{file_name}: {problem}")
    if failures:
        print(f"{len(failures)} of {total} record(s) invalid")
        return 1
    print(f"{total} record(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
