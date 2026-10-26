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
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAutomaticProjectTaskTimer(TransactionCase):
    """Test suite for Automatic Project Task Timer functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Enable timer setting in system parameters
        cls.env['ir.config_parameter'].sudo().set_bool(
            'automatic_project_task_timer.timer_setting', True
        )

        # Create test project
        cls.project = cls.env['project.project'].create({
            'name': 'Timer Test Project',
            'allow_timesheets': True,
        })

        # Create stages
        cls.stage_draft = cls.env['project.task.type'].create({
            'name': 'Draft',
            'sequence': 1,
            'project_ids': [(4, cls.project.id)],
        })
        cls.stage_in_progress = cls.env['project.task.type'].create({
            'name': 'In Progress',
            'sequence': 2,
            'project_ids': [(4, cls.project.id)],
        })
        cls.stage_done = cls.env['project.task.type'].create({
            'name': 'Done',
            'sequence': 3,
            'project_ids': [(4, cls.project.id)],
        })

        # Create employee for the test user
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test User Employee',
            'user_id': cls.env.uid,
            'company_id': cls.env.company.id,
        })

        # Configure timer for In Progress stage
        cls.timer_config = cls.env['timer.configuration'].create({
            'project_id': cls.project.id,
            'stage_id': cls.stage_in_progress.id,
        })

    def test_timer_start_and_stop_lifecycle(self):
        """Test timer automatically starts on entering configured stage and stops on leaving."""
        # Create task in Draft stage
        task = self.env['project.task'].create({
            'name': 'Test Timer Task',
            'project_id': self.project.id,
            'stage_id': self.stage_draft.id,
        })

        self.assertFalse(task.task_timer, "Timer should not be active in Draft stage")
        self.assertFalse(task.is_user_working, "User should not be marked as working")
        self.assertEqual(len(task.timesheet_ids), 0, "No timesheets should exist initially")
        self.assertEqual(task.check_stage, self.stage_in_progress.id, "check_stage should match configured stage")

        # Move task to In Progress stage -> Timer should start
        task.write({'stage_id': self.stage_in_progress.id})
        self.assertTrue(task.task_timer, "Timer should be active in In Progress stage")
        self.assertTrue(task.is_user_working, "User should be marked as working")
        self.assertEqual(len(task.timesheet_ids), 1, "An active timesheet line should be created")

        open_line = task.timesheet_ids.filtered(lambda t: not t.date_end)
        self.assertTrue(open_line, "There should be an open timesheet without date_end")
        self.assertTrue(open_line.date_start, "Timesheet line should have a start date")

        # Test working duration helper
        duration = task.get_working_duration()
        self.assertGreaterEqual(duration, 0, "Working duration should return a valid non-negative number")

        # Move task out of In Progress stage to Done -> Timer should stop
        task.write({'stage_id': self.stage_done.id})
        self.assertFalse(task.task_timer, "Timer should deactivate when leaving configured stage")
        self.assertFalse(task.is_user_working, "User should no longer be marked as working")

        closed_line = task.timesheet_ids[0]
        self.assertTrue(closed_line.date_end, "Timesheet line must have an end date once stopped")
        self.assertEqual(task.duration, 0.0, "Task real duration should be reset to 0 in other stages")

    def test_timer_disabled_when_setting_turned_off(self):
        """Test timer does not start if the global configuration parameter is disabled."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'automatic_project_task_timer.timer_setting', False
        )
        task = self.env['project.task'].create({
            'name': 'Task With Disabled Setting',
            'project_id': self.project.id,
            'stage_id': self.stage_draft.id,
        })

        task.write({'stage_id': self.stage_in_progress.id})
        self.assertFalse(task.task_timer, "Timer should not activate when global setting is disabled")
        self.assertEqual(len(task.timesheet_ids), 0, "No timesheet should be created")
        # Restore timer setting
        self.env['ir.config_parameter'].sudo().set_bool(
            'automatic_project_task_timer.timer_setting', True
        )

    def test_multi_task_batch_operations(self):
        """Test multi-record safe creation and stage updates."""
        tasks = self.env['project.task'].create([
            {
                'name': 'Batch Task 1',
                'project_id': self.project.id,
                'stage_id': self.stage_draft.id,
            },
            {
                'name': 'Batch Task 2',
                'project_id': self.project.id,
                'stage_id': self.stage_in_progress.id,
            },
        ])
        self.assertEqual(len(tasks), 2)
        task1, task2 = tasks[0], tasks[1]
        self.assertFalse(task1.task_timer)
        self.assertTrue(task2.task_timer)

        # Batch write stage to draft
        tasks.write({'stage_id': self.stage_draft.id})
        self.assertFalse(task1.task_timer)
        self.assertFalse(task2.task_timer)

        # Batch write stage to in_progress
        tasks.write({'stage_id': self.stage_in_progress.id})
        self.assertTrue(task1.task_timer)
        self.assertTrue(task2.task_timer)

    def test_toggle_start(self):
        """Test manual toggle of task timer."""
        task = self.env['project.task'].create({
            'name': 'Toggle Task',
            'project_id': self.project.id,
            'stage_id': self.stage_draft.id,
        })
        self.assertFalse(task.task_timer)
        task.toggle_start()
        self.assertTrue(task.task_timer)
        task.toggle_start()
        self.assertFalse(task.task_timer)

    def test_timer_configuration_onchange_and_write(self):
        """Test timer configuration onchange and existing task updates."""
        config = self.env['timer.configuration'].new({
            'project_id': self.project.id,
        })
        config._onchange_project_id()
        self.assertTrue(self.stage_in_progress.id in config.stage_ids.ids)

        task_in_stage = self.env['project.task'].create({
            'name': 'Pre-existing Task in Stage',
            'project_id': self.project.id,
            'stage_id': self.stage_done.id,
        })

        new_config = self.env['timer.configuration'].create({
            'project_id': self.project.id,
            'stage_id': self.stage_done.id,
        })
        self.assertTrue(task_in_stage.is_status_stage)

        # Test timer.configuration write
        new_config.write({'stage_id': self.stage_in_progress.id})
        self.assertEqual(new_config.stage_id.id, self.stage_in_progress.id)

        # Test onchange when project_id is empty
        empty_config = self.env['timer.configuration'].new({})
        empty_config._onchange_project_id()
        self.assertFalse(empty_config.stage_ids)

        # Test stage_id reset on project change when stage does not belong
        other_project = self.env['project.project'].create({'name': 'Other Project'})
        config.project_id = other_project
        config.stage_id = self.stage_in_progress
        config._onchange_project_id()
        self.assertFalse(config.stage_id)

    def test_res_config_settings_and_edge_cases(self):
        """Test res.config.settings execution and edge cases on task."""
        # Test settings
        settings = self.env['res.config.settings'].create({
            'timer_setting': True,
        })
        settings.execute()
        param = self.env['ir.config_parameter'].sudo().get_bool(
            'automatic_project_task_timer.timer_setting'
        )
        self.assertTrue(param)

        # Test task without project_id
        task_no_project = self.env['project.task'].create({
            'name': 'Task without Project',
        })
        self.assertEqual(task_no_project.check_stage, 0)
        self.assertFalse(task_no_project.task_timer)

        # Test working duration when date_start is not set
        task_with_project = self.env['project.task'].create({
            'name': 'Task With Project For Duration Test',
            'project_id': self.project.id,
            'stage_id': self.stage_draft.id,
        })
        timesheet = self.env['account.analytic.line'].create({
            'name': 'Test Duration Line',
            'task_id': task_with_project.id,
            'user_id': self.env.user.id,
            'employee_id': self.employee.id,
            'project_id': self.project.id,
        })
        timesheet.date_start = False
        duration = task_with_project.get_working_duration()
        self.assertGreaterEqual(duration, 0)

