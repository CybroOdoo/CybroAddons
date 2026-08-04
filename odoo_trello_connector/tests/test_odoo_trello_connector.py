# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOdooTrelloConnector(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.project = cls.env['project.project'].create({
            'name': 'Test Project',
            'trello_reference': 'BOARD001',
        })

        cls.task = cls.env['project.task'].create({
            'name': 'Test Task',
            'project_id': cls.project.id,
            'trello_reference': 'CARD001',
            'stage_reference': 'LIST001',
        })

    # ---------------------------------------------------------
    # Project Fields
    # ---------------------------------------------------------

    def test_project_trello_reference(self):
        self.assertEqual(
            self.project.trello_reference,
            'BOARD001'
        )

    # ---------------------------------------------------------
    # Task Fields
    # ---------------------------------------------------------

    def test_task_trello_reference(self):
        self.assertEqual(
            self.task.trello_reference,
            'CARD001'
        )

    def test_task_stage_reference(self):
        self.assertEqual(
            self.task.stage_reference,
            'LIST001'
        )

    # ---------------------------------------------------------
    # User Trello Fields
    # ---------------------------------------------------------

    def test_user_trello_credentials(self):
        user = self.env['res.users'].create({
            'name': 'Trello User',
            'login': 'trello_user_test',
            'api_key': 'API123',
            'token': 'TOKEN123',
            'user_name': 'trello_demo',
        })

        self.assertEqual(user.api_key, 'API123')
        self.assertEqual(user.token, 'TOKEN123')
        self.assertEqual(user.user_name, 'trello_demo')

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_action_import_without_credentials(self):
        user = self.env['res.users'].create({
            'name': 'Import User',
            'login': 'import_user_test',
        })

        with self.assertRaises(ValidationError):
            user.action_import()

    # ---------------------------------------------------------
    # SQL Constraints
    # ---------------------------------------------------------

    def test_unique_api_key_constraint(self):
        self.env['res.users'].create({
            'name': 'User One',
            'login': 'user_one_test',
            'api_key': 'UNIQUE_API_KEY',
        })

        with self.assertRaises(Exception):
            self.env['res.users'].create({
                'name': 'User Two',
                'login': 'user_two_test',
                'api_key': 'UNIQUE_API_KEY',
            })

    def test_unique_username_constraint(self):
        self.env['res.users'].create({
            'name': 'User Three',
            'login': 'user_three_test',
            'user_name': 'trello_unique',
        })

        with self.assertRaises(Exception):
            self.env['res.users'].create({
                'name': 'User Four',
                'login': 'user_four_test',
                'user_name': 'trello_unique',
            })