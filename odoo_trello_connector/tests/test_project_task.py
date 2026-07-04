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


class TestProjectTask(TransactionCase):
    """Test cases for project.task trello fields"""

    def setUp(self):
        super().setUp()
        self.project = self.env['project.project'].create({
            'name': 'Test Project For Tasks',
        })
        self.task = self.env['project.task'].create({
            'name': 'Test Trello Task',
            'project_id': self.project.id,
        })

    def test_01_trello_reference_field_exists(self):
        """Test that trello_reference field exists on project.task"""
        self.assertIn('trello_reference', self.env['project.task']._fields)

    def test_02_stage_reference_field_exists(self):
        """Test that stage_reference field exists on project.task"""
        self.assertIn('stage_reference', self.env['project.task']._fields)

    def test_03_create_task_with_trello_reference(self):
        """Test creating a task with a trello_reference value"""
        task = self.env['project.task'].create({
            'name': 'Task With Trello Ref',
            'project_id': self.project.id,
            'trello_reference': 'cardid_abc123',
        })
        self.assertEqual(task.trello_reference, 'cardid_abc123')

    def test_04_create_task_with_stage_reference(self):
        """Test creating a task with stage_reference value"""
        task = self.env['project.task'].create({
            'name': 'Task With Stage Ref',
            'project_id': self.project.id,
            'stage_reference': 'listid_xyz789',
        })
        self.assertEqual(task.stage_reference, 'listid_xyz789')

    def test_05_update_trello_fields(self):
        """Test updating both trello fields"""
        self.assertFalse(self.task.trello_reference)
        self.assertFalse(self.task.stage_reference)
        self.task.write({
            'trello_reference': 'card_upd123',
            'stage_reference': 'list_upd456',
        })
        self.assertEqual(self.task.trello_reference, 'card_upd123')
        self.assertEqual(self.task.stage_reference, 'list_upd456')

    def test_06_trello_fields_default_empty(self):
        """Test that both trello fields default to empty"""
        task = self.env['project.task'].create({
            'name': 'No Ref Task',
            'project_id': self.project.id,
        })
        self.assertFalse(task.trello_reference)
        self.assertFalse(task.stage_reference)
