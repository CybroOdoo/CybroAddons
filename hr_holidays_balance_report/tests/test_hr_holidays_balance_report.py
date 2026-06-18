# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests import TransactionCase, tagged
from odoo.fields import Date
from datetime import timedelta

@tagged('post_install', '-at_install')
class TestHrHolidaysBalanceReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestHrHolidaysBalanceReport, cls).setUpClass()
        
        # Create an employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        
        # Create a leave type
        cls.leave_type = cls.env['hr.leave.type'].create({
            'name': 'Test Leave Type',
            'requires_allocation': 'yes',
            'leave_validation_type': 'no_validation',
        })
        
        # Create an allocation
        cls.allocation = cls.env['hr.leave.allocation'].create({
            'name': 'Test Allocation',
            'employee_id': cls.employee.id,
            'holiday_status_id': cls.leave_type.id,
            'number_of_days': 10,
            'state': 'confirm',
        })
        cls.allocation.action_validate()

        # Create a leave
        cls.leave = cls.env['hr.leave'].create({
            'name': 'Test Leave',
            'employee_id': cls.employee.id,
            'holiday_status_id': cls.leave_type.id,
            'request_date_from': Date.today() + timedelta(days=1),
            'request_date_to': Date.today() + timedelta(days=2),
            'number_of_days': 2,
        })
        cls.leave.action_validate()
        
        cls.env.flush_all()

    def test_01_balance_leave_report(self):
        """Test the leave balance report view"""
        # Query the report view for our employee and leave type
        report = self.env['report.balance.leave'].search([
            ('emp_id', '=', self.employee.id),
            ('leave_type_id', '=', self.leave_type.id)
        ])
        
        # Check if the report has records
        self.assertTrue(report, "Report should have a record for the employee and leave type")
        
        # Check the values
        self.assertEqual(report.allocated_days, 10, "Allocated days should be 10")
        self.assertEqual(report.taken_days, 2, "Taken days should be 2")
        self.assertEqual(report.balance_days, 8, "Balance days should be 8")
