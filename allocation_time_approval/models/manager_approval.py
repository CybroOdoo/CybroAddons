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
from odoo import fields, models


class ManagerApproval(models.Model):
    """Model for managing project task time allocation approvals."""

    _name = 'manager.approval'
    _description = "Manager Approval"

    task_id = fields.Many2one(
        "project.task",
        string="Task",
        required=True,
        ondelete="cascade",
        help="Corresponding project task for approval",
    )
    project_id = fields.Many2one(
        "project.project",
        string="Project",
        help="Corresponding project",
    )
    user_ids = fields.Many2many(
        'res.users',
        string="Assignees",
        required=True,
        help="Assigned users for the task",
    )
    planned_hours = fields.Float(
        string="Allocated Hours",
        help="Planned allocation time requested for assignees",
    )
    is_button_view = fields.Boolean(
        string="Approved",
        help="Indicates whether the allocation request has been approved",
    )
    is_button_view_cancel = fields.Boolean(
        string="Cancelled",
        help="Indicates whether the allocation request has been cancelled",
    )

    def action_approve(self):
        """Approve allocated hours and transition tasks to In Progress stage."""
        for record in self:
            if not record.task_id:
                continue
            progress_stage = record.task_id._get_project_stage(
                "project.project_stage_1"
            )
            vals = {
                'allocated_hours': record.planned_hours,
                'user_ids': [(6, 0, record.user_ids.ids)],
                'manager_approval_id': record.id,
            }
            if record.project_id:
                vals['project_id'] = record.project_id.id
            if progress_stage:
                vals['stage_id'] = progress_stage.id
            record.task_id.write(vals)

            record.write({
                'is_button_view': True,
                'is_button_view_cancel': False,
            })

    def action_manager_cancel(self):
        """Cancel allocated hours request and transition tasks to Cancelled stage."""
        for record in self:
            if not record.task_id:
                continue
            cancel_stage = record.task_id._get_project_stage(
                "project.project_stage_3"
            )
            vals = {}
            if cancel_stage:
                vals['stage_id'] = cancel_stage.id
            if vals:
                record.task_id.write(vals)
            record.task_id._update_personal_stages('cancel')

            record.write({
                'is_button_view_cancel': True,
                'is_button_view': False,
            })
