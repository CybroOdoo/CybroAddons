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

from odoo.tests.common import TransactionCase



class TestHrEmployee(TransactionCase):
    """Test cases for hr.employee discipline count computation"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.department = cls.env['hr.department'].create({
            'name': 'HR Department',
        })

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Employee Test',
            'department_id': cls.department.id,
        })

        cls.reason = cls.env['discipline.category'].create({
            'code': 'DISC03',
            'name': 'Violation',
            'category_type': 'disciplinary',
        })

        cls.action_category = cls.env['discipline.category'].create({
            'code': 'ACT02',
            'name': 'Suspension',
            'category_type': 'action',
        })

        # Create the action in draft first, then move it to 'action' state
        # via action_function() so the ORM sequence is respected.
        cls.disciplinary_action = cls.env['disciplinary.action'].create([{
            'employee_id': cls.employee.id,
            'department_id': cls.department.id,
            'discipline_reason_id': cls.reason.id,
            'action_id': cls.action_category.id,
            'action_details': 'Suspended for violation',
        }])
        # Move through states the proper way to reach 'action'
        cls.disciplinary_action.assign_function()  # draft -> explain
        cls.disciplinary_action.explanation = 'Explained'
        cls.disciplinary_action.explanation_function()  # explain -> submitted
        cls.disciplinary_action.action_function()  # submitted -> action


    def test_compute_discipline_count(self):
        """Validated (state='action') disciplinary records are counted"""

        self.employee._compute_discipline_count()

        self.assertEqual(
            self.employee.discipline_count, 1,
            "discipline_count should be 1 for one validated action",
        )


    def test_compute_discipline_count_zero(self):
        """Employee with no validated actions has a count of zero"""

        other_employee = self.env['hr.employee'].create({
            'name': 'No Action Employee',
            'department_id': self.department.id,
        })
        other_employee._compute_discipline_count()

        self.assertEqual(
            other_employee.discipline_count, 0,
            "discipline_count should be 0 when no validated actions exist",
        )


    def test_compute_discipline_count_excludes_non_action_states(self):
        """Only records in state='action' are included in the count"""

        employee2 = self.env['hr.employee'].create({
            'name': 'Draft Action Employee',
            'department_id': self.department.id,
        })
        # Create a disciplinary action that stays in 'draft' (not validated)
        self.env['disciplinary.action'].create([{
            'employee_id': employee2.id,
            'department_id': self.department.id,
            'discipline_reason_id': self.reason.id,
        }])

        employee2._compute_discipline_count()

        self.assertEqual(
            employee2.discipline_count, 0,
            "draft/explain/submitted actions must not be counted",
        )


