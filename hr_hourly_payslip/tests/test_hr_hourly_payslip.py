# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import datetime

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHrHourlyPayslip(TransactionCase):
    """ Tests for the hourly payslip fields and computations. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Hourly Employee',
            'hourly_cost': 10.0,
            'hourly_payslip': True,
        })
        cls.env['hr.attendance'].create([
            {
                'employee_id': cls.employee.id,
                'check_in': datetime(2026, 1, 5, 8, 0, 0),
                'check_out': datetime(2026, 1, 5, 12, 0, 0),
            },
            {
                'employee_id': cls.employee.id,
                'check_in': datetime(2026, 1, 6, 8, 0, 0),
                'check_out': datetime(2026, 1, 6, 10, 0, 0),
            },
            {
                'employee_id': cls.employee.id,
                'check_in': datetime(2026, 2, 5, 8, 0, 0),
                'check_out': datetime(2026, 2, 5, 9, 0, 0),
            },
        ])

    def _new_payslip(self, employee=None, **values):
        vals = {
            'employee_id': (employee or self.employee).id,
            'date_from': '2026-01-01',
            'date_to': '2026-01-31',
        }
        vals.update(values)
        return self.env['hr.payslip'].new(vals)

    def test_total_hours_in_period(self):
        """ Only the attendances inside the period are counted. """
        payslip = self._new_payslip()
        self.assertAlmostEqual(payslip.total_hours, 6.0, places=2)

    def test_hour_based_salary(self):
        """ Salary is the hourly cost multiplied by the worked hours. """
        payslip = self._new_payslip()
        self.assertAlmostEqual(payslip.hour_based_salary, 60.0, places=2)

    def test_show_total_hours_enabled(self):
        """ The hours are shown for hourly employees. """
        payslip = self._new_payslip()
        self.assertTrue(payslip.show_total_hours)

    def test_show_total_hours_disabled(self):
        """ The hours are hidden when the option is off. """
        self.employee.hourly_payslip = False
        payslip = self._new_payslip()
        self.assertFalse(payslip.show_total_hours)

    def test_onchange_employee(self):
        """ The onchange toggles the visibility of the hours. """
        payslip = self._new_payslip()
        payslip._onchange_employee_id()
        self.assertTrue(payslip.show_total_hours)
        self.employee.hourly_payslip = False
        payslip._onchange_employee_id()
        self.assertFalse(payslip.show_total_hours)

    def test_no_employee(self):
        """ Without employee or dates, everything is zero. """
        payslip = self.env['hr.payslip'].new({})
        self.assertEqual(payslip.total_hours, 0.0)
        self.assertEqual(payslip.hour_based_salary, 0.0)
        self.assertFalse(payslip.show_total_hours)

    def test_basic_rule_uses_hours(self):
        """ The basic salary rule is based on the worked hours. """
        rule = self.env.ref('hr_payroll_community.hr_rule_basic')
        self.assertIn('total_hours', rule.amount_python_compute)
        self.assertIn('contract.wage', rule.amount_python_compute)
