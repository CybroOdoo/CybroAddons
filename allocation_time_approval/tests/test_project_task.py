from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProjectTaskAllocationApproval(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_project_task_stage_xmlids()
        cls.project = cls.env['project.project'].create({
            'name': 'Task Allocation Approval Project',
            'allow_timesheets': True,
        })
        cls.stage_new = cls.env.ref('project.project_stage_0')
        cls.stage_progress = cls.env.ref('project.project_stage_1')
        cls.stage_done = cls.env.ref('project.project_stage_2')
        cls.stage_cancel = cls.env.ref('project.project_stage_3')
        cls.stage_to_approve = cls.env.ref(
            'allocation_time_approval.task_type_to_approve')
        for stage in (
                cls.stage_new, cls.stage_progress, cls.stage_done,
                cls.stage_cancel, cls.stage_to_approve):
            stage.write({'project_ids': [(4, cls.project.id)]})

        base_group = cls.env.ref('base.group_user')
        cls.project_user = cls.env['res.users'].create({
            'name': 'Allocation Project User',
            'login': 'allocation_project_user',
            'email': 'allocation_project_user@example.com',
            'group_ids': [(6, 0, [
                base_group.id,
                cls.env.ref('project.group_project_user').id,
                cls.env.ref('hr_timesheet.group_hr_timesheet_user').id,
            ])],
        })
        cls.project_manager = cls.env['res.users'].create({
            'name': 'Allocation Project Manager',
            'login': 'allocation_project_manager',
            'email': 'allocation_project_manager@example.com',
            'group_ids': [(6, 0, [
                base_group.id,
                cls.env.ref('project.group_project_manager').id,
                cls.env.ref('hr_timesheet.group_hr_timesheet_user').id,
            ])],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Allocation Project Employee',
            'user_id': cls.project_user.id,
        })
        cls.personal_done_stage = cls.env['project.task.type'].create({
            'name': 'Done',
            'sequence': 6,
            'fold': True,
            'user_id': cls.project_user.id,
        })
        cls.personal_cancel_stage = cls.env['project.task.type'].create({
            'name': 'Cancel',
            'sequence': 5,
            'fold': True,
            'user_id': cls.project_user.id,
        })

    @classmethod
    def _ensure_project_task_stage_xmlids(cls):
        stages = {
            'project_stage_0': {'name': 'New', 'sequence': 1},
            'project_stage_1': {'name': 'In Progress', 'sequence': 2},
            'project_stage_2': {'name': 'Done', 'sequence': 3, 'fold': True},
            'project_stage_3': {'name': 'Cancel', 'sequence': 4, 'fold': True},
        }
        for xmlid_name, values in stages.items():
            if cls.env.ref(f'project.{xmlid_name}', raise_if_not_found=False):
                continue
            stage = cls.env['project.task.type'].create(values)
            cls.env['ir.model.data'].sudo().create({
                'module': 'project',
                'name': xmlid_name,
                'model': 'project.task.type',
                'res_id': stage.id,
            })

    def _create_task(self, name, stage=None, user=None, allocated_hours=4.0):
        return self.env['project.task'].create({
            'name': name,
            'project_id': self.project.id,
            'stage_id': (stage or self.stage_new).id,
            'user_ids': [(6, 0, [(user or self.project_user).id])],
            'allocated_hours': allocated_hours,
        })

    def _create_approval(self, task):
        return self.env['manager.approval'].create({
            'task': task.name,
            'project_id': task.project_id.id,
            'user_ids': [(6, 0, task.user_ids.ids)],
            'planned_hours': task.allocated_hours,
            'task_id': task.id,
        })

    def test_stage_boolean_computes_match_current_stage(self):
        task = self._create_task('Boolean Draft Task', stage=self.stage_new)
        self.assertTrue(task.is_new_stage)
        self.assertFalse(task.is_approve_stage)
        self.assertFalse(task.is_progress_stage)

        task.stage_id = self.stage_to_approve
        self.assertFalse(task.is_new_stage)
        self.assertTrue(task.is_approve_stage)
        self.assertFalse(task.is_progress_stage)

        task.stage_id = self.stage_progress
        self.assertFalse(task.is_new_stage)
        self.assertFalse(task.is_approve_stage)
        self.assertTrue(task.is_progress_stage)

    def test_action_approval_moves_task_and_creates_manager_approval(self):
        task = self._create_task('Task Sent For Approval',
                                 allocated_hours=7.0)

        task.with_user(self.project_user).action_approval()

        approval = self.env['manager.approval'].sudo().search([
            ('task_id', '=', task.id),
        ])
        self.assertEqual(task.stage_id, self.stage_to_approve)
        self.assertFalse(task.is_create_task)
        self.assertEqual(task.allocated_hours, 0.0)
        self.assertEqual(len(approval), 1)
        self.assertEqual(approval.task, 'Task Sent For Approval')
        self.assertEqual(approval.project_id, self.project)
        self.assertEqual(approval.user_ids, self.project_user)
        self.assertEqual(approval.planned_hours, 7.0)

    def test_action_done_rejects_non_manager_when_spent_exceeds_allocated(self):
        task = self._create_task('Over Budget Task',
                                 stage=self.stage_progress,
                                 allocated_hours=1.0)
        self.env['account.analytic.line'].create({
            'name': 'Over budget work',
            'project_id': self.project.id,
            'task_id': task.id,
            'employee_id': self.employee.id,
            'unit_amount': 2.0,
        })
        task.invalidate_recordset(['effective_hours'])

        with self.assertRaises(UserError):
            task.with_user(self.project_user).action_done()

        self.assertEqual(task.stage_id, self.stage_progress)

    def test_action_done_allows_manager_and_updates_personal_stage(self):
        task = self._create_task('Manager Done Task',
                                 stage=self.stage_progress,
                                 allocated_hours=1.0)
        self.env['account.analytic.line'].create({
            'name': 'Manager accepted work',
            'project_id': self.project.id,
            'task_id': task.id,
            'employee_id': self.employee.id,
            'unit_amount': 2.0,
        })
        personal_stage = self.env['project.task.stage.personal'].search([
            ('task_id', '=', task.id),
            ('user_id', '=', self.project_user.id),
        ])

        task.with_user(self.project_manager).action_done()

        self.assertEqual(task.stage_id, self.stage_done)
        self.assertTrue(personal_stage.stage_id)

    def test_action_cancel_moves_task_and_updates_personal_stage(self):
        task = self._create_task('Cancelled Task', stage=self.stage_progress)
        personal_stage = self.env['project.task.stage.personal'].search([
            ('task_id', '=', task.id),
            ('user_id', '=', self.project_user.id),
        ])

        task.with_user(self.project_user).action_cancel()

        self.assertEqual(task.stage_id, self.stage_cancel)
        self.assertTrue(personal_stage.stage_id)

    def test_update_personal_stages_assigns_current_user_when_task_has_none(self):
        task = self.env['project.task'].create({
            'name': 'Task Without Assignee',
            'project_id': self.project.id,
            'stage_id': self.stage_progress.id,
        })
        task.write({'user_ids': [(5, 0, 0)]})

        task.with_user(self.project_user)._update_personal_stages('done')

        task.invalidate_recordset(['user_ids'])
        self.assertIn(self.project_user, task.user_ids)
        personal_stage = self.env['project.task.stage.personal'].search([
            ('task_id', '=', task.id),
            ('user_id', '=', self.project_user.id),
        ])
        self.assertTrue(personal_stage.stage_id)

    def test_non_manager_cannot_move_new_task_directly_to_progress(self):
        task = self._create_task('Restricted New Task', stage=self.stage_new)

        with self.assertRaises(ValidationError):
            task.with_user(self.project_user).write({
                'stage_id': self.stage_progress.id,
            })

    def test_non_manager_can_only_move_new_task_to_approval(self):
        task = self._create_task('Allowed Approval Move', stage=self.stage_new)

        task.with_user(self.project_user).write({
            'stage_id': self.stage_to_approve.id,
        })

        approval = self.env['manager.approval'].sudo().search([
            ('task_id', '=', task.id),
        ])
        self.assertEqual(task.stage_id, self.stage_to_approve)
        self.assertEqual(len(approval), 1)
        self.assertEqual(task.allocated_hours, 0.0)

    def test_manager_move_from_to_approve_to_progress_marks_approval_approved(self):
        task = self._create_task('Manager Approves Task',
                                 stage=self.stage_to_approve)
        approval = self._create_approval(task)

        task.with_user(self.project_manager).write({
            'stage_id': self.stage_progress.id,
        })

        self.assertEqual(task.stage_id, self.stage_progress)
        self.assertTrue(approval.is_button_view)
        self.assertFalse(approval.is_button_view_cancel)

    def test_manager_move_from_to_approve_to_done_removes_approval(self):
        task = self._create_task('Manager Completes Approval',
                                 stage=self.stage_to_approve)
        approval = self._create_approval(task)

        task.with_user(self.project_manager).write({
            'stage_id': self.stage_done.id,
        })

        self.assertFalse(approval.exists())

    def test_manager_cannot_move_done_task_back_to_approval(self):
        task = self._create_task('Done Back To Approval',
                                 stage=self.stage_done)

        with self.assertRaises(ValidationError):
            task.with_user(self.project_manager).write({
                'stage_id': self.stage_to_approve.id,
            })
