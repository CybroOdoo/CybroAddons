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


class ChecklistItemLine(models.Model):
    """Model for checklist item lines associated with a specific project task."""
    _name = 'checklist.item.line'
    _description = 'Checklist Item Line'

    check_list_item_id = fields.Many2one(
        'checklist.item',
        required=True,
        help="Checklist item template reference"
    )
    description = fields.Char(
        help="Description of the checklist item"
    )
    task_id = fields.Many2one(
        'project.task',
        ondelete='cascade',
        help="Associated project task"
    )
    checklist_id = fields.Many2one(
        'task.checklist',
        help="Associated task checklist"
    )
    state = fields.Selection(
        selection=[
            ('todo', 'To Do'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],
        default='todo',
        required=True,
        readonly=True,
        copy=False,
        help="Status of the task checklist item"
    )

    def action_approve_and_next(self):
        """
        Method to transition the state of an object to 'in_progress'.
        This action is typically performed to approve and move the object to the
        next stage.

        :return: None
        """
        self.state = 'in_progress'

    def action_mark_completed(self):
        """
        Method to mark an object as completed by transitioning its state to
        'done'.
        This action indicates that the associated task or process has been
        successfully finished.

        :return: None
        """
        self.state = 'done'

    def action_mark_canceled(self):
        """
        Method to mark an object as canceled by transitioning its state to
        'cancel'.
        This action indicates that the associated task or process has been
        canceled or terminated.

        :return: None
        """
        self.state = 'cancel'
