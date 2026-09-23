"""CLI entry point for Mulberry Document Model tooling."""

import argparse
import json
import sys
from pathlib import Path

from processing.exporter import (
    generate_json_schema,
    create_realistic_example,
    generate_typescript_definitions,
)
from processing.models.document import Document


def export_artifacts(base_dir: Path) -> None:
    """Generate and write schema.json, example.json, and TypeScript definitions."""
    processing_dir = base_dir / "processing"
    src_types_dir = base_dir / "src" / "types"

    processing_dir.mkdir(parents=True, exist_ok=True)
    src_types_dir.mkdir(parents=True, exist_ok=True)

    # 1. JSON Schema
    schema = generate_json_schema()
    schema_path = processing_dir / "schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"✅ Generated JSON Schema: {schema_path}")

    # 2. Realistic Example JSON
    example_doc = create_realistic_example()
    example_path = processing_dir / "example.json"
    with open(example_path, "w", encoding="utf-8") as f:
        f.write(example_doc.model_dump_json(indent=2))
    print(f"✅ Generated Realistic Example Document: {example_path}")

    # 3. TypeScript Definitions
    ts_defs = generate_typescript_definitions()
    ts_path = src_types_dir / "document.ts"
    with open(ts_path, "w", encoding="utf-8") as f:
        f.write(ts_defs)
    print(f"✅ Generated TypeScript Types: {ts_path}")


def validate_file(file_path: Path) -> bool:
    """Validate a JSON file against Pydantic Document model."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        doc = Document.model_validate(data)
        print(f"✅ Validation successful: '{file_path}' is a valid Mulberry Document (id={doc.id}).")
        return True
    except Exception as e:
        print(f"❌ Validation failed for '{file_path}':\n{e}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Mulberry Canonical Document Model Tooling")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # export subcommand
    export_parser = subparsers.add_parser("export", help="Export JSON schema, example JSON, and TS definitions")
    export_parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Root workspace directory",
    )

    # validate subcommand
    val_parser = subparsers.add_parser("validate", help="Validate a JSON document file")
    val_parser.add_argument("file", type=Path, help="Path to JSON file to validate")

    args = parser.parse_args()

    if args.command == "export" or args.command is None:
        root_path = getattr(args, "root", Path(__file__).resolve().parents[3])
        export_artifacts(root_path)
    elif args.command == "validate":
        success = validate_file(args.file)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
