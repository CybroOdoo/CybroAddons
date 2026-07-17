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


class TestHrEmployee(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestHrEmployee, cls).setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Hourly Test Employee',
        })

    def test_onchange_hourly_payslip(self):
        """Test that enabling hourly_payslip modifies the basic salary rule compute expression."""
        basic_rule = self.env.ref('hr_payroll_community.hr_rule_basic')

        self.employee.hourly_payslip = True
        self.employee._onchange_hourly_payslip()

        self.assertEqual(
            basic_rule.amount_python_compute,
            'result = employee.hourly_cost*payslip.total_hours',
            "The basic salary rule compute expression was not updated correctly."
        )
