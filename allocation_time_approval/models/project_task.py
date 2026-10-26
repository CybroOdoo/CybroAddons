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
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProjectTask(models.Model):
    """Inherit project.task to add approval workflow fields and logic."""

    _inherit = 'project.task'

    is_new_stage = fields.Boolean(
        string="New Stage",
        compute="_compute_is_new_stage",
        help="Indicates whether the task is in an initial or draft stage",
    )
    is_approve_stage = fields.Boolean(
        string="To Approve Stage",
        compute="_compute_is_approve_stage",
        help="Indicates whether the task is in the To Approve stage",
    )
    is_progress_stage = fields.Boolean(
        string="In Progress Stage",
        compute="_compute_is_progress_stage",
        help="Indicates whether the task is in the In Progress stage",
    )
    manager_approval_id = fields.Many2one(
        "manager.approval",
        string="Manager Approval",
        copy=False,
        help="Linked Manager Approval record",
    )
    is_create_task = fields.Boolean(
        string="Task Create Boolean",
        default=True,
        help="Flag to track initial task creation versus approval flow",
    )

    def _get_to_approve_stage(self):
        """Retrieve the 'To Approve' stage without creating or modifying data."""
        stage = self.env.ref(
            'allocation_time_approval.task_type_to_approve',
            raise_if_not_found=False,
        )
        if not stage:
            project = (
                self.project_id
                if len(self) == 1
                else self.env['project.project']
            )
            if project:
                stage = self.env['project.task.type'].search([
                    ('name', '=', 'To Approve'),
                    ('user_id', '=', False),
                    ('project_ids', 'in', project.ids),
                ], limit=1)
            if not stage:
                stage = self.env['project.task.type'].search([
                    ('name', '=', 'To Approve'),
                    ('user_id', '=', False),
                ], limit=1)
        return stage or self.env['project.task.type']

    def _get_project_stage(self, stage_xml_id):
        """Retrieve project stage safely without creating or modifying data."""
        stage = self.env.ref(stage_xml_id, raise_if_not_found=False)
        if stage:
            return stage

        name_map = {
            'project.project_stage_0': ['New', 'Inbox', 'Draft'],
            'project.project_stage_1': ['In Progress', 'Progress', 'Doing'],
            'project.project_stage_2': ['Done', 'Completed', 'Finished'],
            'project.project_stage_3': ['Cancelled', 'Canceled'],
        }
        candidate_names = name_map.get(stage_xml_id, [])
        if not candidate_names:
            return self.env['project.task.type']

        project = (
            self.project_id
            if len(self) == 1
            else self.env['project.project']
        )

        if project:
            stage = self.env['project.task.type'].search([
                ('name', 'in', candidate_names),
                ('user_id', '=', False),
                ('project_ids', 'in', project.ids),
            ], limit=1)

        if not stage:
            stage = self.env['project.task.type'].search([
                ('name', 'in', candidate_names),
                ('user_id', '=', False),
            ], limit=1)

        return stage or self.env['project.task.type']

    @api.depends('stage_id', 'stage_id.name')
    def _compute_is_new_stage(self):
        """Set `is_new_stage` to True if task is in an initial or draft stage."""
        for task in self:
            if not task.stage_id:
                task.is_new_stage = True
                continue
            stage_name = (task.stage_id.name or '').strip().lower()
            is_specialized = (
                stage_name == 'to approve'
                or 'progress' in stage_name
                or 'doing' in stage_name
                or 'done' in stage_name
                or 'completed' in stage_name
                or 'cancel' in stage_name
            )
            task.is_new_stage = not is_specialized

    @api.depends('stage_id', 'stage_id.name')
    def _compute_is_approve_stage(self):
        """Set `is_approve_stage` to True when task is in To Approve stage."""
        to_approve_ref = self.env.ref(
            'allocation_time_approval.task_type_to_approve',
            raise_if_not_found=False,
        )
        for task in self:
            stage = task.stage_id
            task.is_approve_stage = bool(
                stage and (
                    (to_approve_ref and stage.id == to_approve_ref.id)
                    or (
                        stage.name
                        and stage.name.strip().lower() == 'to approve'
                    )
                )
            )

    @api.depends('stage_id', 'stage_id.name')
    def _compute_is_progress_stage(self):
        """Set `is_progress_stage` to True when task is in In Progress stage."""
        progress_ref = self.env.ref(
            'project.project_stage_1',
            raise_if_not_found=False,
        )
        for task in self:
            stage = task.stage_id
            task.is_progress_stage = bool(
                stage and (
                    (progress_ref and stage.id == progress_ref.id)
                    or (
                        stage.name
                        and any(
                            term in stage.name.strip().lower()
                            for term in ('in progress', 'progress', 'doing')
                        )
                    )
                )
            )

    def action_approval(self):
        """Submit tasks for manager approval."""
        to_approve_stage = self._get_to_approve_stage()
        for task in self:
            task.is_create_task = False
            approval = self.env['manager.approval'].sudo().create({
                'project_id': task.project_id.id,
                'user_ids': [(6, 0, task.user_ids.ids)],
                'planned_hours': task.allocated_hours,
                'task_id': task.id,
            })
            vals = {
                'allocated_hours': 0.0,
                'manager_approval_id': approval.id,
            }
            if to_approve_stage:
                vals['stage_id'] = to_approve_stage.id
            task.write(vals)

    def action_done(self):
        """Mark tasks as Done with overtime check."""
        done_stage = self._get_project_stage('project.project_stage_2')
        is_manager = self.env.user.has_group('project.group_project_manager')

        for task in self:
            allocated = task.allocated_hours or 0.0
            spent = task.effective_hours or 0.0
            if spent > allocated and not is_manager:
                raise UserError(_(
                    "You have exceeded the allocated hours.\n"
                    "Only a Project Manager can mark this task as Done."
                ))

            if done_stage:
                task.sudo().write({'stage_id': done_stage.id})
            task._update_personal_stages('done')

    def action_cancel(self):
        """Mark tasks as Cancelled."""
        cancel_stage = self._get_project_stage("project.project_stage_3")
        for task in self:
            if cancel_stage:
                task.sudo().write({'stage_id': cancel_stage.id})
            task._update_personal_stages('cancel')

    def _update_personal_stages(self, target_type):
        """Update personal stages for assigned users."""
        for task in self:
            if not task.user_ids and self.env.user:
                task.sudo().write({'user_ids': [(4, self.env.user.id)]})

            for user in task.user_ids:
                personal_stage = self.env[
                    'project.task.stage.personal'
                ].sudo().search([
                    ('task_id', '=', task.id),
                    ('user_id', '=', user.id),
                ], limit=1)

                if not personal_stage and user.id == self.env.uid:
                    personal_stage = self.env[
                        'project.task.stage.personal'
                    ].sudo().create({
                        'task_id': task.id,
                        'user_id': user.id,
                    })

                if personal_stage:
                    stages = self.env['project.task.type'].sudo().search(
                        [('user_id', '=', user.id)],
                        order='sequence desc',
                    )
                    target_stage = False
                    if target_type == 'done':
                        target_stage = stages.filtered(
                            lambda s: 'Done' in (s.name or '')
                            or (s.fold and s.sequence >= 6)
                        )[:1]
                    else:
                        target_stage = stages.filtered(
                            lambda s: 'Cancel' in (s.name or '')
                            or (s.fold and s.sequence >= 7)
                        )[:1]

                    if not target_stage and stages:
                        folded_stages = stages.filtered(lambda s: s.fold)
                        target_stage = folded_stages[:1] or stages[:1]

                    if target_stage:
                        personal_stage.write({'stage_id': target_stage.id})

    def write(self, values):
        """Enforce stage transition permissions and synchronize approvals."""
        if 'stage_id' in values:
            new_stage_id = values.get('stage_id')
            to_approve_stage = self._get_to_approve_stage()
            stage_0 = self._get_project_stage("project.project_stage_0")
            stage_1 = self._get_project_stage("project.project_stage_1")
            stage_2 = self._get_project_stage("project.project_stage_2")
            stage_3 = self._get_project_stage("project.project_stage_3")
            is_manager = self.env.user.has_group(
                'project.group_project_manager'
            )

            for task in self:
                current_stage_id = task.stage_id.id

                if not is_manager:
                    if (
                        to_approve_stage
                        and current_stage_id == to_approve_stage.id
                        and new_stage_id in (
                            stage_0.id,
                            stage_1.id,
                            stage_2.id,
                            stage_3.id,
                        )
                    ):
                        raise ValidationError(
                            _("Only Managers can perform this move!")
                        )
                    if (
                        stage_0
                        and current_stage_id == stage_0.id
                        and (
                            not to_approve_stage
                            or new_stage_id != to_approve_stage.id
                        )
                    ):
                        raise ValidationError(
                            _("Only Managers can perform this move!")
                        )
                    if (
                        stage_2
                        and current_stage_id == stage_2.id
                        and new_stage_id in (
                            to_approve_stage.id,
                            stage_0.id,
                            stage_3.id,
                        )
                    ):
                        raise ValidationError(
                            _("Only Managers can perform this move!")
                        )
                    if (
                        stage_1
                        and current_stage_id == stage_1.id
                        and new_stage_id in (
                            stage_0.id,
                            to_approve_stage.id,
                        )
                    ):
                        raise ValidationError(
                            _("Only Managers can perform this move!")
                        )
                    if (
                        stage_3
                        and current_stage_id == stage_3.id
                        and new_stage_id in (
                            stage_0.id,
                            stage_1.id,
                            stage_2.id,
                            to_approve_stage.id,
                        )
                    ):
                        raise ValidationError(
                            _("Only Managers can perform this move!")
                        )
                    if stage_0 and new_stage_id == stage_0.id:
                        raise ValidationError(
                            _("Only Managers can perform this move!")
                        )

                if is_manager:
                    if (
                        stage_2
                        and to_approve_stage
                        and current_stage_id == stage_2.id
                        and new_stage_id == to_approve_stage.id
                    ):
                        raise ValidationError(_(
                            "You cannot move a completed task back to "
                            "the approval stage."
                        ))

                if (
                    to_approve_stage
                    and new_stage_id == to_approve_stage.id
                    and task.is_create_task
                ):
                    approval = self.env['manager.approval'].sudo().create({
                        'project_id': task.project_id.id,
                        'user_ids': [(6, 0, task.user_ids.ids)],
                        'planned_hours': task.allocated_hours,
                        'task_id': task.id,
                    })
                    task.allocated_hours = 0.0
                    task.manager_approval_id = approval.id

                # Synchronize manager.approval state by task_id
                approvals = self.env['manager.approval'].sudo().search(
                    [('task_id', '=', task.id)]
                )
                if (
                    is_manager
                    and to_approve_stage
                    and current_stage_id == to_approve_stage.id
                ):
                    if new_stage_id in (stage_0.id, stage_2.id):
                        approvals.unlink()
                    elif new_stage_id == stage_3.id:
                        approvals.write({'is_button_view_cancel': True})
                    elif new_stage_id == stage_1.id:
                        approvals.write({'is_button_view': True})

                if stage_1 and current_stage_id == stage_1.id:
                    if new_stage_id in (stage_2.id, stage_3.id):
                        approvals.write({
                            'is_button_view': True,
                            'is_button_view_cancel': True,
                        })

        result = super().write(values)

        if 'stage_id' in values:
            new_stage_id = values.get('stage_id')
            new_stage = self.env['project.task.type'].sudo().browse(
                new_stage_id
            )
            done_stage = self._get_project_stage("project.project_stage_2")
            cancel_stage = self._get_project_stage("project.project_stage_3")

            for task in self:
                if (done_stage and new_stage_id == done_stage.id) or (
                    new_stage.name and 'Done' in new_stage.name
                ):
                    task._update_personal_stages('done')
                elif (cancel_stage and new_stage_id == cancel_stage.id) or (
                    new_stage.name and 'Cancel' in new_stage.name
                ):
                    task._update_personal_stages('cancel')

        return result
