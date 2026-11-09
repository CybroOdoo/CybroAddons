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
class TestProjectTaskSequence(TransactionCase):
    """Test suite for project and task sequence numbering functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Project = cls.env['project.project']
        cls.Task = cls.env['project.task']

    def test_01_project_default_sequence(self):
        """Test project sequence generation with default prefix."""
        project = self.Project.create({
            'name': 'Default Sequence Project',
        })
        self.assertTrue(project.project_sequence)
        self.assertNotEqual(project.project_sequence, 'New')
        self.assertTrue(project.project_sequence.startswith('PRJ/'))
        self.assertTrue(project.task_sequence_id)

    def test_02_project_custom_prefix(self):
        """Test project sequence generation with custom prefix."""
        project = self.Project.create({
            'name': 'Alpha Project',
            'project_prefix': 'ALPHA',
        })
        self.assertTrue(project.project_sequence)
        self.assertTrue(project.project_sequence.startswith('ALPHA/'))
        self.assertTrue(project.task_sequence_id)

    def test_03_project_prefix_write(self):
        """Test updating project prefix on an existing project."""
        project = self.Project.create({
            'name': 'Mutable Project',
            'project_prefix': 'INIT',
        })
        initial_seq = project.project_sequence
        self.assertTrue(initial_seq.startswith('INIT/'))

        project.write({'project_prefix': 'UPDATE'})
        self.assertTrue(project.project_sequence.startswith('UPDATE/'))
        self.assertNotEqual(project.project_sequence, initial_seq)

    def test_04_task_sequence_generation(self):
        """Test task sequence generation under a project."""
        project = self.Project.create({
            'name': 'Task Test Project',
            'project_prefix': 'TESTPRJ',
        })
        task1 = self.Task.create({
            'name': 'Task 1',
            'project_id': project.id,
        })
        self.assertTrue(task1.task_sequence)
        self.assertNotEqual(task1.task_sequence, 'New')
        self.assertTrue(task1.task_sequence.startswith(project.project_sequence))
        self.assertTrue(task1.task_sequence.endswith('0001'))

        # Create second task in the same project
        task2 = self.Task.create({
            'name': 'Task 2',
            'project_id': project.id,
        })
        self.assertTrue(task2.task_sequence)
        self.assertTrue(task2.task_sequence.startswith(project.project_sequence))
        self.assertTrue(task2.task_sequence.endswith('0002'))

    def test_05_subtask_hierarchical_sequence(self):
        """Test sub-task hierarchical sequence generation."""
        project = self.Project.create({
            'name': 'Subtask Test Project',
            'project_prefix': 'HIER',
        })
        parent_task = self.Task.create({
            'name': 'Parent Task',
            'project_id': project.id,
        })
        self.assertTrue(parent_task.task_sequence)

        subtask1 = self.Task.create({
            'name': 'Subtask 1',
            'project_id': project.id,
            'parent_id': parent_task.id,
        })
        expected_sub1 = f"{parent_task.task_sequence}/Sub Task 1"
        self.assertEqual(subtask1.task_sequence, expected_sub1)

        subtask2 = self.Task.create({
            'name': 'Subtask 2',
            'project_id': project.id,
            'parent_id': parent_task.id,
        })
        expected_sub2 = f"{parent_task.task_sequence}/Sub Task 2"
        self.assertEqual(subtask2.task_sequence, expected_sub2)

    def test_06_task_write_and_bypass_context(self):
        """Test updating a task and verifying bypass_sequence context."""
        project = self.Project.create({
            'name': 'Write Test Project',
        })
        task = self.Task.create({
            'name': 'Task Before Write',
            'project_id': project.id,
        })
        orig_seq = task.task_sequence
        self.assertTrue(orig_seq)

        # Write without bypass context
        task.write({'name': 'Task After Normal Write'})
        self.assertTrue(task.task_sequence)

        # Write with bypass context
        task.with_context(bypass_sequence=True).write({'name': 'Task After Bypass Write'})
        self.assertTrue(task.task_sequence)

    def test_07_task_without_project(self):
        """Test creating a task without assigning a project."""
        task = self.Task.create({
            'name': 'Stand-alone Task',
        })
        # When no project is set, custom sequence remains default 'New'
        self.assertEqual(task.task_sequence, 'New')

    def test_08_batch_create(self):
        """Test batch creation of projects and tasks."""
        projects = self.Project.create([
            {'name': 'Batch Project 1', 'project_prefix': 'BATCH1'},
            {'name': 'Batch Project 2', 'project_prefix': 'BATCH2'},
        ])
        self.assertEqual(len(projects), 2)
        self.assertTrue(projects[0].project_sequence.startswith('BATCH1/'))
        self.assertTrue(projects[1].project_sequence.startswith('BATCH2/'))

        tasks = self.Task.create([
            {'name': 'Batch Task 1', 'project_id': projects[0].id},
            {'name': 'Batch Task 2', 'project_id': projects[1].id},
        ])
        self.assertEqual(len(tasks), 2)
        self.assertTrue(tasks[0].task_sequence.startswith(projects[0].project_sequence))
        self.assertTrue(tasks[1].task_sequence.startswith(projects[1].project_sequence))
