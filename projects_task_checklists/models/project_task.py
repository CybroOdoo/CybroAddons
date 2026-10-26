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
from odoo import Command, api, fields, models


class ProjectTask(models.Model):
    """Inherits project.task to add checklist tracking and scheduled dates.

    Fields:
        start_date: Scheduled start datetime for task execution.
        end_date: Scheduled end datetime for task completion.
        progress: Computed completion percentage based on completed checklist items.
        checklist_id: Selected task.checklist template used to populate items.
        checklist_line_ids: One2many lines of checklist.item.line associated with the task.
    """
    _inherit = 'project.task'

    start_date = fields.Datetime(
        string="Scheduled Start Date",
        help="Scheduled start date and time for the task"
    )
    end_date = fields.Datetime(
        string="Scheduled End Date",
        help="Scheduled completion date and time for the task"
    )
    progress = fields.Float(
        compute='_compute_progress',
        string="Progress (%)",
        help="Progress percentage of completed checklist items"
    )
    checklist_id = fields.Many2one(
        'task.checklist',
        help="Select a checklist template to populate items"
    )
    checklist_line_ids = fields.One2many(
        'checklist.item.line',
        'task_id',
        string="Checklist Items",
        help="Checklist items assigned to this task"
    )

    @api.onchange('checklist_id')
    def _onchange_checklist_id(self):
        """Populates checklist_line_ids when a checklist template is selected."""
        self.checklist_line_ids = False
        if not self.checklist_id:
            return
        self.checklist_line_ids = [
            Command.create({
                'check_list_item_id': item.id,
                'description': item.description,
                'state': 'todo',
                'checklist_id': self.checklist_id.id,
            })
            for item in self.checklist_id.checklist_ids
        ]

    @api.depends('checklist_line_ids.state')
    def _compute_progress(self):
        """Calculates progress percentage based on checklist items in 'done' state."""
        for task in self:
            if not task.checklist_line_ids:
                task.progress = 0.0
                continue
            total_completed = sum(
                1 for line in task.checklist_line_ids
                if line.state == 'done'
            )
            task.progress = (total_completed / len(task.checklist_line_ids)) * 100.0

