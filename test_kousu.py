import csv
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from csv_processor import CsvProcessor
from config_manager import ConfigManager
from kousu import KousuApp, parse_time_today, rounded_hours, seconds_between


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

    def test_rounding_does_not_round_up_exact_boundary(self):
        start = datetime(2026, 8, 30, 10, 0)
        end = start + timedelta(minutes=30)
        self.assertEqual(rounded_hours(start, end, 15), 0.5)

    def test_negative_elapsed_time_is_clamped_to_zero(self):
        end = datetime(2026, 8, 30, 10, 0)
        start = end + timedelta(minutes=1)
        self.assertEqual(seconds_between(start, end), 0.0)
        self.assertEqual(rounded_hours(start, end, 15), 0.0)

    def test_parse_time_today_uses_given_date_and_clears_seconds(self):
        now = datetime(2026, 8, 30, 14, 25, 37, 123456)
        self.assertEqual(
            parse_time_today(" 09:05 ", now),
            datetime(2026, 8, 30, 9, 5),
        )

    def test_parse_time_today_rejects_invalid_time(self):
        with self.assertRaises(ValueError):
            parse_time_today("25:00", datetime(2026, 8, 30))


class CsvProcessorTests(unittest.TestCase):
    def test_new_csv_has_header_and_record(self):
        with tempfile.TemporaryDirectory() as directory:
            processor = CsvProcessor(directory)
            processor.write_record("20260830", "調査", 0.5, "10:00", "10:30")
            with open(Path(directory) / "20260830.csv", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[0], processor.header)
            self.assertEqual(rows[1], ["調査", "00:30", "10:00", "10:30"])

    def test_write_record_normalizes_clock_and_duration_formats(self):
        with tempfile.TemporaryDirectory() as directory:
            processor = CsvProcessor(directory)
            processor.write_record("20260830", "調査", 25 / 60, "09:05", "09:30")
            with open(Path(directory) / "20260830.csv", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[1], ["調査", "00:25", "09:05", "09:30"])

    def test_old_headerless_csv_is_repaired_without_losing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "20260830.csv"
            path.parent.mkdir(exist_ok=True)
            path.write_text("調査,0.5,10:00,10:30\n", encoding="utf-8")
            processor = CsvProcessor(directory)
            rows = processor.ensure_csv_file("20260830")
            self.assertEqual(rows[0], processor.header)
            self.assertEqual(rows[1], ["調査", "00:30", "10:00", "10:30"])

    def test_existing_headered_csv_legacy_duration_is_migrated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "20260830.csv"
            processor = CsvProcessor(directory)
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(processor.header)
                writer.writerow(["調査", "1.25", "10:00", "11:15"])

            rows = processor.ensure_csv_file("20260830")

            self.assertEqual(rows[1], ["調査", "01:15", "10:00", "11:15"])
            with path.open(encoding="utf-8-sig", newline="") as f:
                self.assertEqual(list(csv.reader(f))[1][1], "01:15")

    def test_summary_accepts_headerless_legacy_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "20260830.csv"
            path.write_text("調査,0.5,10:00,10:30\n", encoding="utf-8")
            processor = CsvProcessor(directory)
            self.assertEqual(processor.get_day_summarized(datetime(2026, 8, 30)), {"調査": 0.5})

    def test_summary_reads_hhmm_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            processor = CsvProcessor(directory)
            processor.write_record("20260830", "調査", 1.5, "10:00", "11:30")
            self.assertEqual(
                processor.get_day_summarized(datetime(2026, 8, 30)), {"調査": 1.5}
            )

    def test_day_summary_aggregates_same_task_and_ignores_short_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            processor = CsvProcessor(directory)
            path = Path(directory) / "20260830.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(processor.header)
                writer.writerow(["調査", "0.5", "10:00", "10:30"])
                writer.writerow(["調査", "1.25", "11:00", "12:15"])
                writer.writerow(["不完全な行"])
            self.assertEqual(
                processor.get_day_summarized(datetime(2026, 8, 30)), {"調査": 1.75}
            )

    def test_period_summary_includes_each_date_and_returns_totals(self):
        with tempfile.TemporaryDirectory() as directory:
            processor = CsvProcessor(directory)
            processor.write_record("20260830", "調査", 0.5, "10:00", "10:30")
            processor.write_record("20260831", "実装", 1.0, "10:00", "11:00")
            processor.write_record("20260831", "調査", 0.25, "13:00", "13:15")
            self.assertEqual(
                processor.get_summarized("20260830", "20260831"),
                {"調査": 0.75, "実装": 1.0},
            )

    def test_missing_day_is_an_empty_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            processor = CsvProcessor(directory)
            self.assertEqual(
                processor.get_day_summarized(datetime(2026, 8, 30)), {}
            )


class ConfigManagerTests(unittest.TestCase):
    def test_missing_config_is_created_with_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            config = ConfigManager(path)
            self.assertEqual(config.get("round_unit_minutes"), 5)
            self.assertEqual(config.get("idle_notice_minutes"), 1)
            self.assertTrue(path.is_file())

    def test_partial_config_is_completed_and_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"folder_name": "work"}', encoding="utf-8")
            config = ConfigManager(path)
            self.assertEqual(config.get("folder_name"), "work")
            self.assertEqual(config.get("system_font_family"), "Arial")
            reloaded = ConfigManager(path)
            self.assertEqual(reloaded.get("window_standby_width"), 400)

    def test_idle_notice_minutes_is_configurable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"idle_notice_minutes": 3}', encoding="utf-8")
            config = ConfigManager(path)
            self.assertEqual(config.get("idle_notice_minutes"), 3)

    def test_set_is_saved_and_get_supports_explicit_default(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            config = ConfigManager(path)
            config.set("round_unit_minutes", 15)
            config.set("custom_option", "value")
            reloaded = ConfigManager(path)
            self.assertEqual(reloaded.get("round_unit_minutes"), 15)
            self.assertEqual(reloaded.get("custom_option", "fallback"), "value")
            self.assertEqual(reloaded.get("missing_option", "fallback"), "fallback")

    def test_corrupt_config_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text("not json", encoding="utf-8")
            config = ConfigManager(path)
            self.assertEqual(config.config, ConfigManager.DEFAULT_CONFIG)


class KousuAppLogicTests(unittest.TestCase):
    def make_app_for_logic_test(self):
        app = KousuApp.__new__(KousuApp)
        app.is_counting = True
        app.task_name = "調査"
        app.time_count_started = datetime(2026, 8, 30, 23, 50)
        app.round_unit_minutes = 15
        app.csv_processor = Mock()
        app.show_standby_frame = Mock()
        return app

    def test_stop_uses_start_date_and_wall_clock_duration(self):
        app = self.make_app_for_logic_test()
        end = datetime(2026, 8, 31, 0, 10)

        with patch("kousu.messagebox.showinfo"):
            app.stop_counting(end)

        app.csv_processor.write_record.assert_called_once_with(
            date_str="20260830",
            task_name="調査",
            duration=0.5,
            start_time="23:50",
            end_time="00:10",
        )
        self.assertFalse(app.is_counting)
        app.show_standby_frame.assert_called_once_with()

    def test_interrupt_does_not_write_a_record(self):
        app = self.make_app_for_logic_test()

        app.interrupt_counting()

        app.csv_processor.write_record.assert_not_called()
        self.assertFalse(app.is_counting)
        app.show_standby_frame.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
