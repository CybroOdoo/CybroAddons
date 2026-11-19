# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
from datetime import date, datetime

import pytz
from freezegun import freeze_time

from odoo.tests import tagged

from .common import NOW, HrLeaveDashboardCommon


@tagged('post_install', '-at_install')
class TestHrLeaveDashboard(HrLeaveDashboardCommon):
    """Dashboard data served by hr.leave and hr.employee."""

    def _leave_model(self, user=None, employee=None):
        """hr.leave as ``user`` (manager by default), optionally viewing
        the dashboard of ``employee`` through the context."""
        model = self.env['hr.leave'].with_user(user or self.manager_user)
        if employee:
            model = model.with_context(employee_id=employee.id)
        return model

    # ------------------------------------------------------------------
    # Current employee card
    # ------------------------------------------------------------------
    def test_current_employee(self):
        data = self._leave_model().get_current_employee()
        self.assertEqual(data['id'], self.manager.id)
        self.assertEqual(data['name'], 'Dash Manager')
        self.assertEqual(data['work_email'], 'manager@example.com')
        self.assertEqual(data['work_phone'], '+1 555 0100')
        self.assertEqual(data['department_id'], self.department.name)
        self.assertEqual(data['company'], self.company.name)
        self.assertTrue(data['image_1920'])
        self.assertIsInstance(data['image_1920'], str)
        self.assertEqual(data['manager'], {})
        self.assertEqual(data['manager_all_count'], 0)
        self.assertEqual(sorted(data['child_ids']),
                         sorted((self.employee_a | self.employee_b).ids))
        self.assertEqual({c['id'] for c in data['children']},
                         {self.employee_a.id, self.employee_b.id})
        child = next(c for c in data['children'] if c['id'] == self.employee_a.id)
        self.assertEqual(child['approval_status_count'],
                         {'validate_count': 0, 'confirm_count': 0, 'refuse_count': 0})

    def test_current_employee_from_context(self):
        """The dashboard can show another employee via ``employee_id``."""
        self.employee_a.image_1920 = False
        data = self._leave_model(employee=self.employee_a).get_current_employee()
        self.assertEqual(data['id'], self.employee_a.id)
        self.assertFalse(data['image_1920'])
        self.assertEqual(data['manager']['id'], self.manager.id)
        self.assertEqual(data['manager_all_count'], 1)
        self.assertEqual(data['children'], [])

    def test_current_employee_without_employee(self):
        self.assertEqual(
            self._leave_model(self.no_employee_user).get_current_employee(), {})

    def test_prepare_employee_data_empty(self):
        self.assertEqual(
            self.env['hr.leave']._prepare_employee_data(self.env['hr.employee']), {})

    # ------------------------------------------------------------------
    # On leave today
    # ------------------------------------------------------------------
    @freeze_time(NOW)
    def test_absentees_today(self):
        self._create_leave(self.employee_a, date(2026, 6, 17))
        self._create_leave(self.employee_b, date(2026, 6, 18))
        absentees = self._leave_model().get_absentees()
        self.assertEqual([a['employee_id'] for a in absentees], [self.employee_a.id])
        self.assertEqual(absentees[0]['name'], 'Dash Employee A')

    @freeze_time('2026-06-17 03:00:00')
    def test_absentees_leave_starting_later_today(self):
        """A leave starting later today already counts as on leave today."""
        leave = self._create_leave(self.employee_a, date(2026, 6, 17))
        self.assertGreater(leave.date_from, datetime(2026, 6, 17, 3, 0))
        absentees = self._leave_model().get_absentees()
        self.assertEqual([a['employee_id'] for a in absentees], [self.employee_a.id])

    @freeze_time(NOW)
    def test_absentees_without_team(self):
        self._create_leave(self.employee_a, date(2026, 6, 17))
        self.assertEqual(
            self._leave_model(employee=self.employee_a).get_absentees(), [])
        self.assertEqual(
            self._leave_model(self.no_employee_user).get_absentees(), [])

    # ------------------------------------------------------------------
    # Timezones and periods
    # ------------------------------------------------------------------
    def test_safe_tz(self):
        Leave = self.env['hr.leave']
        self.assertEqual(Leave._safe_tz('Asia/Kolkata').zone, 'Asia/Kolkata')
        self.assertEqual(Leave._safe_tz(False), pytz.utc)
        self.assertEqual(Leave._safe_tz('Mars/Olympus_Mons'), pytz.utc)

    def test_dashboard_tz(self):
        Leave = self.env['hr.leave'].with_user(self.manager_user)
        self.employee_a.tz = 'Asia/Kolkata'
        self.assertEqual(Leave._dashboard_tz(self.employee_a).zone, 'Asia/Kolkata')
        self.manager_user.tz = 'Europe/Brussels'
        self.assertEqual(
            Leave._dashboard_tz(self.env['hr.employee']).zone, 'Europe/Brussels')

    @freeze_time(NOW)
    def test_period_domain(self):
        Leave = self._leave_model()
        self.assertEqual(Leave._period_domain(False), [])
        self.assertEqual(Leave._period_domain('all'), [])
        expected = {
            'today': (date(2026, 6, 17), date(2026, 6, 17)),
            'this_week': (date(2026, 6, 15), date(2026, 6, 21)),
            'this_month': (date(2026, 6, 1), date(2026, 6, 30)),
            'this_year': (date(2026, 1, 1), date(2026, 12, 31)),
        }
        for period, (start, end) in expected.items():
            self.assertEqual(
                Leave._period_domain(period),
                [('request_date_from', '<=', end), ('request_date_to', '>=', start)],
                period)

    @freeze_time('2026-06-17 20:00:00')
    def test_period_domain_uses_viewer_timezone(self):
        """20:00 UTC is already 18 June in India."""
        self.manager.tz = 'Asia/Kolkata'
        domain = self._leave_model(employee=self.manager)._period_domain('today')
        self.assertEqual(domain[0][2], date(2026, 6, 18))

    # ------------------------------------------------------------------
    # Approval status counts
    # ------------------------------------------------------------------
    @freeze_time(NOW)
    def test_approval_status_counts_by_period(self):
        self._create_leave(self.employee_a, date(2026, 6, 17))            # today
        self._create_leave(self.employee_a, date(2026, 6, 19), state='confirm')  # this week
        self._create_leave(self.employee_a, date(2026, 6, 24), state='refuse')   # this month
        self._create_leave(self.employee_a, date(2026, 9, 14))            # this year
        self._create_leave(self.employee_a, date(2027, 1, 11))            # next year
        Leave = self._leave_model()
        expected = {
            'today': (1, 0, 0),
            'this_week': (1, 1, 0),
            'this_month': (1, 1, 1),
            'this_year': (2, 1, 1),
            False: (3, 1, 1),
        }
        for period, (validate, confirm, refuse) in expected.items():
            self.assertEqual(
                Leave.get_approval_status_count(self.employee_a.id, period),
                {'validate_count': validate, 'confirm_count': confirm,
                 'refuse_count': refuse}, period)

    def test_approval_status_count_without_employee(self):
        self.assertEqual(
            self.env['hr.leave'].get_approval_status_count(False),
            {'validate_count': 0, 'confirm_count': 0, 'refuse_count': 0})

    @freeze_time(NOW)
    def test_team_approval_status_counts(self):
        self._create_leave(self.employee_a, date(2026, 6, 17))
        self._create_leave(self.employee_b, date(2026, 6, 24))
        Leave = self._leave_model()
        counts = Leave.get_team_approval_status_counts(
            [self.employee_a.id, self.employee_b.id], 'this_week')
        self.assertEqual(counts[self.employee_a.id]['validate_count'], 1)
        self.assertEqual(counts[self.employee_b.id]['validate_count'], 0)
        self.assertEqual(Leave.get_team_approval_status_counts(None), {})

    # ------------------------------------------------------------------
    # Current shift
    # ------------------------------------------------------------------
    def _set_fixed_calendar(self, employee):
        """Give ``employee`` a fixed-hours schedule: Wednesday 08-12 and
        13-17, plus a one-off Saturday 20 June 09-12 attendance."""
        calendar = self.env['resource.calendar'].create({
            'name': 'Dashboard Fixed Hours',
            'attendance_ids': [
                (0, 0, {'dayofweek': '2', 'hour_from': 8, 'hour_to': 12}),
                (0, 0, {'dayofweek': '2', 'hour_from': 13, 'hour_to': 17}),
            ],
        })
        self.assertFalse(any(calendar.attendance_ids.mapped('duration_based')))
        employee.resource_calendar_id = calendar
        return calendar

    def _set_variable_calendar(self, employee):
        """Give ``employee`` a variable schedule with a single dated
        attendance: Saturday 20 June 2026, 09-12."""
        calendar = self.env['resource.calendar'].create({
            'name': 'Dashboard Variable',
            'calendar_type': 'variable',
            'attendance_ids': [
                (0, 0, {'date': date(2026, 6, 20), 'hour_from': 9, 'hour_to': 12}),
            ],
        })
        self.assertEqual(len(calendar.attendance_ids), 1)
        employee.resource_calendar_id = calendar
        return calendar

    @freeze_time(NOW)
    def test_current_shift_fixed_hours(self):
        self._set_fixed_calendar(self.manager)
        self.assertEqual(self._leave_model().get_current_shift(), 'Morning')

    @freeze_time('2026-06-17 14:00:00')
    def test_current_shift_afternoon(self):
        self._set_fixed_calendar(self.manager)
        self.assertEqual(self._leave_model().get_current_shift(), 'Afternoon')

    @freeze_time('2026-06-17 04:30:00')
    def test_current_shift_uses_employee_timezone(self):
        """04:30 UTC is 10:00 in India, inside the Wednesday morning shift."""
        self._set_fixed_calendar(self.manager)
        self.manager.tz = 'Asia/Kolkata'
        self.assertEqual(self._leave_model().get_current_shift(), 'Morning')

    @freeze_time('2026-06-17 12:30:00')
    def test_current_shift_lunch_break(self):
        self._set_fixed_calendar(self.manager)
        self.assertFalse(self._leave_model().get_current_shift())

    @freeze_time('2026-06-20 10:00:00')
    def test_current_shift_one_off_date(self):
        """A dated attendance only applies on its own date (a Saturday).
        It is the schedule's only attendance, so core labels it Full Day."""
        calendar = self._set_variable_calendar(self.manager)
        self.assertEqual(calendar.attendance_ids.day_period, 'full_day')
        self.assertEqual(self._leave_model().get_current_shift(), 'Full Day')

    @freeze_time('2026-06-27 10:00:00')
    def test_current_shift_not_on_other_dates(self):
        self._set_variable_calendar(self.manager)
        self.assertFalse(self._leave_model().get_current_shift())

    @freeze_time(NOW)
    def test_current_shift_duration_based(self):
        """The default schedule is duration based (8 hours a day, no fixed
        time): Odoo places the 8 hours around 12:00, i.e. 08:00-16:00."""
        attendances = self.manager.resource_calendar_id.attendance_ids
        self.assertTrue(all(attendances.mapped('duration_based')))
        self.assertEqual(self._leave_model().get_current_shift(), 'Full Day')

    @freeze_time('2026-06-17 17:00:00')
    def test_current_shift_duration_based_evening(self):
        self.assertFalse(self._leave_model().get_current_shift())

    @freeze_time('2026-06-20 10:00:00')
    def test_current_shift_duration_based_weekend(self):
        self.assertFalse(self._leave_model().get_current_shift())

    def test_current_shift_without_employee(self):
        self.assertFalse(self._leave_model(self.no_employee_user).get_current_shift())

    # ------------------------------------------------------------------
    # Upcoming holidays and public holidays on the calendar
    # ------------------------------------------------------------------
    @freeze_time(NOW)
    def test_upcoming_holidays(self):
        past = self._create_public_holiday(
            'Past Holiday', datetime(2026, 6, 1), datetime(2026, 6, 1, 23, 59))
        upcoming = self._create_public_holiday(
            'Upcoming Holiday', datetime(2026, 7, 6), datetime(2026, 7, 7, 23, 59))
        holidays = self._leave_model().get_upcoming_holidays()
        ids = [h['id'] for h in holidays]
        self.assertIn(upcoming.id, ids)
        self.assertNotIn(past.id, ids)
        row = next(h for h in holidays if h['id'] == upcoming.id)
        self.assertEqual(row, {'id': upcoming.id, 'name': 'Upcoming Holiday',
                               'date_from': '2026-07-06', 'date_to': '2026-07-07'})

    @freeze_time(NOW)
    def test_upcoming_holidays_local_dates(self):
        """A holiday starting at midnight in India is stored the day before
        in UTC, but must be shown on its local date."""
        self.company.tz = 'Asia/Kolkata'
        holiday = self._create_public_holiday(
            'Local Holiday', datetime(2026, 12, 24, 18, 30), datetime(2026, 12, 25, 18, 29))
        rows = self._leave_model(self.no_employee_user).get_upcoming_holidays()
        row = next(h for h in rows if h['id'] == holiday.id)
        self.assertEqual((row['date_from'], row['date_to']), ('2026-12-25', '2026-12-25'))

    def test_public_holidays_calendar(self):
        self.manager.tz = 'Asia/Kolkata'
        self._create_public_holiday(
            'Two Day Holiday', datetime(2026, 12, 24, 18, 30), datetime(2026, 12, 26, 18, 29))
        days = self.manager.get_public_holidays(
            datetime(2026, 12, 1), datetime(2026, 12, 31, 23, 59))
        self.assertTrue(days.get('2026-12-25'))
        self.assertTrue(days.get('2026-12-26'))
        self.assertNotIn('2026-12-24', days)

    def test_public_holidays_calendar_other_schedule(self):
        """Holidays of another working schedule are not shown."""
        other_calendar = self.env['resource.calendar'].create({'name': 'Other'})
        holiday = self._create_public_holiday(
            'Other Schedule Holiday', datetime(2026, 11, 2), datetime(2026, 11, 2, 23, 59))
        holiday.calendar_id = other_calendar
        days = self.env['hr.employee'].with_user(self.manager_user).get_public_holidays(
            datetime(2026, 11, 1), datetime(2026, 11, 30, 23, 59))
        self.assertNotIn('2026-11-02', days)

    # ------------------------------------------------------------------
    # Validated leaves (fed to the PDF report)
    # ------------------------------------------------------------------
    def test_all_validated_leaves(self):
        validated = self._create_leave(self.employee_a, date(2026, 6, 17))
        refused = self._create_leave(self.employee_b, date(2026, 6, 17), state='refuse')
        rows = self._leave_model().get_all_validated_leaves()
        ids = [r['id'] for r in rows]
        self.assertIn(validated.id, ids)
        self.assertNotIn(refused.id, ids)
        row = next(r for r in rows if r['id'] == validated.id)
        self.assertEqual(row['employee_id'], self.employee_a.id)
        self.assertEqual(row['leave_type_id'], self.work_entry_type.id)
        self.assertEqual(row['number_of_days'], 1)
