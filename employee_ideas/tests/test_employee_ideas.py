# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestEmployeeIdeas(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.department = cls.env['hr.department'].create({
            'name': 'Research',
            'company_id': cls.company.id,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'user_id': cls.env.uid,
            'department_id': cls.department.id,
            'company_id': cls.company.id,
        })
        cls.idea_type = cls.env['idea.type'].create({
            'name': 'Process Improvement',
            'minimum_vote': 2,
            'company_id': cls.company.id,
            'hr_department_ids': [(6, 0, [cls.department.id])],
        })

    def test_create_assigns_sequence(self):
        idea = self.env['employee.idea'].create({
            'title': 'Reduce wait time',
            'idea_type_id': self.idea_type.id,
            'details': 'Automate the approval step for repeated requests.',
            'employee_id': self.employee.id,
        })

        self.assertTrue(idea.reference_no)
        self.assertNotEqual(idea.reference_no, 'New')

    def test_state_actions_update_state(self):
        idea = self.env['employee.idea'].create({
            'title': 'Improve onboarding',
            'idea_type_id': self.idea_type.id,
            'details': 'Create a guided onboarding checklist.',
            'employee_id': self.employee.id,
        })

        idea.action_send_approval()
        self.assertEqual(idea.state, 'approval')

        idea.action_approve()
        self.assertEqual(idea.state, 'post')

        idea.action_reject()
        self.assertEqual(idea.state, 'rejected')

    def test_vote_wizard_and_comment_validation(self):
        idea = self.env['employee.idea'].create({
            'title': 'Shared workspace',
            'idea_type_id': self.idea_type.id,
            'details': 'Set up a shared collaboration area.',
            'employee_id': self.employee.id,
        })

        action = idea.action_give_vote()
        wizard = self.env['give.vote'].browse(action['res_id'])

        self.assertEqual(action['res_model'], 'give.vote')
        self.assertEqual(wizard.employee_ideas_id, idea)
        self.assertEqual(wizard.reference, idea.reference_no)
        self.assertEqual(wizard.employee_id, self.employee)

        with self.assertRaises(ValidationError):
            wizard.action_submit_comment()

        wizard.comments = 'Looks good'
        wizard.action_submit_comment()
        self.assertEqual(wizard.status, 'Commented')

    def test_idea_type_total_ideas(self):
        self.env['employee.idea'].create({
            'title': 'Cut manual steps',
            'idea_type_id': self.idea_type.id,
            'details': 'Remove one manual validation step.',
            'employee_id': self.employee.id,
        })

        self.idea_type._compute_total_ideas()
        self.assertEqual(self.idea_type.total_ideas, 1)
