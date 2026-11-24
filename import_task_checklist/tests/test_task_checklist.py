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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTaskChecklist(TransactionCase):
    """Unit tests for task.checklist model extension in import_task_checklist."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TaskChecklist = cls.env['task.checklist']
        cls.company = cls.env.company

    def test_task_checklist_company_id_default(self):
        """Test default value and assignment of company_id field on task.checklist."""
        checklist = self.TaskChecklist.create({
            'name': 'Company Default Checklist',
            'description': 'Testing company_id default',
        })
        self.assertEqual(
            checklist.company_id,
            self.company,
            "company_id on task.checklist should default to the active company"
        )

    def test_task_checklist_create(self):
        """Test creating task.checklist with explicit company."""
        other_company = self.env['res.company'].create({'name': 'Second Test Company'})
        checklist = self.TaskChecklist.create({
            'name': 'Multi-Company Checklist',
            'description': 'Testing explicit company assignment',
            'company_id': other_company.id,
        })
        self.assertEqual(checklist.company_id, other_company)
