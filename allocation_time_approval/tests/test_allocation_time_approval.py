from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAllocationTimeApproval(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env.ref("project.project_project_1")
        cls.stage_new = cls.env.ref("project.project_stage_0")
        cls.stage_in_progress = cls.env.ref("project.project_stage_1")
        cls.stage_to_approve = cls.env.ref(
            "allocation_time_approval.task_type_to_approve"
        )
        cls.project_user = cls.env["res.users"].with_context(
            no_reset_password=True
        ).create(
            {
                "name": "Allocation Approval User",
                "login": "allocation_approval_user",
                "email": "allocation_approval_user@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("project.group_project_user").id])
                ],
            }
        )

    def _create_task(self, planned_hours=6.0):
        return self.env["project.task"].create(
            {
                "name": "Allocation Approval Task",
                "project_id": self.project.id,
                "user_ids": [(6, 0, [self.project_user.id])],
                "planned_hours": planned_hours,
                "stage_id": self.stage_new.id,
            }
        )

    def test_action_approval_creates_manager_approval(self):
        task = self._create_task(planned_hours=8.5)

        task.action_approval()

        approval = self.env["manager.approval"].search(
            [("task_id", "=", task.id)], limit=1
        )
        self.assertTrue(approval)
        self.assertEqual(task.stage_id, self.stage_to_approve)
        self.assertEqual(task.planned_hours, 0.0)
        self.assertEqual(approval.task, task.name)
        self.assertEqual(approval.project_id, task.project_id)
        self.assertEqual(approval.user_ids, task.user_ids)
        self.assertEqual(approval.planned_hours, 8.5)

    def test_manager_approval_approve_updates_task(self):
        task = self._create_task(planned_hours=5.0)
        task.action_approval()
        approval = self.env["manager.approval"].search(
            [("task_id", "=", task.id)], limit=1
        )

        approval.action_approve()
        task.invalidate_cache()

        self.assertEqual(task.stage_id, self.stage_in_progress)
        self.assertEqual(task.manager_approval_id, approval)
        self.assertEqual(task.planned_hours, 5.0)
        self.assertTrue(approval.button_view_boolean)
        self.assertFalse(approval.button_view_boolean_cancel)

    def test_project_user_cannot_move_task_from_to_approve(self):
        task = self._create_task()
        task.action_approval()

        with self.assertRaises(ValidationError):
            task.with_user(self.project_user).write(
                {"stage_id": self.stage_in_progress.id}
            )
