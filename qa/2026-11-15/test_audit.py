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
        app._displayed_day = self.d.day
        app.mascot.is_active = app.compact_overlay.is_active = False
        app.dnd_until = 0
        app.next_reminder_time = 0
        for hour, active in ((21, False), (22, True), (23, True), (0, True), (5, True), (6, False)):
            with self.subTest(hour=hour):
                app.next_reminder_time = 0
                app.trigger_reminder.reset_mock()
                with patch.object(w.time, 'localtime', return_value=Mock(tm_hour=hour)):
                    w.WatertimeApp._check_timer_loop(app)
                self.assertEqual(app.trigger_reminder.call_count, int(active))

    def test_quick_setup_preview_and_save_use_the_expected_settings(self):
        self.d.set_goal(11)
        original = self.file.read_bytes()
        app = Mock()
        app.data = self.d
        app.dnd_until = 0
        app.next_reminder_time = 1300
        app.tray = Mock()
        app.goal_options = app.interval_options = app.snooze_options = app.style_options = {}
        app._schedule_next_reminder.side_effect = lambda: w.WatertimeApp._schedule_next_reminder(app)
        entry = Mock()
        entry.get.return_value = 'Preview Name'
        buttons = {}
        fields = []

        def button(*args, text, command, **kwargs):
            buttons[text] = command
            return Mock()

        def combobox(*args, **kwargs):
            field = Mock()
            field.set.side_effect = lambda value: setattr(field.get, 'return_value', value)
            fields.append(field)
            return field

        widgets = Mock(Button=button, Entry=Mock(return_value=entry))
        with (patch.object(w, 'tk', widgets),
              patch.object(w.ttk, 'Combobox', side_effect=combobox),
              patch.object(w, 'screen_work_area', return_value=(0, 0, 1280, 800)),
              patch.object(w, 'load_app_icon_image', return_value=None),
              patch.object(w.time, 'time', return_value=1000)):
            w.WatertimeApp.open_quick_setup(app)
            self.assertEqual(fields[0].get(), '11 glasses')
            fields[1].set('30 mins')
            fields[4].set('Compact (Corner Notification)')
            fields[5].set('5 mins')
            buttons['Preview Reminder']()
            app._show_reminder.assert_called_once_with('compact', preview=w.ReminderPreview('Preview Name', 5))
            self.assertEqual(self.file.read_bytes(), original)
            self.assertEqual(self.d.reminder_style, 'mascot')
            self.assertEqual(self.d.snooze_interval_minutes, 10)
            self.assertEqual(app.next_reminder_time, 1300)

            buttons['Save & Get Started']()
            saved = w.WaterData()
            self.assertEqual((saved.goal, saved.interval_minutes, saved.reminder_style), (11, 30, 'compact'))
            self.assertEqual((saved.user_name, saved.snooze_interval_minutes), ('Preview Name', 5))
            self.assertEqual(app.next_reminder_time, 2800)
            app.tray.update_menu.assert_called_once()

    def test_preview_buttons_do_not_log_or_snooze(self):
        for handler in ('_handle_log', '_handle_snooze', '_handle_auto_dismiss'):
            with self.subTest(handler=handler):
                overlay = w.CompactReminderOverlay.__new__(w.CompactReminderOverlay)
                overlay.data = self.d
                overlay.preview = w.ReminderPreview('Preview Name', 30)
                overlay.win = Mock()
                overlay.dismiss_job = 'timer'
                overlay.on_log = Mock()
                overlay.on_snooze = Mock()
                overlay.on_close = Mock()
                getattr(overlay, handler)()
                overlay.on_log.assert_not_called()
                overlay.on_snooze.assert_not_called()
                overlay.on_close.assert_not_called()
                overlay.win.withdraw.assert_called_once()
        for handler in ('on_yes', 'on_later'):
            with self.subTest(handler=handler):
                overlay = w.MascotOverlay.__new__(w.MascotOverlay)
                overlay.preview = w.ReminderPreview('Preview Name', 30)
                overlay.data = self.d
                overlay.win = Mock()
                overlay.dismiss_job = 'timer'
                overlay.on_snooze = Mock()
                overlay._walk_out = Mock()
                getattr(overlay, handler)()
                overlay.on_snooze.assert_not_called()
                overlay._walk_out.assert_called_once()
        self.assertEqual(self.d.count, 0)
        self.assertFalse(self.file.exists())

    def test_rollover_refreshes_dashboard_and_tray_during_snooze(self):
        yesterday = str(date.today() - timedelta(days=1))
        self.d.data.update(date=yesterday, glasses_count=8)
        app = Mock()
        app.data = self.d
        app._displayed_day = yesterday
        app.dnd_until = 1300
        app._refresh_ui_progress.side_effect = lambda: w.WatertimeApp._refresh_ui_progress(app)
        with patch.object(w.time, 'time', return_value=1000), patch.object(w, 'create_tray_icon_image') as badge:
            w.WatertimeApp._check_timer_loop(app)
            w.WatertimeApp._check_timer_loop(app)
        app._refresh_ui_progress.assert_called_once()
        app.lbl_hero_litres.config.assert_called_once_with(text='0.00 L')
        badge.assert_called_once_with(0, self.d.goal, 64)
        self.assertEqual(self.d.data['history'][yesterday], 8)
        app.trigger_reminder.assert_not_called()

    def test_rescheduling_preserves_an_active_snooze(self):
        app = Mock(data=self.d, dnd_until=1450, next_reminder_time=1450)
        self.d.set_interval(30)
        with patch.object(w.time, 'time', return_value=1000):
            w.WatertimeApp._schedule_next_reminder(app)
        self.assertEqual(app.next_reminder_time, 1450)

    def test_due_reminder_waits_for_an_open_preview(self):
        self.d.set_work_hours_enabled(False)
        self.d.set_pause_on_meeting(False)
        app = Mock(data=self.d, _displayed_day=self.d.day, dnd_until=0, next_reminder_time=990)
        app.mascot.is_active = True
        app.compact_overlay.is_active = False
        with patch.object(w.time, 'time', return_value=1000):
            w.WatertimeApp._check_timer_loop(app)
            app.trigger_reminder.assert_not_called()
            self.assertEqual(app.next_reminder_time, 990)
            app.mascot.is_active = False
            w.WatertimeApp._check_timer_loop(app)
        app.trigger_reminder.assert_called_once()
        self.assertEqual(app.next_reminder_time, 1300)

    def test_tray_default_snooze_reads_current_preference(self):
        app = Mock(data=self.d)
        with (patch.object(w, 'IS_MACOS', False),
              patch.object(w.pystray, 'Icon') as icon,
              patch.object(w.threading, 'Thread')):
            w.WatertimeApp._init_tray(app)
        menu = icon.call_args.args[3]
        snooze = next(item for item in menu.items if item.text == 'Snooze / DND').submenu.items[0]
        self.d.set_snooze_interval(25)
        self.assertEqual(snooze.text, 'Snooze 25m (Default)')
        snooze(app.tray)
        scheduled_callback = app.root.after.call_args.args[1]
        scheduled_callback()
        app.set_snooze.assert_called_once_with(25)

    def test_automatic_reminder_checks_quiet_hours_and_snooze_at_display_time(self):
        self.d.set_work_hours(9, 18)
        self.d.set_pause_on_meeting(False)
        app = Mock(data=self.d, dnd_until=0)
        for hour, snooze, should_show in ((8, 0, False), (10, 1300, False), (10, 0, True)):
            app.dnd_until = snooze
            app._show_reminder.reset_mock()
            with (patch.object(w.time, 'time', return_value=1000),
                  patch.object(w.time, 'localtime', return_value=Mock(tm_hour=hour))):
                w.WatertimeApp.trigger_reminder(app)
            self.assertEqual(app._show_reminder.call_count, int(should_show))

    def test_linux_reminder_emojis_render_without_an_emoji_font(self):
        reminders = [(subtitle, emoji) for _, subtitle, emoji in w.MASCOT_QUOTES]
        reminders.extend((('', '🎉'), ('', '🏆'), ('', '⏰'), ('', '👍')))
        font = w.ImageFont.load_default(size=12)
        with patch.object(w.sys, 'platform', 'linux'), patch.object(w, '_load_fonts', return_value=(font, None)):
            for subtitle, emoji in reminders:
                with self.subTest(emoji=emoji):
                    image = w.render_speech_bubble_image('Hydration check', subtitle, emoji)
                    icon = w._load_reminder_emoji(ord(emoji))
                    icon_colors = {color for _, color in icon.getcolors(196) if color[3] == 255}
                    rendered_colors = {color for _, color in image.crop((24, 33, 296, 53)).getcolors(5440)}
                    self.assertGreater(len(icon_colors & rendered_colors), 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
