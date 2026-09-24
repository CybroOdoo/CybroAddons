# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil Ashok(odoo@cybrosys.com)
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
from odoo import fields, models


class ManagerApproval(models.Model):
    """
    Model to manage manager approval for task time allocation.
    Stores task details, assigned users, and planned hours for review.
    """
    _name = 'manager.approval'
    _description = "Manager Approval"

    task = fields.Char(string="Task", help="Task name for project")
    project_id = fields.Many2one("project.project", string="Project",
                                 help="Corresponding project name")
    user_ids = fields.Many2many('res.users', string="Assignees",
                                help="Corresponding assignees name",
                                required=True)
    planned_hours = fields.Float(string="Allocated Hours",
                                 help="Allocation time for assignees")
    button_view_boolean = fields.Boolean(string="Button view",
                                         help="Button for approve button")
    button_view_boolean_cancel = fields.Boolean(string="Cancel Button",
                                                help="Button for cancel")
    task_id = fields.Many2one("project.task", string="Project Task",
                              help="Getting corresponding task")

    def write(self, vals):
        """
        Sync changes made in the manager approval record to the linked project task.
        """
        res = super(ManagerApproval, self).write(vals)
        for record in self:
            task_vals = {}
            if 'task' in vals:
                task_vals['name'] = record.task
            if 'project_id' in vals:
                task_vals['project_id'] = record.project_id.id
            if 'user_ids' in vals:
                task_vals['user_ids'] = [(6, 0, record.user_ids.ids)]
            if 'planned_hours' in vals:
                task_vals['allocated_hours'] = record.planned_hours
            
            if task_vals and record.task_id:
                record.task_id.write(task_vals)
        return res

    def action_approve(self):
        """
        Approves the time allocation request.
        Updates the linked project task with the approved details,
        moves it to the second sequence stage (In Progress), and hides the approve button.
        """
        users = [rec for rec in self.user_ids.ids]
        stage_id = False
        if self.project_id and self.project_id.type_ids:
            sorted_stages = self.project_id.type_ids.sorted('sequence')
            if len(sorted_stages) > 1:
                stage_id = sorted_stages[1].id
            elif sorted_stages:
                stage_id = sorted_stages[0].id
        if not stage_id:
            try:
                stage_1 = self.env.ref("project.project_stage_1", raise_if_not_found=False)
                stage_id = stage_1.id if stage_1 else False
            except ValueError:
                stage_id = False
        if not stage_id:
            stage_rec = self.env['project.task.type'].search([], order='sequence asc', limit=2)
            if len(stage_rec) > 1:
                stage_id = stage_rec[1].id

        vals = {
            'name': self.task,
            'project_id': self.project_id.id,
            'user_ids': [(6, 0, users)],
            'allocated_hours': self.planned_hours,
            'manager_approval_id': self.id
        }
        if stage_id:
            vals['stage_id'] = stage_id

        self.task_id.sudo().write(vals)
        self.button_view_boolean = True
        self.button_view_boolean_cancel = False

    def action_manager_cancel(self):
        """
        Cancels the time allocation request.
        Moves the linked project task to the 'Cancelled' stage,
        pauses the timer if active, and hides the cancel button.
        """
        stage_id = False
        if self.project_id and self.project_id.type_ids:
            stages = self.project_id.type_ids.sorted('sequence')
            # 1. Search for cancel/annul in stage name
            cancel_stage = stages.filtered(lambda s: 'cancel' in s.name.lower() or 'annul' in s.name.lower())
            if cancel_stage:
                stage_id = cancel_stage[0].id
            # 2. If 4 or more stages, the last stage is Canceled
            elif len(stages) >= 4:
                stage_id = stages[-1].id
            # 3. If multiple folded stages exist, pick the last folded stage
            else:
                folded = stages.filtered(lambda s: s.fold)
                if len(folded) > 1:
                    stage_id = folded[-1].id

        if not stage_id:
            try:
                stage_3 = self.env.ref("project.project_stage_3", raise_if_not_found=False)
                stage_id = stage_3.id if stage_3 else False
            except ValueError:
                stage_id = False
        if not stage_id:
            stage_rec = self.env['project.task.type'].search([('name', 'ilike', 'cancel')], limit=1)
            if stage_rec:
                stage_id = stage_rec.id

        if stage_id:
            self.task_id.sudo().write({'stage_id': stage_id})
        if hasattr(self.task_id, 'action_timer_pause'):
            self.task_id.action_timer_pause()
        self.button_view_boolean_cancel = True
        self.button_view_boolean = False
