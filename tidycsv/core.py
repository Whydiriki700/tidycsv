"""Core analysis and cleaning for tidycsv.

Four mess classes are handled:
- duplicate rows (exact copies)
- stray whitespace in every cell
- phone columns: Indonesian numbers in mixed formats normalized to +62 form
- money columns: strings like "Rp 1.500.000" turned into plain integers
- date columns: mixed common formats normalized to ISO yyyy-mm-dd
"""
import csv
import io
import re
from datetime import datetime

PHONE_HINTS = ("phone", "hp", "telp", "telepon", "wa", "whatsapp", "mobile", "kontak")
MONEY_HINTS = ("harga", "price", "total", "nominal", "amount", "biaya", "tarif")
DATE_HINTS = ("tanggal", "date", "tgl", "waktu", "time")

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y",
                "%d/%m/%y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y")


def column_kind(header):
    h = header.strip().lower()
    if any(k in h for k in PHONE_HINTS):
        return "phone"
    if any(k in h for k in MONEY_HINTS):
        return "money"
    if any(k in h for k in DATE_HINTS):
        return "date"
    return "text"


def normalize_phone(value):
    digits = re.sub(r"\D", "", value)
    if not digits:
        return value.strip(), False
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif digits.startswith("62"):
        pass
    elif digits.startswith("8"):
        digits = "62" + digits
    else:
        return value.strip(), False
    result = "+" + digits
    return result, result != value.strip()


def normalize_money(value):
    v = value.strip()
    if not v:
        return v, False
    cleaned = re.sub(r"(?i)rp\.?\s*", "", v).strip()
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d+(,\d+)?", cleaned):
        cleaned = cleaned.replace(",", ".")
    elif re.fullmatch(r"-?\d+", cleaned):
        pass
    else:
        return v, False
    if "." in cleaned:
        number = float(cleaned)
        text = str(int(number)) if number == int(number) else str(number)
    else:
        text = str(int(cleaned))
    return text, text != v


def normalize_date(value):
    v = value.strip()
    if not v:
        return v, False
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(v, fmt)
            iso = parsed.strftime("%Y-%m-%d")
            return iso, iso != v
        except ValueError:
            continue
    return v, False


NORMALIZERS = {"phone": normalize_phone, "money": normalize_money, "date": normalize_date}


def read_rows(text, delimiter=","):
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    return [row for row in reader]


def analyze_and_clean(rows):
    """Returns (report_dict, cleaned_rows)."""
    if not rows:
        return {"rows": 0, "columns": 0, "issues": {}}, []
    header = [c.strip() for c in rows[0]]
    kinds = [column_kind(h) for h in header]
    width = len(header)
    issues = {"duplicate_rows": 0, "ragged_rows": 0, "whitespace_cells": 0,
              "phones_normalized": 0, "money_normalized": 0, "dates_normalized": 0}
    cleaned = [header]
    seen = set()
    for row in rows[1:]:
        if len(row) != width:
            issues["ragged_rows"] += 1
            row = (row + [""] * width)[:width]
        out = []
        for idx, cell in enumerate(row):
            value = cell.strip()
            if value != cell:
                issues["whitespace_cells"] += 1
            kind = kinds[idx]
            if kind in NORMALIZERS and value:
                new_value, changed = NORMALIZERS[kind](value)
                if changed:
                    counter = {"phone": "phones_normalized", "money": "money_normalized",
                               "date": "dates_normalized"}[kind]
                    issues[counter] += 1
                    value = new_value
            out.append(value)
        key = tuple(out)
        if key in seen:
            issues["duplicate_rows"] += 1
            continue
        seen.add(key)
        cleaned.append(out)
    report = {
        "rows": len(rows) - 1,
        "columns": width,
        "rows_after_clean": len(cleaned) - 1,
        "column_kinds": dict(zip(header, kinds)),
        "issues": issues,
    }
    return report, cleaned


def rows_to_csv(rows, delimiter=","):
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    writer.writerows(rows)
    return buffer.getvalue()
