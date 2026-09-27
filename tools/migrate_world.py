from __future__ import annotations

import argparse
from pathlib import Path

from storage.converter import (
    LegacyConverter,
    write_conversion_report,
    write_human_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert one legacy Adventure world ZIP into a canonical package."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "destination",
        type=Path,
        nargs="?",
        help="Defaults to <source>.canonical.zip",
    )
    parser.add_argument(
        "--allow-lossy",
        action="store_true",
        help="Permit explicitly reported unsupported legacy fields.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing destination after successful validation.",
    )
    args = parser.parse_args()

    converter = LegacyConverter()
    report = converter.convert_file(
        args.source,
        args.destination,
        allow_lossy=args.allow_lossy,
        force=args.force,
    )
    destination = Path(report.output)
    write_conversion_report(
        report,
        destination.with_name(destination.name + ".report.json"),
    )
    write_human_report(
        report,
        destination.with_name(destination.name + ".report.txt"),
    )

    print(f"Converted: {report.source}")
    print(f"Output:    {report.output}")
    print(f"Result:    {report.result}")
    print(f"SHA-256:   {report.output_sha256}")
    if report.discarded:
        print("Discarded:")
        for entry in report.discarded:
            print(f"  - {entry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
