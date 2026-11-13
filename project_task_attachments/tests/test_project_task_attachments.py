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
class TestProjectTaskAttachments(TransactionCase):
    """Test suite covering project and task attachment functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({
            'name': 'Test Attachment Project',
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Test Attachment Task',
            'project_id': cls.project.id,
        })

    def test_01_create_project_attachment_via_project_id(self):
        """Test creating an attachment with project_id sets res_model and attach_to."""
        attachment = self.env['ir.attachment'].create({
            'name': 'Project Plan.pdf',
            'project_id': self.project.id,
        })
        self.assertEqual(attachment.attach_to, 'project', "Attachment attach_to must be 'project'.")
        self.assertEqual(attachment.res_model, 'project.project', "res_model must be set to 'project.project'.")
        self.assertEqual(attachment.res_id, self.project.id, "res_id must match the project ID.")
        self.assertFalse(attachment.task_id, "task_id should not be set for a project attachment.")

    def test_02_create_task_attachment_via_task_id(self):
        """Test creating an attachment with task_id sets res_model and attach_to."""
        attachment = self.env['ir.attachment'].create({
            'name': 'Task Specification.pdf',
            'task_id': self.task.id,
        })
        self.assertEqual(attachment.attach_to, 'task', "Attachment attach_to must be 'task'.")
        self.assertEqual(attachment.res_model, 'project.task', "res_model must be set to 'project.task'.")
        self.assertEqual(attachment.res_id, self.task.id, "res_id must match the task ID.")
        self.assertFalse(attachment.project_id, "project_id should not be set for a task attachment.")

    def test_03_create_attachment_from_action_context(self):
        """Test attaching new documents using action context defaults."""
        # Project documents action context simulation
        project_attachment = self.env['ir.attachment'].with_context(
            default_attach_to='project',
            default_res_model='project.project',
        ).create({
            'name': 'Project Document.txt',
            'project_id': self.project.id,
        })
        self.assertEqual(project_attachment.attach_to, 'project')
        self.assertEqual(project_attachment.res_model, 'project.project')
        self.assertEqual(project_attachment.res_id, self.project.id)

        # Task documents action context simulation
        task_attachment = self.env['ir.attachment'].with_context(
            default_attach_to='task',
            default_res_model='project.task',
        ).create({
            'name': 'Task Document.txt',
            'task_id': self.task.id,
        })
        self.assertEqual(task_attachment.attach_to, 'task')
        self.assertEqual(task_attachment.res_model, 'project.task')
        self.assertEqual(task_attachment.res_id, self.task.id)

    def test_04_write_attachment_sync(self):
        """Test updating project_id or task_id synchronizes res_model and res_id."""
        attachment = self.env['ir.attachment'].create({
            'name': 'Sync Test Document.pdf',
            'project_id': self.project.id,
        })
        self.assertEqual(attachment.attach_to, 'project')
        self.assertEqual(attachment.res_model, 'project.project')

        # Switch to task
        attachment.write({'task_id': self.task.id})
        self.assertEqual(attachment.attach_to, 'task')
        self.assertEqual(attachment.res_model, 'project.task')
        self.assertEqual(attachment.res_id, self.task.id)
        self.assertFalse(attachment.project_id)

        # Switch back to project
        attachment.write({'project_id': self.project.id})
        self.assertEqual(attachment.attach_to, 'project')
        self.assertEqual(attachment.res_model, 'project.project')
        self.assertEqual(attachment.res_id, self.project.id)
        self.assertFalse(attachment.task_id)

    def test_05_res_model_and_res_id_sync(self):
        """Test setting res_model and res_id automatically updates project_id and task_id."""
        proj_attachment = self.env['ir.attachment'].create({
            'name': 'Direct Project.pdf',
            'res_model': 'project.project',
            'res_id': self.project.id,
        })
        self.assertEqual(proj_attachment.project_id, self.project)
        self.assertEqual(proj_attachment.attach_to, 'project')

        task_attachment = self.env['ir.attachment'].create({
            'name': 'Direct Task.pdf',
            'res_model': 'project.task',
            'res_id': self.task.id,
        })
        self.assertEqual(task_attachment.task_id, self.task)
        self.assertEqual(task_attachment.attach_to, 'task')

    def test_06_actions_allow_creation(self):
        """Verify that menu actions do not block creation with 'create': False."""
        task_action = self.env.ref('project_task_attachments.ir_attachment_action_view_task_documents', raise_if_not_found=False)
        project_action = self.env.ref('project_task_attachments.ir_attachment_action_view_project_documents', raise_if_not_found=False)

        self.assertTrue(task_action, "Task documents action must be present.")
        self.assertTrue(project_action, "Project documents action must be present.")

        task_context = task_action.context or ''
        project_context = project_action.context or ''

        self.assertNotIn("'create': False", task_context, "Task action context should not disable creation.")
        self.assertNotIn("'create': False", project_context, "Project action context should not disable creation.")
