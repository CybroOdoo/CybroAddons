# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields


class TestFreeResourceWizard(TransactionCase):

    def setUp(self):
        """Prepare the test environment before each test case."""
        super().setUp()

    @classmethod
    def setUpClass(cls):
        """Create common test records used across all test cases."""
        super(TestFreeResourceWizard, cls).setUpClass()

        project_vals = {
            'name': 'Test Project',
            'privacy_visibility': 'employees',
        }
        if 'billing_type' in cls.env['project.project']._fields:
            project_vals['billing_type'] = 'not_billable'
        cls.project = cls.env['project.project'].create(project_vals)

        cls.user_1 = cls.env['res.users'].create({
            'name': 'Resource One',
            'login': 'res_one',
            'email': 'res1@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        cls.user_2 = cls.env['res.users'].create({
            'name': 'Resource Two',
            'login': 'res_two',
            'email': 'res2@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_wizard_date_validation(self):
        """Test that date_to must be after date_from."""
        with self.assertRaises(ValidationError):
            self.env['free.resource'].create({
                'date_from': fields.Date.to_date('2026-06-10'),
                'date_to': fields.Date.to_date('2026-06-05'),
            })

        # Equal dates are also not allowed as date_to <= date_from is checked
        with self.assertRaises(ValidationError):
            self.env['free.resource'].create({
                'date_from': fields.Date.to_date('2026-06-10'),
                'date_to': fields.Date.to_date('2026-06-10'),
            })

    def test_get_free_resource_filtering(self):
        """Test that get_free_resource action domain correctly excludes busy resources and includes free ones."""
        # Create a task assigning user_1 for June 10th to June 20th
        self.env['project.task'].create({
            'name': 'Task A',
            'project_id': self.project.id,
            'task_start_date': fields.Date.to_date('2026-06-10'),
            'date_deadline': fields.Date.to_date('2026-06-20'),
            'user_ids': [(6, 0, [self.user_1.id])],
        })

        # Scenario 1: Wizard for June 12th to June 15th (User 1 is busy)
        wizard_busy = self.env['free.resource'].create({
            'date_from': fields.Date.to_date('2026-06-12'),
            'date_to': fields.Date.to_date('2026-06-15'),
        })
        action_busy = wizard_busy.get_free_resource()
        users_busy = self.env['res.users'].search(action_busy['domain'])
        self.assertNotIn(self.user_1, users_busy)
        self.assertIn(self.user_2, users_busy)

        # Scenario 2: Wizard for June 21st to June 25th (User 1 is free)
        wizard_free = self.env['free.resource'].create({
            'date_from': fields.Date.to_date('2026-06-21'),
            'date_to': fields.Date.to_date('2026-06-25'),
        })
        action_free = wizard_free.get_free_resource()
        users_free = self.env['res.users'].search(action_free['domain'])
        self.assertIn(self.user_1, users_free)
        self.assertIn(self.user_2, users_free)
