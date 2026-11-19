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
from datetime import date

from freezegun import freeze_time

from odoo.tests import tagged

from .common import NOW, HrLeaveDashboardCommon


@tagged('post_install', '-at_install')
class TestHrLeaveReport(HrLeaveDashboardCommon):
    """PDF leave report values and rendering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.allocation = cls.env['hr.leave.allocation'].create({
            'name': 'Dashboard allocation',
            'employee_id': cls.employee_a.id,
            'work_entry_type_id': cls.work_entry_type.id,
            'number_of_days': 10,
        })
        cls.allocation.action_approve()

    def _report(self, user=None):
        return self.env['report.hr_leave_dashboard.hr_leave_report'].with_user(
            user or self.manager_user)

    def _rows(self, values, employee):
        return [r for r in values['filtered_list'] if r['emp_id'] == employee.id]

    @freeze_time(NOW)
    def test_report_periods(self):
        self._create_leave(self.employee_a, date(2026, 6, 17))    # today
        self._create_leave(self.employee_b, date(2026, 6, 19))    # this week
        self._create_leave(self.manager, date(2026, 6, 24))       # this month
        self._create_leave(self.employee_a, date(2026, 9, 14))    # this year
        expected = {
            'today': {self.employee_a},
            'this_week': {self.employee_a, self.employee_b},
            'this_month': {self.employee_a, self.employee_b, self.manager},
            'this_year': {self.employee_a, self.employee_b, self.manager},
        }
        ours = self.employee_a | self.employee_b | self.manager
        for duration, employees in expected.items():
            values = self._report()._get_report_values([], {'duration': duration})
            self.assertEqual(values['duration'], duration)
            self.assertEqual(values['doc_model'], 'hr.leave.report')
            found = {r['emp_id'] for r in values['filtered_list']} & set(ours.ids)
            self.assertEqual(found, {e.id for e in employees}, duration)

    @freeze_time(NOW)
    def test_report_default_period_and_balances(self):
        self._create_leave(self.employee_a, date(2026, 6, 17), date(2026, 6, 18))
        values = self._report()._get_report_values([])
        self.assertEqual(values['duration'], 'today')
        [row] = self._rows(values, self.employee_a)
        self.assertEqual(row['emp_name'], 'Dash Employee A')
        self.assertEqual(row['emp_department'], self.department.id)
        self.assertEqual(row['leave_type'], 'Dashboard Leave')
        self.assertEqual(row['allocated_days'], 10)
        self.assertEqual(row['taken_days'], 2)
        self.assertEqual(row['balance_days'], 8)

    @freeze_time(NOW)
    def test_report_one_row_per_employee_and_type(self):
        self._create_leave(self.employee_a, date(2026, 6, 15))
        self._create_leave(self.employee_a, date(2026, 6, 17))
        values = self._report()._get_report_values([], {'duration': 'this_week'})
        self.assertEqual(len(self._rows(values, self.employee_a)), 1)

    @freeze_time(NOW)
    def test_report_skips_leaves_without_dates(self):
        leave = self._create_leave(self.employee_a, date(2026, 6, 17))
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE hr_leave SET request_date_from = NULL WHERE id = %s", [leave.id])
        values = self._report()._get_report_values([], {'duration': 'today'})
        self.assertEqual(self._rows(values, self.employee_a), [])

    @freeze_time(NOW)
    def test_report_employee_sees_own_department(self):
        """An employee without subordinates only sees their department."""
        outsider = self.env['hr.employee'].create({
            'name': 'Other Department Employee',
            'department_id': self.env['hr.department'].create({'name': 'Other'}).id,
        })
        self._create_leave(self.employee_b, date(2026, 6, 17))
        self._create_leave(outsider, date(2026, 6, 17))
        values = self._report(self.employee_user)._get_report_values(
            [], {'duration': 'today'})
        emp_ids = {r['emp_id'] for r in values['filtered_list']}
        self.assertIn(self.employee_b.id, emp_ids)
        self.assertNotIn(outsider.id, emp_ids)

    def test_generate_date_range(self):
        self.assertEqual(
            self._report().generate_date_range(date(2026, 2, 27), date(2026, 3, 2)),
            ['2026-02-27', '2026-02-28', '2026-03-01', '2026-03-02'])
        self.assertEqual(
            self._report().generate_date_range(date(2026, 3, 2), date(2026, 3, 1)), [])

    @freeze_time(NOW)
    def test_report_renders(self):
        self._create_leave(self.employee_a, date(2026, 6, 17))
        html = self.env['ir.actions.report'].with_user(self.manager_user)._render_qweb_html(
            'hr_leave_dashboard.hr_leave_report', [], data={'duration': 'today'})[0]
        self.assertIn(b'Absentees Today', html)
        self.assertIn(b'Dash Employee A', html)
        self.assertIn(b'10.00', html)

    @freeze_time('2026-06-17 20:00:00')
    def test_report_today_in_user_timezone(self):
        """At 20:00 UTC it is already 18 June for a manager in India."""
        self.manager_user.tz = 'Asia/Kolkata'
        self._create_leave(self.employee_a, date(2026, 6, 18))
        values = self._report()._get_report_values([], {'duration': 'today'})
        self.assertEqual(len(self._rows(values, self.employee_a)), 1)
