# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestIrAttachment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Test Project'})
        cls.task = cls.env['project.task'].create({
            'name': 'Test Task',
            'project_id': cls.project.id,
        })

    # ------------------------------------------------------------------ #
    # Field defaults
    # ------------------------------------------------------------------ #

    def test_attach_to_default_is_project(self):
        """Verify that the default value of attach_to is 'project' when
        only project_id is supplied and task_id is False."""
        att = self.env['ir.attachment'].create({
            'name': 'default_test.txt',
            'project_id': self.project.id,
            'task_id': False,
        })
        self.assertEqual(att.attach_to, 'project')

    def test_project_id_field_exists(self):
        """Verify that the custom project_id field is stored correctly
        on the attachment record after creation."""
        att = self.env['ir.attachment'].create({
            'name': 'field_test.txt',
            'project_id': self.project.id,
            'task_id': False,
        })
        self.assertEqual(att.project_id.id, self.project.id)

    def test_task_id_field_exists(self):
        """Verify that the custom task_id field is stored correctly
        on the attachment record when both project_id and task_id are given."""
        att = self.env['ir.attachment'].create({
            'name': 'task_field_test.txt',
            'project_id': self.project.id,
            'task_id': self.task.id,
        })
        self.assertEqual(att.task_id.id, self.task.id)

    # ------------------------------------------------------------------ #
    # Branch 1: project_id supplied, task_id falsy
    #   → res_id = project_id, res_model = 'project.project'
    # ------------------------------------------------------------------ #

    def test_create_project_only_sets_res_id(self):
        """When project_id is in vals and task_id is False, the create
        override must set res_id to the project's id."""
        att = self.env['ir.attachment'].create({
            'name': 'proj_only.txt',
            'project_id': self.project.id,
            'task_id': False,
        })
        self.assertEqual(att.res_id, self.project.id)

    def test_create_project_only_sets_res_model(self):
        """When project_id is in vals and task_id is False, the create
        override must set res_model to 'project.project'."""
        att = self.env['ir.attachment'].create({
            'name': 'proj_model.txt',
            'project_id': self.project.id,
            'task_id': False,
        })
        self.assertEqual(att.res_model, 'project.project')

    def test_create_project_only_task_id_remains_false(self):
        """When only project_id is supplied, task_id must remain False
        and must not be populated by the create override."""
        att = self.env['ir.attachment'].create({
            'name': 'proj_no_task.txt',
            'project_id': self.project.id,
            'task_id': False,
        })
        self.assertFalse(att.task_id)

    # ------------------------------------------------------------------ #
    # Branch 2: project_id supplied AND task_id supplied
    #   → res_id = task_id, res_model = 'project.task'
    # ------------------------------------------------------------------ #

    def test_create_project_and_task_sets_res_id_to_task(self):
        """When both project_id and task_id are provided, the create
        override must set res_id to the task's id, not the project's."""
        att = self.env['ir.attachment'].create({
            'name': 'proj_task.txt',
            'project_id': self.project.id,
            'task_id': self.task.id,
        })
        self.assertEqual(att.res_id, self.task.id)

    def test_create_project_and_task_sets_res_model_to_task(self):
        """When both project_id and task_id are provided, the create
        override must set res_model to 'project.task'."""
        att = self.env['ir.attachment'].create({
            'name': 'proj_task_model.txt',
            'project_id': self.project.id,
            'task_id': self.task.id,
        })
        self.assertEqual(att.res_model, 'project.task')

    def test_create_project_and_task_project_id_preserved(self):
        """When both project_id and task_id are supplied, project_id
        must still be stored on the attachment even though res_id points
        to the task."""
        att = self.env['ir.attachment'].create({
            'name': 'proj_task_pid.txt',
            'project_id': self.project.id,
            'task_id': self.task.id,
        })
        self.assertEqual(att.project_id.id, self.project.id)

    # ------------------------------------------------------------------ #
    # Branch 3: no project_id key, res_model = 'project.project'
    #   → project_id = res_id, attach_to = 'project'
    # ------------------------------------------------------------------ #

    def test_create_via_res_model_project_sets_project_id(self):
        """When project_id is absent from vals but res_model is
        'project.project', the create override must back-fill project_id
        from res_id."""
        att = self.env['ir.attachment'].create({
            'name': 'via_res_project.txt',
            'res_model': 'project.project',
            'res_id': self.project.id,
        })
        self.assertEqual(att.project_id.id, self.project.id)

    def test_create_via_res_model_project_sets_attach_to_project(self):
        """When project_id is absent but res_model is 'project.project',
        the create override must set attach_to to 'project'."""
        att = self.env['ir.attachment'].create({
            'name': 'via_res_project_attach.txt',
            'res_model': 'project.project',
            'res_id': self.project.id,
        })
        self.assertEqual(att.attach_to, 'project')

    # ------------------------------------------------------------------ #
    # Branch 4: no task_id key, res_model = 'project.task'
    #   → task_id = res_id, attach_to = 'task'
    # ------------------------------------------------------------------ #

    def test_create_via_res_model_task_sets_task_id(self):
        """When task_id is absent from vals but res_model is 'project.task',
        the create override must back-fill task_id from res_id."""
        att = self.env['ir.attachment'].create({
            'name': 'via_res_task.txt',
            'res_model': 'project.task',
            'res_id': self.task.id,
        })
        self.assertEqual(att.task_id.id, self.task.id)

    def test_create_via_res_model_task_sets_attach_to_task(self):
        """When task_id is absent but res_model is 'project.task', the
        create override must set attach_to to 'task'."""
        att = self.env['ir.attachment'].create({
            'name': 'via_res_task_attach.txt',
            'res_model': 'project.task',
            'res_id': self.task.id,
        })
        self.assertEqual(att.attach_to, 'task')

    def test_create_via_res_model_task_res_id_unchanged(self):
        """When routed through branch 4, res_id must remain the task's
        id and must not be altered by the create override."""
        att = self.env['ir.attachment'].create({
            'name': 'via_res_task_rid.txt',
            'res_model': 'project.task',
            'res_id': self.task.id,
        })
        self.assertEqual(att.res_id, self.task.id)

    # ------------------------------------------------------------------ #
    # Unrelated res_model — no branch matches, no mutation
    # ------------------------------------------------------------------ #

    def test_create_unrelated_res_model_unchanged(self):
        """When res_model is neither 'project.project' nor 'project.task',
        the create override must not alter res_model or res_id."""
        att = self.env['ir.attachment'].create({
            'name': 'unrelated.txt',
            'res_model': 'res.partner',
            'res_id': self.env.user.partner_id.id,
        })
        self.assertEqual(att.res_model, 'res.partner')
        self.assertEqual(att.res_id, self.env.user.partner_id.id)

    def test_create_unrelated_res_model_no_project_id(self):
        """When res_model is unrelated to project/task, project_id must
        remain empty because no branch in the override sets it."""
        att = self.env['ir.attachment'].create({
            'name': 'unrelated_no_proj.txt',
            'res_model': 'res.partner',
            'res_id': self.env.user.partner_id.id,
        })
        self.assertFalse(att.project_id)

    def test_create_unrelated_res_model_no_task_id(self):
        """When res_model is unrelated to project/task, task_id must
        remain empty because no branch in the override sets it."""
        att = self.env['ir.attachment'].create({
            'name': 'unrelated_no_task.txt',
            'res_model': 'res.partner',
            'res_id': self.env.user.partner_id.id,
        })
        self.assertFalse(att.task_id)

    # ------------------------------------------------------------------ #
    # create_multi: multiple vals in one call
    # ------------------------------------------------------------------ #

    def test_create_multi_both_branches(self):
        """Verify that create_multi handles mixed vals correctly: one record
        with only project_id (branch 1) and one with both project_id and
        task_id (branch 2), each getting the right res_model and res_id."""
        attachments = self.env['ir.attachment'].create([
            {
                'name': 'multi_proj.txt',
                'project_id': self.project.id,
                'task_id': False,
            },
            {
                'name': 'multi_task.txt',
                'project_id': self.project.id,
                'task_id': self.task.id,
            },
        ])
        self.assertEqual(len(attachments), 2)
        proj_att = attachments.filtered(lambda a: a.name == 'multi_proj.txt')
        task_att = attachments.filtered(lambda a: a.name == 'multi_task.txt')
        self.assertEqual(proj_att.res_model, 'project.project')
        self.assertEqual(proj_att.res_id, self.project.id)
        self.assertEqual(task_att.res_model, 'project.task')
        self.assertEqual(task_att.res_id, self.task.id)

    def test_create_multi_via_res_model(self):
        """Verify that create_multi correctly handles branch 3 and branch 4
        in a single call: res_model-based routing must back-fill project_id
        and task_id and set attach_to accordingly."""
        attachments = self.env['ir.attachment'].create([
            {
                'name': 'multi_via_proj.txt',
                'res_model': 'project.project',
                'res_id': self.project.id,
            },
            {
                'name': 'multi_via_task.txt',
                'res_model': 'project.task',
                'res_id': self.task.id,
            },
        ])
        proj_att = attachments.filtered(lambda a: a.name == 'multi_via_proj.txt')
        task_att = attachments.filtered(lambda a: a.name == 'multi_via_task.txt')
        self.assertEqual(proj_att.project_id.id, self.project.id)
        self.assertEqual(proj_att.attach_to, 'project')
        self.assertEqual(task_att.task_id.id, self.task.id)
        self.assertEqual(task_att.attach_to, 'task')

    # ------------------------------------------------------------------ #
    # attach_to selection values
    # ------------------------------------------------------------------ #

    def test_attach_to_explicit_task(self):
        """When an attachment is created via res_model='project.task',
        attach_to must be set to 'task' by the create override."""
        att = self.env['ir.attachment'].create({
            'name': 'explicit_task.txt',
            'res_model': 'project.task',
            'res_id': self.task.id,
        })
        self.assertEqual(att.attach_to, 'task')

    def test_attach_to_explicit_project(self):
        """When an attachment is created via res_model='project.project',
        attach_to must be set to 'project' by the create override."""
        att = self.env['ir.attachment'].create({
            'name': 'explicit_proj.txt',
            'res_model': 'project.project',
            'res_id': self.project.id,
        })
        self.assertEqual(att.attach_to, 'project')