# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Farhana Jahan PT(odoo@cybrosys.com)
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
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    """ Inherit project,so we are adding certain boolean
     field for defining stages. """
    _inherit = 'project.task'

    new_stage = fields.Boolean(string="New",
                               help="Boolean to visible manager approve",
                               compute="_compute_new_stage")
    to_approve_stage = fields.Boolean(string="To approve",
                                      compute="_compute_to_approve_stage",
                                      help="Boolean to change to approve")
    to_progress_stage = fields.Boolean(string="Task Done",
                                       compute="_compute_to_progress_stage",
                                       help="Boolean to progress stage")
    manager_approval_id = fields.Many2one("manager.approval",
                                          string="Manager Approval",
                                          help="Manager Approval")
    task_create_boolean = fields.Boolean(string="Task Create Boolean",
                                         help="Task Create Boolean",
                                         default=True)

    @api.depends('stage_id')
    def _compute_new_stage(self):
        """Searches for 'New' stage from project.task.type,
        When project_task on 'New' stage then New boolean field got True"""
        for rec in self:
            rec.new_stage = True if rec.stage_id.id == rec.env.ref(
                "project.project_stage_0").id else False

    @api.depends('stage_id')
    def _compute_to_approve_stage(self):
        """Searches for 'To Approve' stage from project.task.type,
        When project_task on 'To Approve' stage then To Approve
        boolean field got True"""
        for rec in self:
            rec.to_approve_stage = True if rec.stage_id.id == rec.env.ref(
                "allocation_time_approval.task_type_to_approve").id else False

    @api.depends('stage_id')
    def _compute_to_progress_stage(self):
        """Searches for 'In Progress' stage from project.task.type,
        When project_task on 'In Progress' stage then In Progress
        boolean field got True"""
        for rec in self:
            rec.to_progress_stage = True if rec.stage_id.id == rec.env.ref(
                "project.project_stage_1").id else False

    def action_approval(self):
        """ When click on 'Manager Approval' button the
        datas are created in manager_approval module,
        and the stage become 'To Approve'"""
        self.task_create_boolean = False
        self.write({'stage_id': self.env.ref(
            "allocation_time_approval.task_type_to_approve").id})
        if not self.task_create_boolean:
            users = [rec for rec in self.user_ids.ids]
            self.env['manager.approval'].create({
                'task': self.name,
                'project_id': self.project_id.id,
                'user_ids': users,
                'planned_hours': self.planned_hours,
                'task_id': self.id
            })
            self.planned_hours = 0

    def action_done(self):
        """ When click on 'Done' the stage become 'Done'"""
        self.write({'stage_id': self.env.ref('project.project_stage_2').id})
        self.manager_approval_id.button_view_boolean = True
        self.manager_approval_id.button_view_boolean_cancel = True

    def action_cancel(self):
        """ When click on 'Cancel' the stage become 'Cancel'"""
        self.write({'stage_id': self.env.ref("project.project_stage_3").id})
        self.manager_approval_id.button_view_boolean = True
        self.manager_approval_id.button_view_boolean_cancel = True

    def write(self, values):
        """ Function for change stage only for Manager"""
        current_stage = self.stage_id.name
        if 'stage_id' in values:
            new_state = values.get('stage_id')
            if (current_stage == self.env.ref(
                    "allocation_time_approval.task_type_to_approve").name) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                if new_state in (self.env.ref("project.project_stage_0").id,
                                 self.env.ref("project.project_stage_1").id,
                                 self.env.ref("project.project_stage_2").id,
                                 self.env.ref("project.project_stage_3").id):
                    raise ValidationError(_(
                        "Only Managers can perform this move!"))
            if (current_stage == self.env.ref(
                    "project.project_stage_0").name) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                if new_state != self.env.ref(
                        "allocation_time_approval.task_type_to_approve").id:
                    raise ValidationError(_(
                        "Only Managers can perform this move!"))
            if (current_stage == self.env.ref(
                    "project.project_stage_2").name) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                if new_state in (self.env.ref(
                        "allocation_time_approval.task_type_to_approve").id,
                                 self.env.ref("project.project_stage_0").id,
                                 self.env.ref("project.project_stage_3").id):
                    raise ValidationError(_(
                        "Only Managers can perform this move!"))
            if (current_stage == self.env.ref(
                    "project.project_stage_1").name) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                if new_state in (self.env.ref("project.project_stage_0").id,
                                 self.env.ref(
                                     "allocation_time_approval.task_type_to_approve").id):
                    raise ValidationError(_(
                        "Only Managers can perform this move!"))
            if (current_stage == self.env.ref(
                    "project.project_stage_3").name) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                if new_state in (self.env.ref('project.project_stage_0').id,
                                 self.env.ref('project.project_stage_1').id,
                                 self.env.ref('project.project_stage_2').id,
                                 self.env.ref(
                                     'allocation_time_approval.task_type_to_approve').id):
                    raise ValidationError(_(
                        "Only Managers can perform this move!"))
            if (new_state == self.env.ref("project.project_stage_0").id) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                raise ValidationError(_("Only Managers can perform this move!"))
            if new_state == self.env.ref(
                    "allocation_time_approval.task_type_to_approve").id:
                if self.task_create_boolean:
                    users = [rec for rec in self.user_ids.ids]
                    self.env['manager.approval'].create({
                        'task': self.name,
                        'project_id': self.project_id.id,
                        'user_ids': users,
                        'planned_hours': self.planned_hours,
                        'task_id': self.id
                    })
                    self.planned_hours = 0
            if (current_stage == self.env.ref(
                    "project.project_stage_2").name) and (
                    self.env.user.has_group('project.group_project_manager')):
                if (new_state == self.env.ref(
                        "allocation_time_approval.task_type_to_approve").id):
                    raise ValidationError(_("You can't move this..!"))
            if (current_stage == self.env.ref(
                    "allocation_time_approval.task_type_to_approve").name) and (
                    self.env.user.has_group('project.group_project_manager')):
                if (new_state == self.env.ref(
                        "project.project_stage_0").id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.unlink()
                if (new_state == self.env.ref(
                        "project.project_stage_2").id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.unlink()
                if (new_state == self.env.ref(
                        "project.project_stage_3").id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.button_view_boolean_cancel = True
                if (new_state == self.env.ref(
                        "project.project_stage_1").id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.button_view_boolean = True
            if current_stage == self.env.ref("project.project_stage_1").name:
                if (new_state == self.env.ref(
                        "project.project_stage_2").id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.button_view_boolean = True
                    task_name.button_view_boolean_cancel = True
            if current_stage == self.env.ref("project.project_stage_1").name:
                if (new_state == self.env.ref(
                        "project.project_stage_3").id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.button_view_boolean = True
                    task_name.button_view_boolean_cancel = True
        return super(ProjectTask, self).write(values)
