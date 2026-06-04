from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestManagerApproval(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_project_task_stage_xmlids()
        cls.project = cls.env['project.project'].create({
            'name': 'Allocation Approval Project',
            'allow_timesheets': True,
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Allocation Approval User',
            'login': 'allocation_approval_user',
            'email': 'allocation_approval_user@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('project.group_project_user').id,
            ])],
        })
        cls.progress_stage = cls.env.ref('project.project_stage_1')
        cls.cancel_stage = cls.env.ref('project.project_stage_3')
        for stage in (cls.progress_stage, cls.cancel_stage):
            stage.write({'project_ids': [(4, cls.project.id)]})

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

    def _create_task(self):
        return self.env['project.task'].create({
            'name': 'Task Waiting Approval',
            'project_id': self.project.id,
            'user_ids': [(6, 0, [self.user.id])],
            'allocated_hours': 2.0,
        })

    def _create_approval(self, task):
        return self.env['manager.approval'].create({
            'task': 'Approved Task Name',
            'project_id': self.project.id,
            'user_ids': [(6, 0, [self.user.id])],
            'planned_hours': 6.5,
            'task_id': task.id,
        })

    def test_action_approve_updates_task_and_button_flags(self):
        task = self._create_task()
        approval = self._create_approval(task)

        approval.action_approve()

        self.assertEqual(task.name, 'Approved Task Name')
        self.assertEqual(task.project_id, self.project)
        self.assertEqual(task.user_ids, self.user)
        self.assertEqual(task.allocated_hours, 6.5)
        self.assertEqual(task.stage_id, self.progress_stage)
        self.assertEqual(task.manager_approval_id, approval)
        self.assertTrue(approval.is_button_view)
        self.assertFalse(approval.is_button_view_cancel)

    def test_action_manager_cancel_cancels_task_and_button_flags(self):
        task = self._create_task()
        approval = self._create_approval(task)

        approval.action_manager_cancel()

        self.assertEqual(task.stage_id, self.cancel_stage)
        self.assertTrue(approval.is_button_view_cancel)
        self.assertFalse(approval.is_button_view)
