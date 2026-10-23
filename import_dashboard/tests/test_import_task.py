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
#############################################################################
import base64
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestImportTask(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'project.task' not in self.env or 'project.project' not in self.env:
            self.skipTest("Project app is not installed")
        self.Wizard = self.env['import.task']
        self.Project = self.env['project.project'].create({'name': 'Task Test Project'})

    def test_action_import_task_csv(self):
        """Test importing task from CSV"""
        csv_content = (
            "Project,Title,Deadline\n"
            "Task Test Project,Implement Feature X,2026-10-15"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        })
        wizard.action_import_task()

        task = self.env['project.task'].search([('name', '=', 'Implement Feature X')])
        self.assertTrue(task, "Task should be created")
        self.assertEqual(task.project_id, self.Project)
