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
"""Automated unit tests for Project and Task Progress Status module."""
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProjectProgressBar(TransactionCase):
    """Test suite covering models, computed fields, constraints, and edge cases
    for project_progress_bar.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test environment and isolate test stages."""
        super().setUpClass()
        # Ensure any pre-existing stages do not conflict with progress constraint checks
        cls.env['project.task.type'].search([
            ('is_progress_stage', '=', True)
        ]).write({'is_progress_stage': False})

        # Test project
        cls.project = cls.env['project.project'].create({
            'name': 'Test Progress Project',
            'is_progress_bar': True,
        })

    def test_01_project_task_type_valid_creation(self):
        """Test valid creation of stages with ascending sequence and progress."""
        stage_1 = self.env['project.task.type'].create({
            'name': 'Progress Stage 1',
            'sequence': 10,
            'progress_bar': 20.0,
            'is_progress_stage': True,
        })
        stage_2 = self.env['project.task.type'].create({
            'name': 'Progress Stage 2',
            'sequence': 20,
            'progress_bar': 50.0,
            'is_progress_stage': True,
        })
        # Test creating a stage with a lower sequence and lower progress
        stage_0 = self.env['project.task.type'].create({
            'name': 'Progress Stage 0',
            'sequence': 5,
            'progress_bar': 10.0,
            'is_progress_stage': True,
        })
        self.assertTrue(stage_1.is_progress_stage)
        self.assertEqual(stage_1.progress_bar, 20.0)
        self.assertTrue(stage_2.is_progress_stage)
        self.assertEqual(stage_2.progress_bar, 50.0)
        self.assertTrue(stage_0.is_progress_stage)
        self.assertEqual(stage_0.progress_bar, 10.0)

    def test_02_project_task_type_duplicate_progress(self):
        """Test that duplicate progress bar values raise a UserError."""
        self.env['project.task.type'].create({
            'name': 'Unique Stage 1',
            'sequence': 10,
            'progress_bar': 35.0,
            'is_progress_stage': True,
        })
        with self.assertRaises(UserError):
            self.env['project.task.type'].create({
                'name': 'Duplicate Progress Stage',
                'sequence': 20,
                'progress_bar': 35.0,
                'is_progress_stage': True,
            })

    def test_03_project_task_type_sequence_mismatch_lower_progress(self):
        """Test error when a higher sequence has a lower progress value."""
        self.env['project.task.type'].create({
            'name': 'Base Stage',
            'sequence': 10,
            'progress_bar': 40.0,
            'is_progress_stage': True,
        })
        with self.assertRaises(UserError):
            self.env['project.task.type'].create({
                'name': 'Invalid Sequence Higher Stage',
                'sequence': 20,
                'progress_bar': 25.0,
                'is_progress_stage': True,
            })

    def test_04_project_task_type_sequence_mismatch_higher_progress(self):
        """Test error when a lower sequence has a higher progress value."""
        self.env['project.task.type'].create({
            'name': 'Higher Sequence Stage',
            'sequence': 30,
            'progress_bar': 50.0,
            'is_progress_stage': True,
        })
        with self.assertRaises(UserError):
            self.env['project.task.type'].create({
                'name': 'Invalid Lower Sequence Stage',
                'sequence': 10,
                'progress_bar': 70.0,
                'is_progress_stage': True,
            })

    def test_05_project_task_type_progress_over_100(self):
        """Test that progress bar value exceeding 100 raises a UserError."""
        with self.assertRaises(UserError):
            self.env['project.task.type'].create({
                'name': 'Over 100 Stage',
                'sequence': 10,
                'progress_bar': 105.0,
                'is_progress_stage': True,
            })

    def test_06_project_task_type_non_progress_stage(self):
        """Test that stages without is_progress_stage can be created freely."""
        stage = self.env['project.task.type'].create({
            'name': 'Normal Stage',
            'sequence': 1,
            'progress_bar': 0.0,
            'is_progress_stage': False,
        })
        self.assertFalse(stage.is_progress_stage)

    def test_07_task_progress_bar_compute(self):
        """Test progress_bar and stage_is_progress computation on project.task."""
        stage_1 = self.env['project.task.type'].create({
            'name': 'Task Progress Stage 1',
            'sequence': 10,
            'progress_bar': 30.0,
            'is_progress_stage': True,
        })
        stage_2 = self.env['project.task.type'].create({
            'name': 'Task Progress Stage 2',
            'sequence': 20,
            'progress_bar': 70.0,
            'is_progress_stage': True,
        })
        task_1 = self.env['project.task'].create({
            'name': 'Test Task 1',
            'project_id': self.project.id,
            'stage_id': stage_1.id,
        })
        task_2 = self.env['project.task'].create({
            'name': 'Test Task 2',
            'project_id': self.project.id,
            'stage_id': stage_2.id,
        })

        self.assertEqual(task_1.progress_bar, 30.0)
        self.assertTrue(task_1.stage_is_progress)
        self.assertEqual(task_2.progress_bar, 70.0)
        self.assertTrue(task_2.stage_is_progress)

        # Stage change recomputes progress
        task_1.write({'stage_id': stage_2.id})
        self.assertEqual(task_1.progress_bar, 70.0)

        # Multi-recordset execution
        (task_1 | task_2)._compute_progress_bar()
        self.assertEqual(task_1.progress_bar, 70.0)
        self.assertEqual(task_2.progress_bar, 70.0)

    def test_08_project_progress_bar_empty_tasks(self):
        """Test project.progressbar computes 0 when there are no tasks."""
        empty_project = self.env['project.project'].create({
            'name': 'Empty Task Project',
            'is_progress_bar': True,
        })
        empty_project._compute_progress_bar()
        self.assertEqual(empty_project.progressbar, 0.0)

    def test_09_project_progress_bar_non_progress_tasks(self):
        """Test project.progressbar computes 0 when tasks are not in progress stages."""
        normal_stage = self.env['project.task.type'].create({
            'name': 'Non Progress Stage',
            'sequence': 5,
            'is_progress_stage': False,
        })
        project = self.env['project.project'].create({
            'name': 'Project with Non Progress Tasks',
            'is_progress_bar': True,
        })
        self.env['project.task'].create({
            'name': 'Non Progress Task',
            'project_id': project.id,
            'stage_id': normal_stage.id,
        })
        project._compute_progress_bar()
        self.assertEqual(project.progressbar, 0.0)

    def test_10_project_progress_bar_average_calculation(self):
        """Test project.progressbar calculates the average of progress tasks."""
        stage_1 = self.env['project.task.type'].create({
            'name': 'Avg Stage 1',
            'sequence': 10,
            'progress_bar': 25.0,
            'is_progress_stage': True,
        })
        stage_2 = self.env['project.task.type'].create({
            'name': 'Avg Stage 2',
            'sequence': 20,
            'progress_bar': 75.0,
            'is_progress_stage': True,
        })
        project = self.env['project.project'].create({
            'name': 'Average Progress Project',
            'is_progress_bar': True,
        })
        self.env['project.task'].create({
            'name': 'Task A',
            'project_id': project.id,
            'stage_id': stage_1.id,
        })
        self.env['project.task'].create({
            'name': 'Task B',
            'project_id': project.id,
            'stage_id': stage_2.id,
        })
        project._compute_progress_bar()
        self.assertAlmostEqual(project.progressbar, 50.0)

    def test_11_project_multi_recordset_compute(self):
        """Test project._compute_progress_bar on multi-recordset."""
        stage = self.env['project.task.type'].create({
            'name': 'Multi Stage',
            'sequence': 15,
            'progress_bar': 60.0,
            'is_progress_stage': True,
        })
        proj_1 = self.env['project.project'].create({'name': 'Project Multi 1'})
        proj_2 = self.env['project.project'].create({'name': 'Project Multi 2'})
        self.env['project.task'].create({
            'name': 'Task Proj 1',
            'project_id': proj_1.id,
            'stage_id': stage.id,
        })
        self.env['project.task'].create({
            'name': 'Task Proj 2',
            'project_id': proj_2.id,
            'stage_id': stage.id,
        })

        (proj_1 | proj_2)._compute_progress_bar()
        self.assertEqual(proj_1.progressbar, 60.0)
        self.assertEqual(proj_2.progressbar, 60.0)

    def test_12_project_is_progress_bar_toggle(self):
        """Test toggling is_progress_bar boolean field on project.project."""
        project = self.env['project.project'].create({
            'name': 'Toggle Flag Project',
            'is_progress_bar': False,
        })
        self.assertFalse(project.is_progress_bar)
        project.write({'is_progress_bar': True})
        self.assertTrue(project.is_progress_bar)

    def test_13_project_task_type_multi_recordset_and_project_scoping(self):
        """Test stage constraint multi-recordset execution and project scoping."""
        proj_a = self.env['project.project'].create({'name': 'Project Alpha'})
        proj_b = self.env['project.project'].create({'name': 'Project Beta'})

        # Same progress percentage on different projects must NOT raise duplicate error
        stage_a = self.env['project.task.type'].create({
            'name': 'Alpha 50%',
            'sequence': 10,
            'progress_bar': 50.0,
            'is_progress_stage': True,
            'project_ids': [proj_a.id],
        })
        stage_b = self.env['project.task.type'].create({
            'name': 'Beta 50%',
            'sequence': 10,
            'progress_bar': 50.0,
            'is_progress_stage': True,
            'project_ids': [proj_b.id],
        })
        self.assertEqual(stage_a.progress_bar, 50.0)
        self.assertEqual(stage_b.progress_bar, 50.0)

        # Batch update across multi-recordset to ensure no singleton error
        (stage_a | stage_b).write({'progress_bar': 65.0})
        self.assertEqual(stage_a.progress_bar, 65.0)
        self.assertEqual(stage_b.progress_bar, 65.0)

    def test_14_project_task_type_negative_progress(self):
        """Test that negative progress bar value raises a UserError."""
        with self.assertRaises(UserError):
            self.env['project.task.type'].create({
                'name': 'Negative Progress Stage',
                'sequence': 10,
                'progress_bar': -10.0,
                'is_progress_stage': True,
            })


