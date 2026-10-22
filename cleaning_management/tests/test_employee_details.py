# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Safa KB(odoo@cybrosys.com)
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
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEmployeeDetails(TransactionCase):
    """Test cases for employee.details model."""

    def setUp(self):
        super().setUp()
        self.EmployeeDetails = self.env['employee.details']
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        self.shift = self.env['cleaning.shift'].create({
            'shift_type': 'Morning Shift',
            'shift_time_from': 8.0,
            'shift_time_to': 16.0,
        })

    def test_create_employee_details(self):
        """Test creating employee details record."""
        emp_detail = self.EmployeeDetails.create({
            'employee_name_id': self.employee.id,
            'time_shift_id': self.shift.id,
        })
        self.assertEqual(emp_detail.employee_name_id, self.employee)
        self.assertEqual(emp_detail.time_shift_id, self.shift)

    def test_employee_details_rec_name(self):
        """Test rec_name returns employee name."""
        emp_detail = self.EmployeeDetails.create({
            'employee_name_id': self.employee.id,
            'time_shift_id': self.shift.id,
        })
        self.assertEqual(emp_detail.display_name, 'Test Employee')

    def test_employee_details_required(self):
        """Test required fields."""
        with self.assertRaises(Exception):
            self.EmployeeDetails.create({'employee_name_id': self.employee.id})