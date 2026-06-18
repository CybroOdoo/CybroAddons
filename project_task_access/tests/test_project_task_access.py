# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo.tests.common import TransactionCase


class TestProjectTaskAccess(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Users = cls.env['res.users'].with_context(
            no_reset_password=True
        )

        # Create User
        cls.user_employee = Users.create({
            'name': 'Employee User',
            'login': 'employee_user',
            'email': 'employee@example.com',
        })

        # Create Project
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project',
        })

        # Create Task
        cls.task = cls.env['project.task'].create({
            'name': 'Test Task',
            'project_id': cls.project.id,
        })

    def test_project_created(self):
        self.assertTrue(self.project)

    def test_task_created(self):
        self.assertTrue(self.task)