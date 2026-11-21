"""CLI: python -m tidycsv [--clean -o OUT] [--json] file.csv"""
import argparse
import json
import sys

from .core import analyze_and_clean, read_rows, rows_to_csv


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tidycsv", description="Report and clean messy CSV files.")
    parser.add_argument("file", help="CSV file to inspect")
    parser.add_argument("--delimiter", default=",", help="Field delimiter (default ,)")
    parser.add_argument("--clean", action="store_true", help="Write the cleaned CSV")
    parser.add_argument("-o", "--output", help="Output path for --clean (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON")
    args = parser.parse_args(argv)

    with open(args.file, encoding="utf-8-sig", newline="") as handle:
        text = handle.read()
    rows = read_rows(text, delimiter=args.delimiter)
    report, cleaned = analyze_and_clean(rows)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"rows: {report['rows']}  columns: {report['columns']}  rows after clean: {report['rows_after_clean']}")
        for name, count in report["issues"].items():
            print(f"  {name}: {count}")
    if args.clean:
        output = rows_to_csv(cleaned, delimiter=args.delimiter)
        if args.output:
            with open(args.output, "w", encoding="utf-8", newline="") as handle:
                handle.write(output)
        else:
            sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
