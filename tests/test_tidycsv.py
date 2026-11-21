import sys, unittest
sys.path.insert(0, ".")
from tidycsv.core import (analyze_and_clean, normalize_date, normalize_money,
                          normalize_phone, read_rows)

MESSY = """nama,no_hp,harga,tanggal
Budi,0812-3456-7890,"Rp 1.500.000",12/11/2026
 Budi ,+62 812 3456 7890,"Rp 1.500.000",12/11/2026
Sari,6281312345678,75000,2026-11-13
"""

class PhoneTests(unittest.TestCase):
    def test_local_format(self):
        self.assertEqual(normalize_phone("0812-3456-7890"), ("+6281234567890", True))
    def test_already_international(self):
        self.assertEqual(normalize_phone("+6281234567890"), ("+6281234567890", False))
    def test_bare_62(self):
        self.assertEqual(normalize_phone("6281312345678"), ("+6281312345678", True))
    def test_non_phone_left_alone(self):
        self.assertEqual(normalize_phone("12345"), ("12345", False))

class MoneyTests(unittest.TestCase):
    def test_rupiah_thousands(self):
        self.assertEqual(normalize_money("Rp 1.500.000"), ("1500000", True))
    def test_plain_number(self):
        self.assertEqual(normalize_money("75000"), ("75000", False))
    def test_decimal_comma(self):
        self.assertEqual(normalize_money("Rp 25.500,50"), ("25500.5", True))
    def test_text_left_alone(self):
        self.assertEqual(normalize_money("gratis"), ("gratis", False))

class DateTests(unittest.TestCase):
    def test_slash_dmy(self):
        self.assertEqual(normalize_date("12/11/2026"), ("2026-11-12", True))
    def test_iso_stays(self):
        self.assertEqual(normalize_date("2026-11-13"), ("2026-11-13", False))
    def test_month_name(self):
        self.assertEqual(normalize_date("5 Jan 2027"), ("2027-01-05", True))

class CleanTests(unittest.TestCase):
    def test_report_and_clean(self):
        rows = read_rows(MESSY)
        report, cleaned = analyze_and_clean(rows)
        self.assertEqual(report["rows"], 3)
        self.assertEqual(report["issues"]["duplicate_rows"], 1)
        self.assertEqual(report["rows_after_clean"], 2)
        self.assertEqual(cleaned[1][1], "+6281234567890")
        self.assertEqual(cleaned[1][2], "1500000")
        self.assertEqual(cleaned[1][3], "2026-11-12")
        self.assertEqual(cleaned[2][3], "2026-11-13")

if __name__ == "__main__":
    unittest.main()
