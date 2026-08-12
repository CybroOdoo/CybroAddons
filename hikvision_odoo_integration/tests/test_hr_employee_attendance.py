# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from datetime import datetime, date
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHrEmployeeAttendance(TransactionCase):
    """Test suite for hr.employee and hr.attendance Hikvision extensions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Employee Test Sync',
            'hikvision_number': '5001',
        })
        cls.today = date.today()

    def test_hr_attendance_hik_worked_hours(self):
        """Test worked hours computation on hr.attendance."""
        check_in = datetime.combine(self.today, datetime.min.time()).replace(hour=8, minute=0)
        check_out = datetime.combine(self.today, datetime.min.time()).replace(hour=16, minute=30)
        att = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': check_in,
            'check_out': check_out,
        })
        self.assertEqual(att.hik_worked_hours, 8.5)

    def test_hr_attendance_open_checkin_worked_hours(self):
        """Test worked hours computation when check_out is missing."""
        check_in = datetime.combine(self.today, datetime.min.time()).replace(hour=8, minute=0)
        att = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': check_in,
        })
        self.assertEqual(att.hik_worked_hours, 0.0)

    def test_employee_daily_attendance_and_hours(self):
        """Test employee daily attendance computed fields for selected date."""
        check_in1 = datetime.combine(self.today, datetime.min.time()).replace(hour=8, minute=0)
        check_out1 = datetime.combine(self.today, datetime.min.time()).replace(hour=12, minute=0) # 4 hours
        check_in2 = datetime.combine(self.today, datetime.min.time()).replace(hour=13, minute=0)
        check_out2 = datetime.combine(self.today, datetime.min.time()).replace(hour=17, minute=0) # 4 hours

        att1 = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': check_in1,
            'check_out': check_out1,
        })
        att2 = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': check_in2,
            'check_out': check_out2,
        })

        self.employee.attendance_date = self.today
        self.employee._compute_daily_attendance_ids()
        self.assertEqual(set(self.employee.daily_attendance_ids.ids), {att1.id, att2.id})

        self.employee._compute_total_attendance_hours()
        self.assertEqual(self.employee.total_attendance_hours, 8.0)

    def test_employee_pending_approval_count(self):
        """Test employee pending approval request count."""
        self.env['attendance.approval'].create({
            'employee_id': self.employee.id,
            'date': self.today,
            'reason': 'Forgot card',
            'state': 'submitted',
        })
        self.env['attendance.approval'].create({
            'employee_id': self.employee.id,
            'date': self.today,
            'reason': 'Sick morning',
            'state': 'draft',
        })

        self.employee._compute_pending_approval_count()
        self.assertEqual(self.employee.pending_approval_count, 1)
