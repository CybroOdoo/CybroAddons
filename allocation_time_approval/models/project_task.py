# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.exceptions import ValidationError, UserError


class ProjectTask(models.Model):
    """ Inherit project,so we are adding certain boolean
     field for defining stages. """
    _inherit = 'project.task'

    is_new_stage = fields.Boolean(string="New",
                                  help="Boolean to visible manager approve",
                                  compute="_compute_is_new_stage")
    is_approve_stage = fields.Boolean(string="To approve",
                                      compute="_compute_is_approve_stage",
                                      help="Boolean to change to approve")
    is_progress_stage = fields.Boolean(string="Task Done",
                                       compute="_compute_is_progress_stage",
                                       help="Boolean to progress stage")
    manager_approval_id = fields.Many2one("manager.approval",
                                          string="Manager Approval",
                                          help="Manager Approval")
    is_create_task = fields.Boolean(string="Task Create Boolean",
                                    help="Task Create Boolean",
                                    default=True)

    def _get_to_approve_stage(self):
        stage = self.env.ref('allocation_time_approval.task_type_to_approve', raise_if_not_found=False)
        if not stage:
            stage = self.env['project.task.type'].search([('name', '=', 'To Approve')], limit=1)
        return stage or self.env['project.task.type']

    def _get_project_stage(self, stage_xml_id):
        stage = self.env.ref(stage_xml_id, raise_if_not_found=False)
        if not stage:
            name_map = {
                'project.project_stage_0': 'New',
                'project.project_stage_1': 'In Progress',
                'project.project_stage_2': 'Done',
                'project.project_stage_3': 'Cancelled',
            }
            fallback_name = name_map.get(stage_xml_id)
            if fallback_name:
                stage = self.env['project.task.type'].search([('name', '=', fallback_name)], limit=1)
        return stage or self.env['project.task.type']

    @api.depends('stage_id')
    def _compute_is_new_stage(self):
        """Set `is_new_stage` to True if the task is not in predefined stages
        (To Approve, In Progress, Done, Cancel).Otherwise, mark it as False."""
        for rec in self:
            # Flexible check for initial stages.
            # If the task is NOT in a specialized stage (To Approve, In
            # Progress, Done, Cancel),
            # we treat it as being in a 'New' or 'Draft' stage.
            approve_stage = rec._get_to_approve_stage()
            progress_stage = rec._get_project_stage("project.project_stage_1")
            done_stage = rec._get_project_stage("project.project_stage_2")
            cancel_stage = rec._get_project_stage("project.project_stage_3")

            excluded_stages = [s.id for s in
                               [approve_stage, progress_stage, done_stage,
                                cancel_stage] if s]
            rec.is_new_stage = rec.stage_id.id not in excluded_stages

    @api.depends('stage_id')
    def _compute_is_approve_stage(self):
        """Searches for 'To Approve' stage from project.task.type,
        When project_task on 'To Approve' stage then To Approve
        boolean field got True"""
        for rec in self:
            rec.is_approve_stage = bool(rec.stage_id) and rec.stage_id.id == rec._get_to_approve_stage().id

    @api.depends('stage_id')
    def _compute_is_progress_stage(self):
        """Searches for 'In Progress' stage from project.task.type,
        When project_task on 'In Progress' stage then In Progress
        boolean field got True"""
        for rec in self:
            rec.is_progress_stage = bool(rec.stage_id) and rec.stage_id.id == rec._get_project_stage(
                "project.project_stage_1").id

    def action_approval(self):
        """ When click on 'Manager Approval' button the
        datas are created in manager_approval module,
        and the stage become 'To Approve'"""
        self.is_create_task = False
        
        # Check whether there is a to approve stage
        stage = self.env.ref('allocation_time_approval.task_type_to_approve', raise_if_not_found=False)
        if not stage:
            stage = self.env['project.task.type'].search([('name', '=', 'To Approve')], limit=1)
            
        if not stage:
            # Create it with current project id
            stage_vals = {
                'name': 'To Approve',
                'sequence': 1,
                'fold': True,
            }
            if self.project_id:
                stage_vals['project_ids'] = [(4, self.project_id.id)]
            stage = self.env['project.task.type'].create(stage_vals)
            
            # Register XML ID so existing references don't break
            self.env['ir.model.data']._update_xmlids([{
                'xml_id': 'allocation_time_approval.task_type_to_approve',
                'record': stage,
                'noupdate': True,
            }])
        else:
            # Stage exists. If not linked to this project, add the project to the stage
            if self.project_id and self.project_id not in stage.project_ids:
                stage.write({'project_ids': [(4, self.project_id.id)]})

        self.write({
            'stage_id': stage.id,
        })
        if not self.is_create_task:
            users = [rec for rec in self.user_ids.ids]
            self.env['manager.approval'].create({
                'task': self.name,
                'project_id': self.project_id.id,
                'user_ids': users,
                'planned_hours': self.allocated_hours,
                'task_id': self.id
            })
            self.allocated_hours = 0

    def action_done(self):
        """ When click on 'Done' the stage become 'Done' """

        for task in self:
            allocated = task.allocated_hours or 0.0
            spent = task.effective_hours or 0.0

            if spent > allocated:
                if not self.env.user.has_group('project.group_project_manager'):
                    raise UserError(_(
                        "You have exceeded the allocated hours.\n"
                        "Only a Project Manager can mark this task as Done."
                    ))

            task.sudo().write({
                'stage_id': self._get_project_stage('project.project_stage_2').id,
            })
            task._update_personal_stages('done')

    def action_cancel(self):
        """ When click on 'Cancel' the stage become 'Cancel'"""
        self.sudo().write({
            'stage_id': self._get_project_stage("project.project_stage_3").id,
        })
        self._update_personal_stages('cancel')

    def _update_personal_stages(self, target_type):
        """ Update personal stages for all assigned users.
        target_type can be 'done' or 'cancel' """
        for task in self:
            # If the task has no assignees, add the current user as an assignee
            # so it appears in their "My Tasks" view.
            if not task.user_ids and self.env.user:
                task.sudo().write({'user_ids': [(4, self.env.user.id)]})

            for user in task.user_ids:
                personal_stage = self.env[
                    'project.task.stage.personal'].sudo().search([
                    ('task_id', '=', task.id),
                    ('user_id', '=', user.id)
                ], limit=1)
                # If personal_stage doesn't exist yet, we can create it
                if not personal_stage and user.id == self.env.uid:
                    # Creating a personal stage record often happens
                    # automatically in Odoo,
                    # but we can force it if needed.
                    personal_stage = self.env[
                        'project.task.stage.personal'].sudo().create({
                        'task_id': task.id,
                        'user_id': user.id,
                    })

                if personal_stage:
                    # Find the user's personal stage that matches the
                    # target_type
                    # We search all personal stages for this user
                    stages = self.env['project.task.type'].sudo().search(
                        [('user_id', '=', user.id),],
                        order='sequence desc')

                    target_stage = False
                    if target_type == 'done':
                        # Look for 'Done' in name, or folded stage with high
                        # sequence (default is 6)
                        target_stage = stages.filtered(
                            lambda s: 'Done' in s.name or (
                                        s.fold and s.sequence >= 6))[:1]
                    else:
                        # Look for 'Cancel' in name, or folded stage with high
                        # sequence (default is 7)
                        target_stage = stages.filtered(
                            lambda s: 'Cancel' in s.name or (
                                        s.fold and s.sequence >= 7))[:1]

                    if not target_stage and stages:
                        # Fallback to the highest sequence stage among folded
                        # ones, or just the last stage
                        folded_stages = stages.filtered(lambda s: s.fold)
                        target_stage = folded_stages[:1] or stages[:1]

                    if target_stage:
                        personal_stage.write({'stage_id': target_stage.id})

    def write(self, values):
        """ Function for change stage only for Manager"""
        current_stage = self.stage_id.name
        if 'stage_id' in values:
            new_state = values.get('stage_id')
            
            # Fetch all stages using safe helper methods
            to_approve_stage = self._get_to_approve_stage()
            stage_0 = self._get_project_stage("project.project_stage_0")
            stage_1 = self._get_project_stage("project.project_stage_1")
            stage_2 = self._get_project_stage("project.project_stage_2")
            stage_3 = self._get_project_stage("project.project_stage_3")

            if (current_stage == to_approve_stage.name) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                if new_state in (stage_0.id, stage_1.id, stage_2.id, stage_3.id):
                    raise ValidationError(_(
                        "Only Managers can perform this move!"))
            if (current_stage == stage_0.name) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                if new_state != to_approve_stage.id:
                    raise ValidationError(_(
                        "Only Managers can perform this move!"))
            if (current_stage == stage_2.name) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                if new_state in (to_approve_stage.id, stage_0.id, stage_3.id):
                    raise ValidationError(_(
                        "Only Managers can perform this move!"))
            if (current_stage == stage_1.name) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                if new_state in (stage_0.id, to_approve_stage.id):
                    raise ValidationError(_(
                        "Only Managers can perform this move!"))
            if (current_stage == stage_3.name) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                if new_state in (stage_0.id, stage_1.id, stage_2.id, to_approve_stage.id):
                    raise ValidationError(_(
                        "Only Managers can perform this move!"))
            if (new_state == stage_0.id) and (
                    not self.env.user.has_group(
                        'project.group_project_manager')):
                raise ValidationError(_("Only Managers can perform this move!"))
            if new_state == to_approve_stage.id:
                if self.is_create_task:
                    users = [rec for rec in self.user_ids.ids]
                    self.env['manager.approval'].create({
                        'task': self.name,
                        'project_id': self.project_id.id,
                        'user_ids': users,
                        'planned_hours': self.allocated_hours,
                        'task_id': self.id
                    })
                    self.allocated_hours = 0
            if (current_stage == stage_2.name) and (
                    self.env.user.has_group('project.group_project_manager')):
                if (new_state == to_approve_stage.id):
                    raise ValidationError(_("You can't move this..!"))
            if (current_stage == to_approve_stage.name) and (
                    self.env.user.has_group('project.group_project_manager')):
                if (new_state == stage_0.id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.unlink()
                if (new_state == stage_2.id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.unlink()
                if (new_state == stage_3.id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.is_button_view_cancel = True
                if (new_state == stage_1.id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.is_button_view = True
            if current_stage == stage_1.name:
                if (new_state == stage_2.id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.is_button_view = True
                    task_name.is_button_view_cancel = True
            if current_stage == stage_1.name:
                if (new_state == stage_3.id):
                    task_name = self.env["manager.approval"].search(
                        [('task', '=', self.name)])
                    task_name.is_button_view = True
                    task_name.is_button_view_cancel = True
        result = super(ProjectTask, self).write(values)

        if 'stage_id' in values:
            new_state_id = values.get('stage_id')
            new_stage = self.env['project.task.type'].sudo().browse(
                new_state_id)
            done_stage = self._get_project_stage("project.project_stage_2")
            cancel_stage = self._get_project_stage("project.project_stage_3")

            if (done_stage and new_state_id == done_stage.id) or (
                    new_stage.name and 'Done' in new_stage.name):
                self._update_personal_stages('done')
            elif (cancel_stage and new_state_id == cancel_stage.id) or (
                    new_stage.name and 'Cancel' in new_stage.name):
                self._update_personal_stages('cancel')

        return result
