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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    """
    Inherit project.task to add stages and manager approval workflow
    for task time allocation.
    """
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
    is_administrator = fields.Boolean(compute='_compute_is_administrator')

    def _compute_is_administrator(self):
        for rec in self:
            rec.is_administrator = self.env.user.has_group('base.group_system') or self.env.user.has_group('project.group_project_manager')

    @api.depends('stage_id', 'project_id.type_ids')
    def _compute_new_stage(self):
        """
        Computes the 'new_stage' boolean field based on the task's stage.
        Sets to True if the task is in the default 'New' stage of its project.
        """
        for rec in self:
            if not rec.stage_id:
                rec.new_stage = False
                continue
            is_new = False
            if rec.project_id and rec.project_id.type_ids:
                first_stage = rec.project_id.type_ids.sorted('sequence')[0]
                if rec.stage_id.id == first_stage.id:
                    is_new = True
            if not is_new:
                try:
                    stage = rec.env.ref("project.project_stage_0", raise_if_not_found=False)
                except ValueError:
                    stage = None
                if not stage:
                    stage = rec.env['project.task.type'].search([], order='sequence asc', limit=1)
                if stage and rec.stage_id.id == stage.id:
                    is_new = True
            rec.new_stage = is_new

    def action_timer_start(self):
        """
        Extends the action_timer_start to prevent starting the timer
        if the task is in 'New' or 'To Approve' stages.
        """
        try:
            stage_0 = self.env.ref("project.project_stage_0", raise_if_not_found=False)
        except ValueError:
            stage_0 = None
        if not stage_0:
            stage_0 = self.env['project.task.type'].search([], order='sequence asc', limit=1)
        try:
            stage_to_approve = self.env.ref("allocation_time_approval.task_type_to_approve", raise_if_not_found=False)
        except ValueError:
            stage_to_approve = None
        if (not getattr(self.user_timer_id, 'timer_start', False) and getattr(self, 'display_timesheet_timer', False) and
                (not stage_0 or self.stage_id.id != stage_0.id) and
                (not stage_to_approve or self.stage_id.id != stage_to_approve.id)):
            super(ProjectTask, self).action_timer_start()

    @api.depends('stage_id')
    def _compute_to_approve_stage(self):
        """
        Computes the 'to_approve_stage' boolean field.
        Sets to True if the task is in the 'To Approve' stage.
        """
        for rec in self:
            try:
                stage = rec.env.ref("allocation_time_approval.task_type_to_approve", raise_if_not_found=False)
            except ValueError:
                stage = None
            rec.to_approve_stage = True if stage and rec.stage_id.id == stage.id else False

    @api.depends('stage_id', 'project_id.type_ids')
    def _compute_to_progress_stage(self):
        """
        Computes the 'to_progress_stage' boolean field.
        Sets to True if the task is in the second sequence stage (In Progress stage).
        """
        for rec in self:
            is_progress = False
            if rec.project_id and rec.project_id.type_ids:
                sorted_stages = rec.project_id.type_ids.sorted('sequence')
                if len(sorted_stages) > 1:
                    is_progress = (rec.stage_id.id == sorted_stages[1].id)
                elif sorted_stages:
                    is_progress = (rec.stage_id.id == sorted_stages[0].id)
            if not is_progress:
                try:
                    stage = rec.env.ref("project.project_stage_1", raise_if_not_found=False)
                except ValueError:
                    stage = None
                if stage and rec.stage_id.id == stage.id:
                    is_progress = True
            rec.to_progress_stage = is_progress

    def action_approval(self):
        """
        Moves the task to the 'To Approve' stage and creates a
        manager approval record for the task's time allocation.
        """
        self.task_create_boolean = False
        
        # Ensure the 'To Approve' stage is a global stage (accessible to all)
        # by clearing any accidentally assigned user_id (personal stage).
        try:
            stage = self.env.ref("allocation_time_approval.task_type_to_approve", raise_if_not_found=False).sudo()
        except ValueError:
            stage = None
        if stage and stage.user_id:
            stage.user_id = False

        if stage:
            self.write({'stage_id': stage.id})
        if not self.task_create_boolean:
            users = [rec for rec in self.user_ids.ids]
            approval = self.manager_approval_id or self.env['manager.approval'].search([('task_id', '=', self.id)], limit=1)
            vals = {
                'task': self.name,
                'project_id': self.project_id.id,
                'user_ids': [(6, 0, users)],
                'planned_hours': self.allocated_hours,
                'task_id': self.id,
                'button_view_boolean': False,
                'button_view_boolean_cancel': False,
            }
            if approval:
                approval.sudo().write(vals)
            else:
                approval = self.env['manager.approval'].sudo().create(vals)
                self.manager_approval_id = approval.id
            self.allocated_hours = 0

    def action_done(self):
        """
        Moves the task to the 'Done' stage and updates the
        corresponding manager approval record.
        """
        stage_id = False
        if self.project_id and self.project_id.type_ids:
            stages = self.project_id.type_ids.sorted('sequence')
            # 1. Folded stage that is not canceled
            folded = stages.filtered(lambda s: s.fold and 'cancel' not in s.name.lower())
            if folded:
                stage_id = folded[0].id
            # 2. Stage with name containing done/complete/finish
            if not stage_id:
                named = stages.filtered(lambda s: any(kw in s.name.lower() for kw in ('done', 'complete', 'finish', 'termin')))
                if named:
                    stage_id = named[0].id
            # 3. Sequence fallback: 3rd stage if >=3 stages exist, else last stage
            if not stage_id:
                if len(stages) >= 3:
                    stage_id = stages[2].id
                elif stages:
                    stage_id = stages[-1].id

        if not stage_id:
            try:
                stage = self.env.ref('project.project_stage_2', raise_if_not_found=False)
                stage_id = stage.id if stage else False
            except ValueError:
                stage_id = False
        if stage_id:
            self.sudo().write({'stage_id': stage_id})
        self.manager_approval_id.sudo().button_view_boolean = True
        self.manager_approval_id.sudo().button_view_boolean_cancel = True

    def action_cancel(self):
        """
        Moves the task to the 'Cancelled' stage and updates the
        corresponding manager approval record.
        """
        stage_id = False
        if self.project_id and self.project_id.type_ids:
            stages = self.project_id.type_ids.sorted('sequence')
            # 1. Name match for cancel/annul
            cancel_stage = stages.filtered(lambda s: 'cancel' in s.name.lower() or 'annul' in s.name.lower())
            if cancel_stage:
                stage_id = cancel_stage[0].id
            # 2. 4th sequence stage if 4+ stages exist
            elif len(stages) >= 4:
                stage_id = stages[-1].id
            # 3. Last folded stage if multiple folded stages exist
            else:
                folded = stages.filtered(lambda s: s.fold)
                if len(folded) > 1:
                    stage_id = folded[-1].id

        if not stage_id:
            try:
                stage = self.env.ref('project.project_stage_3', raise_if_not_found=False)
                stage_id = stage.id if stage else False
            except ValueError:
                stage_id = False
        if stage_id:
            self.sudo().write({'stage_id': stage_id})
        self.manager_approval_id.sudo().button_view_boolean = True
        self.manager_approval_id.sudo().button_view_boolean_cancel = True


    def write(self, values):
        """
        Extends the write method to enforce stage transition restrictions:
        Normal users can ONLY move tasks to the 'To Approve' stage.
        All other stage changes require Project Manager access.
        """
        if 'stage_id' in values:
            new_state = values.get('stage_id')
            is_manager = self.env.user.has_group('project.group_project_manager') or self.env.su
            
            try:
                stage_to_approve = self.env.ref("allocation_time_approval.task_type_to_approve", raise_if_not_found=False)
            except ValueError:
                stage_to_approve = None
            stage_to_approve_id = stage_to_approve.id if stage_to_approve else False

            # Restrict stage changes for normal users
            if not is_manager:
                if new_state != stage_to_approve_id:
                    raise ValidationError(_("Only Managers can change task stages!"))
                
            if new_state == stage_to_approve_id:
                for task in self:
                    if task.task_create_boolean:
                        users = [rec for rec in task.user_ids.ids]
                        approval = task.manager_approval_id or task.env['manager.approval'].search([('task_id', '=', task.id)], limit=1)
                        vals = {
                            'task': task.name,
                            'project_id': task.project_id.id,
                            'user_ids': [(6, 0, users)],
                            'planned_hours': task.allocated_hours,
                            'task_id': task.id,
                            'button_view_boolean': False,
                            'button_view_boolean_cancel': False,
                        }
                        if approval:
                            approval.sudo().write(vals)
                        else:
                            approval = task.env['manager.approval'].sudo().create(vals)
                            task.manager_approval_id = approval.id
                        task.allocated_hours = 0
            
            # Update associated manager.approval record status if available
            for task in self:
                if task.manager_approval_id:
                    approval = task.manager_approval_id.sudo()
                    if new_state == stage_to_approve_id:
                        pass
                    else:
                        approval.button_view_boolean = True
                        approval.button_view_boolean_cancel = True
            
        return super(ProjectTask, self).write(values)

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type == 'form':
            from lxml import etree
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//button[@name='action_timer_start']"):
                modifiers = node.get('invisible', '')
                if modifiers:
                    node.set('invisible', f"({modifiers}) or new_stage == True")
                else:
                    node.set('invisible', "new_stage == True")
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
