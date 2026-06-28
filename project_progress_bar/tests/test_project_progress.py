# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class TestProjectProgress(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProjectProgress, cls).setUpClass()
        _logger.info("Setting up TestProjectProgress environment")

        # Deactivate any existing stages that have is_progress_stage=True to avoid test interference
        cls.env['project.task.type'].search([('is_progress_stage', '=', True)]).write({'is_progress_stage': False})

        # Create a project
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project Progress Bar',
        })

        # Create unique stages for tests
        cls.stage_new = cls.env['project.task.type'].create({
            'name': 'Test Stage New',
            'sequence': 1000,
            'is_progress_stage': True,
            'progress_bar': 10.0,
        })
        cls.stage_progress = cls.env['project.task.type'].create({
            'name': 'Test Stage In Progress',
            'sequence': 2000,
            'is_progress_stage': True,
            'progress_bar': 50.0,
        })
        cls.stage_done = cls.env['project.task.type'].create({
            'name': 'Test Stage Done',
            'sequence': 3000,
            'is_progress_stage': True,
            'progress_bar': 100.0,
        })

        # A stage that is NOT a progress stage
        cls.stage_draft = cls.env['project.task.type'].create({
            'name': 'Test Stage Draft',
            'sequence': 500,
            'is_progress_stage': False,
            'progress_bar': 0.0,
        })
        _logger.info("setUpClass completed successfully")

    def test_01_stage_constraints(self):
        """Test the constraints on project.task.type (stages)."""
        _logger.info("Running test_01_stage_constraints")

        # 1. Progress percentage cannot exceed 100
        with self.assertRaises(UserError, msg="Progress percentage should be <= 100"):
            self.env['project.task.type'].create({
                'name': 'Invalid Progress Stage',
                'sequence': 4000,
                'is_progress_stage': True,
                'progress_bar': 101.0,
            })
        _logger.info("Constraint for progress > 100 validated successfully")

        # 2. Progress must not be duplicated
        with self.assertRaises(UserError, msg="Progress percentage cannot be duplicated"):
            self.env['project.task.type'].create({
                'name': 'Duplicate Progress Stage',
                'sequence': 4000,
                'is_progress_stage': True,
                'progress_bar': 50.0,  # Duplicate of stage_progress
            })
        _logger.info("Constraint for duplicated progress validated successfully")

        # 3. Sequence and progress percentage must align
        # Stage with higher sequence must have greater progress
        with self.assertRaises(UserError, msg="Higher sequence stage must have greater progress"):
            self.env['project.task.type'].create({
                'name': 'Bad Sequence Stage',
                'sequence': 2500,  # between sequence 2000 (50.0) and 3000 (100.0)
                'is_progress_stage': True,
                'progress_bar': 40.0,  # 40% < 50% of sequence 2000, which is incorrect
            })
        _logger.info("Constraint for higher sequence / lower progress validated successfully")

        # Stage with lower sequence must have lower progress
        with self.assertRaises(UserError, msg="Lower sequence stage must have lower progress"):
            self.env['project.task.type'].create({
                'name': 'Bad Sequence Stage 2',
                'sequence': 1500,  # between sequence 1000 (10.0) and 2000 (50.0)
                'is_progress_stage': True,
                'progress_bar': 60.0,  # 60% > 50% of sequence 2000, which is incorrect
            })
        _logger.info("Constraint for lower sequence / higher progress validated successfully")

    def test_02_task_progress_calculation(self):
        """Test the progress_bar computation on project.task."""
        _logger.info("Running test_02_task_progress_calculation")

        # Create a task in stage_new
        task = self.env['project.task'].create({
            'name': 'Test Task 1',
            'project_id': self.project.id,
            'stage_id': self.stage_new.id,
        })
        self.assertEqual(task.progress_bar, 10.0, "Task progress bar should match the stage progress bar")

        # Change the stage of the task
        task.stage_id = self.stage_progress.id
        self.assertEqual(task.progress_bar, 50.0, "Task progress bar should update when stage is changed")
        _logger.info("Task progress bar compute and stage change verified successfully")

    def test_03_project_progress_average(self):
        """Test that project progress_bar computes average of tasks' progress in progress stages."""
        _logger.info("Running test_03_project_progress_average")

        # Initially, no tasks, progressbar should be 0
        self.assertEqual(self.project.progressbar, 0.0, "Project progress should be 0 when there are no tasks")

        # Create tasks
        task1 = self.env['project.task'].create({
            'name': 'Task 1',
            'project_id': self.project.id,
            'stage_id': self.stage_new.id,  # 10%
        })
        task2 = self.env['project.task'].create({
            'name': 'Task 2',
            'project_id': self.project.id,
            'stage_id': self.stage_progress.id,  # 50%
        })
        # This task is in stage_draft which is NOT a progress stage, so it should be ignored in the calculation
        task3 = self.env['project.task'].create({
            'name': 'Task 3',
            'project_id': self.project.id,
            'stage_id': self.stage_draft.id,  # 0%, but is_progress_stage=False
        })

        # Trigger compute
        self.project._compute_progress_bar()

        # Expected: average of (10% + 50%) = 30%
        self.assertEqual(self.project.progressbar, 30.0, "Project progress should be the average of tasks in progress stages")
        _logger.info("Project average progress calculation verified successfully")
