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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import datetime
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProjectTaskChecklist(TransactionCase):
    """Test suite covering checklist templates, task lines, and progress calculation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({
            'name': 'Test Checklist Project',
        })
        cls.checklist = cls.env['task.checklist'].create({
            'name': 'Deployment Checklist',
            'description': 'Standard deployment procedures',
        })
        cls.item_1 = cls.env['checklist.item'].create({
            'name': 'Code Review',
            'sequence': 1,
            'description': 'Perform peer code review',
            'checklist_id': cls.checklist.id,
        })
        cls.item_2 = cls.env['checklist.item'].create({
            'name': 'Run Unit Tests',
            'sequence': 2,
            'description': 'Ensure all unit tests pass',
            'checklist_id': cls.checklist.id,
        })
        cls.item_3 = cls.env['checklist.item'].create({
            'name': 'Deploy to Server',
            'sequence': 3,
            'description': 'Execute deployment script',
            'checklist_id': cls.checklist.id,
        })

    def test_01_checklist_template_creation(self):
        """Verify that checklist template and items are created correctly."""
        self.assertEqual(self.checklist.name, 'Deployment Checklist')
        self.assertEqual(len(self.checklist.checklist_ids), 3)
        self.assertEqual(self.checklist.checklist_ids.mapped('name'), [
            'Code Review', 'Run Unit Tests', 'Deploy to Server'
        ])

    def test_02_task_checklist_onchange(self):
        """Verify onchange assigns checklist lines from the selected template."""
        task = self.env['project.task'].create({
            'name': 'Release Feature X',
            'project_id': self.project.id,
        })
        self.assertEqual(len(task.checklist_line_ids), 0)
        self.assertEqual(task.progress, 0.0)

        task.checklist_id = self.checklist
        task._onchange_checklist_id()

        self.assertEqual(len(task.checklist_line_ids), 3)
        states = set(task.checklist_line_ids.mapped('state'))
        self.assertEqual(states, {'todo'})
        self.assertEqual(task.progress, 0.0)

    def test_03_checklist_item_state_transitions_and_progress(self):
        """Verify state transition actions and dynamic progress computation."""
        task = self.env['project.task'].create({
            'name': 'Release Feature Y',
            'project_id': self.project.id,
            'checklist_id': self.checklist.id,
        })
        task._onchange_checklist_id()
        lines = task.checklist_line_ids

        line1, line2, line3 = lines[0], lines[1], lines[2]

        # 1. Approve & Next -> in_progress
        line1.action_approve_and_next()
        self.assertEqual(line1.state, 'in_progress')
        task.invalidate_recordset(fnames=['progress'])
        self.assertEqual(task.progress, 0.0)

        # 2. Mark completed -> done (1 of 3 = 33.33%)
        line1.action_mark_completed()
        self.assertEqual(line1.state, 'done')
        task.invalidate_recordset(fnames=['progress'])
        self.assertAlmostEqual(task.progress, 100.0 / 3.0, places=2)

        # 3. Mark second completed -> done (2 of 3 = 66.67%)
        line2.action_mark_completed()
        self.assertEqual(line2.state, 'done')
        task.invalidate_recordset(fnames=['progress'])
        self.assertAlmostEqual(task.progress, 200.0 / 3.0, places=2)

        # 4. Mark third completed -> done (3 of 3 = 100.0%)
        line3.action_mark_completed()
        self.assertEqual(line3.state, 'done')
        task.invalidate_recordset(fnames=['progress'])
        self.assertEqual(task.progress, 100.0)

        # 5. Mark third canceled -> cancel (2 of 3 = 66.67%)
        line3.action_mark_canceled()
        self.assertEqual(line3.state, 'cancel')
        task.invalidate_recordset(fnames=['progress'])
        self.assertAlmostEqual(task.progress, 200.0 / 3.0, places=2)

    def test_04_task_start_and_end_dates(self):
        """Verify scheduled start_date and end_date fields on project.task."""
        dt_start = datetime(2026, 11, 1, 9, 0, 0)
        dt_end = datetime(2026, 11, 15, 18, 0, 0)

        task = self.env['project.task'].create({
            'name': 'Scheduled Task With Dates',
            'project_id': self.project.id,
            'start_date': dt_start,
            'end_date': dt_end,
        })
        self.assertEqual(task.start_date, dt_start)
        self.assertEqual(task.end_date, dt_end)

    def test_05_task_cascade_deletion(self):
        """Verify deleting a task cascades and removes its checklist lines."""
        task = self.env['project.task'].create({
            'name': 'Temporary Task',
            'project_id': self.project.id,
            'checklist_id': self.checklist.id,
        })
        task._onchange_checklist_id()
        line_ids = task.checklist_line_ids.ids
        self.assertTrue(line_ids)

        task.unlink()
        remaining_lines = self.env['checklist.item.line'].search([('id', 'in', line_ids)])
        self.assertFalse(remaining_lines)

    def test_06_access_rights(self):
        """Verify internal user (base.group_user) has access to checklist models."""
        demo_user = self.env['res.users'].create({
            'name': 'Demo Internal User',
            'login': 'demo_internal_user_chk',
            'email': 'demo_chk@example.com',
            'group_ids': [self.env.ref('base.group_user').id],
        })
        # Read checklist as demo user
        checklists = self.env['task.checklist'].with_user(demo_user).search([])
        self.assertIn(self.checklist, checklists)

        # Read checklist item as demo user
        items = self.env['checklist.item'].with_user(demo_user).search([])
        self.assertIn(self.item_1, items)

        # Create checklist line as demo user
        task = self.env['project.task'].create({
            'name': 'Demo User Task',
            'project_id': self.project.id,
        })
        line = self.env['checklist.item.line'].with_user(demo_user).create({
            'task_id': task.id,
            'check_list_item_id': self.item_1.id,
            'checklist_id': self.checklist.id,
        })
        self.assertTrue(line.id)
        line.with_user(demo_user).action_approve_and_next()
        self.assertEqual(line.state, 'in_progress')

