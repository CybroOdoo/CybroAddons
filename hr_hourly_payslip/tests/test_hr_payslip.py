# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import common
from odoo import fields
from datetime import datetime


class TestHrPayslip(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestHrPayslip, cls).setUpClass()

        cls.employee_hourly = cls.env['hr.employee'].create({
            'name': 'Hourly Employee',
            'hourly_payslip': True,
            'hourly_cost': 50.0,
        })
        cls.employee_salaried = cls.env['hr.employee'].create({
            'name': 'Salaried Employee',
            'hourly_payslip': False,
            'hourly_cost': 0.0,
        })

        cls.date_from = fields.Date.to_date('2026-06-01')
        cls.date_to = fields.Date.to_date('2026-06-30')

        cls.attendance_1 = cls.env['hr.attendance'].create({
            'employee_id': cls.employee_hourly.id,
            'check_in': datetime(2026, 6, 5, 8, 0, 0),
            'check_out': datetime(2026, 6, 5, 16, 0, 0),  # 8 hours
        })
        cls.attendance_2 = cls.env['hr.attendance'].create({
            'employee_id': cls.employee_hourly.id,
            'check_in': datetime(2026, 6, 12, 9, 0, 0),
            'check_out': datetime(2026, 6, 12, 17, 0, 0),  # 8 hours
        })
        cls.attendance_outside = cls.env['hr.attendance'].create({
            'employee_id': cls.employee_hourly.id,
            'check_in': datetime(2026, 7, 5, 8, 0, 0),
            'check_out': datetime(2026, 7, 5, 16, 0, 0),  # Outside the June date range
        })

    def test_onchange_employee_id(self):
        """Test that show_total_hours is set to True when employee_id has hourly_payslip set to True."""
        payslip_1 = self.env['hr.payslip'].new({
            'employee_id': self.employee_hourly.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        })
        payslip_1._onchange_employee_id()
        self.assertTrue(
            payslip_1.show_total_hours,
            "show_total_hours should be True for hourly employee"
        )

        payslip_2 = self.env['hr.payslip'].new({
            'employee_id': self.employee_salaried.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        })
        payslip_2._onchange_employee_id()
        self.assertFalse(
            payslip_2.show_total_hours,
            "show_total_hours should remain False for salaried employee"
        )

    def test_compute_total_hours_and_salary(self):
        """Test that total worked hours and hour based salary are calculated correctly."""
        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee_hourly.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        })

        self.assertEqual(self.attendance_1.worked_hours, 7.0)
        self.assertEqual(self.attendance_2.worked_hours, 7.0)

        payslip._compute_total_hours()
        self.assertEqual(
            payslip.total_hours, 14.0,
            "Total hours should be 14.0 (sum of attendance_1 and attendance_2)"
        )

        payslip._compute_hour_based_salary()
        self.assertEqual(
            payslip.hour_based_salary, 700.0,
            "Hour based salary should be 50.0 * 14 = 700.0"
        )
