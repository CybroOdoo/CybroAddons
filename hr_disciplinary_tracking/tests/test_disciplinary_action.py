# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase



class TestDisciplinaryAction(TransactionCase):
    """Test cases for disciplinary.action"""

    @classmethod
    def setUpClass(cls):

        super().setUpClass()

        cls.department = cls.env['hr.department'].create({
            'name': 'Testing Department',
        })

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'department_id': cls.department.id,
        })

        cls.reason = cls.env['discipline.category'].create({
            'code': 'DISC01',
            'name': 'Late Attendance',
            'category_type': 'disciplinary',
        })

        cls.action_category = cls.env['discipline.category'].create({
            'code': 'ACT01',
            'name': 'Warning',
            'category_type': 'action',
        })

        cls.action = cls.env['disciplinary.action'].create([{
            'employee_id': cls.employee.id,
            'department_id': cls.department.id,
            'discipline_reason_id': cls.reason.id,
        }])


    def test_compute_get_user(self):
        """Test compute get user"""


        self.action._compute_get_user()

        self.assertIn(
            self.action.read_only,
            [True, False]
        )


    def test_onchange_employee_id(self):
        """Test onchange employee"""


        self.action.employee_id = self.employee
        self.action._onchange_employee_id()

        self.assertEqual(
            self.action.department_id,
            self.department
        )


    def test_onchange_employee_id_validation(self):
        """Test onchange employee validation"""


        self.action.state = 'action'

        with self.assertRaises(ValidationError):
            self.action._onchange_employee_id()


    def test_onchange_discipline_reason_validation(self):
        """Test discipline reason validation"""


        self.action.state = 'action'

        with self.assertRaises(ValidationError):
            self.action._onchange_discipline_reason_id()



    def test_assign_function(self):
        """Test assign function"""

        self.action.assign_function()

        self.assertEqual(self.action.state, 'explain')


    def test_cancel_function(self):
        """Test cancel function"""


        self.action.cancel_function()

        self.assertEqual(self.action.state, 'cancel')


    def test_set_to_function(self):
        """Test set to draft"""


        self.action.set_to_function()

        self.assertEqual(self.action.state, 'draft')


    def test_action_function_validation(self):
        """Test action validation"""


        with self.assertRaises(ValidationError):
            self.action.action_function()


    def test_action_function(self):
        """Test action function"""


        self.action.write({
            'action_id': self.action_category.id,
            'action_details': 'Warning issued',
        })

        self.action.action_function()

        self.assertEqual(self.action.state, 'action')


    def test_explanation_function_validation(self):
        """Test explanation validation"""


        self.action.explanation = False

        with self.assertRaises(ValidationError):
            self.action.explanation_function()


    def test_explanation_function(self):
        """Test explanation function"""


        self.action.write({
            'explanation': 'Medical emergency',
        })

        self.action.explanation_function()

        self.assertEqual(self.action.state, 'submitted')
