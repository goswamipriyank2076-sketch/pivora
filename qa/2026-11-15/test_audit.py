"""Read-only application audit; all writes use a temporary test profile."""
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import watertime as w


class Audit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.file = Path(self.tmp.name) / 'data.json'
        self.patch = patch.object(w, 'DATA_FILE', self.file)
        self.patch.start()
        self.d = w.WaterData()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_add_and_reload(self):
        self.d.add_glass()
        self.assertEqual(w.WaterData().count, 1)
        self.assertEqual(self.d.litres_drunk, .25)

    def test_undo_floor(self):
        self.assertFalse(self.d.undo_glass())
        self.d.add_glass()
        self.assertTrue(self.d.undo_glass())
        self.assertEqual(self.d.count, 0)

    def test_goal_percentage_cap(self):
        self.d.set_glass_count(12)
        self.assertEqual(self.d.percentage, 100)

    def test_positive_limits(self):
        self.d.set_goal(0)
        self.d.set_interval(-1)
        self.d.set_snooze_interval(0)
        self.assertEqual((self.d.goal, self.d.interval_minutes, self.d.snooze_interval_minutes), (1, 1, 1))

    def test_day_rollover(self):
        yesterday = str(date.today() - timedelta(days=1))
        self.d.data.update(date=yesterday, glasses_count=8)
        self.assertEqual(self.d.count, 0)
        self.assertEqual(self.d.data['history'][yesterday], 8)

    def test_streak(self):
        self.d.data['history'][str(date.today() - timedelta(days=1))] = 8
        self.d.set_glass_count(8)
        self.assertEqual(self.d.streak, 2)

    def test_seven_days(self):
        self.assertEqual(len(self.d.get_last_7_days()), 7)

    def test_time_roundtrip(self):
        for hour in range(24):
            self.assertEqual(w.parse_12h_hour(w.hour_to_12h(hour)), hour)

    def test_malformed_json_fallback(self):
        self.file.write_text('{broken')
        self.assertEqual(w.WaterData().count, 0)

    def test_active_hours_survive_restart(self):
        for end in (20, 21):
            self.d.set_work_hours(8, end)
            for day in (date.today(), date.today() - timedelta(days=1)):
                profile = json.loads(self.file.read_text(encoding='utf-8'))
                profile['date'] = str(day)
                self.file.write_text(json.dumps(profile), encoding='utf-8')
                loaded = w.WaterData()
                self.assertEqual((loaded.work_start_hour, loaded.work_end_hour), (8, end))

    def test_reset_clears_today_history(self):
        yesterday = str(date.today() - timedelta(days=1))
        self.d.data['history'][yesterday] = 3
        self.d.add_glass()
        self.d.reset()
        loaded = w.WaterData()
        self.assertEqual(loaded.count, 0)
        self.assertEqual(loaded.data['history'], {yesterday: 3})

    def test_save_failure_is_reported(self):
        self.d.add_glass()
        original = self.file.read_bytes()
        for operation in ('write_text', 'replace'):
            with patch.object(Path, operation, side_effect=PermissionError('test failure')):
                with self.assertRaises(w.DataSaveError):
                    self.d.add_glass()
            self.assertEqual(self.d.count, 1)
            self.assertEqual(self.file.read_bytes(), original)
            self.assertEqual(list(self.file.parent.iterdir()), [self.file])
        self.d.add_glass()
        self.assertEqual(w.WaterData().count, 2)

    def test_save_error_callback_shows_dialog(self):
        app = Mock()
        error = w.DataSaveError('Could not save your changes. Please try again.')
        with patch.object(w.messagebox, 'showerror') as show_error:
            w.WatertimeApp._report_callback_exception(app, type(error), error, None)
        show_error.assert_called_once_with('Pivora', str(error), parent=app.root)

    def test_overnight_schedule_triggers(self):
        self.d.set_work_start_hour(22)
        self.d.set_work_end_hour(6)
        self.d.set_pause_on_meeting(False)
        app = Mock()
        app.data = self.d
        app.dnd_until = 0
        app.next_reminder_time = 0
        for hour, active in ((21, False), (22, True), (23, True), (0, True), (5, True), (6, False)):
            with self.subTest(hour=hour):
                app.next_reminder_time = 0
                app.trigger_reminder.reset_mock()
                with patch.object(w.time, 'localtime', return_value=Mock(tm_hour=hour)):
                    w.WatertimeApp._check_timer_loop(app)
                self.assertEqual(app.trigger_reminder.call_count, int(active))


if __name__ == '__main__':
    unittest.main(verbosity=2)
