import csv
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from csv_processor import CsvProcessor
from kousu import rounded_hours, seconds_between


class TimeCalculationTests(unittest.TestCase):
    def test_uses_wall_clock_time_across_sleep_and_day_boundary(self):
        start = datetime(2026, 8, 30, 23, 59, 50)
        end = start + timedelta(hours=2, seconds=10)
        self.assertEqual(seconds_between(start, end), 7210)
        self.assertAlmostEqual(rounded_hours(start, end), 7210 / 3600)

    def test_rounding_is_optional(self):
        start = datetime(2026, 8, 30, 10, 0)
        end = start + timedelta(minutes=16)
        self.assertEqual(rounded_hours(start, end, 15), 0.5)
        self.assertAlmostEqual(rounded_hours(start, end, 0), 16 / 60)


class CsvProcessorTests(unittest.TestCase):
    def test_new_csv_has_header_and_record(self):
        with tempfile.TemporaryDirectory() as directory:
            processor = CsvProcessor(directory)
            processor.write_record("20260830", "調査", 0.5, "10:00", "10:30")
            with open(Path(directory) / "20260830.csv", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[0], processor.header)
            self.assertEqual(rows[1][0], "調査")

    def test_old_headerless_csv_is_repaired_without_losing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "20260830.csv"
            path.parent.mkdir(exist_ok=True)
            path.write_text("調査,0.5,10:00,10:30\n", encoding="utf-8")
            processor = CsvProcessor(directory)
            rows = processor.ensure_csv_file("20260830")
            self.assertEqual(rows[0], processor.header)
            self.assertEqual(rows[1][0], "調査")

    def test_summary_accepts_headerless_legacy_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "20260830.csv"
            path.write_text("調査,0.5,10:00,10:30\n", encoding="utf-8")
            processor = CsvProcessor(directory)
            self.assertEqual(processor.get_day_summarized(datetime(2026, 8, 30)), {"調査": 0.5})


if __name__ == "__main__":
    unittest.main()
