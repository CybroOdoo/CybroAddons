# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class ChecklistItemLine(models.Model):
    """
    Model for checklist lines
    """
    _name = 'checklist.item.line'
    _description = 'Checklist Item Line'

    check_list_item_id = fields.Many2one('checklist.item',
                                         string="Checklist item", required=True,
                                         help='Checklist item')
    description = fields.Char(string="Description",
                              help="Description of the checklist item")
    projects_id = fields.Many2one('project.task', string="Project",
                                  help="Name of the project")
    checklist_id = fields.Many2one('task.checklist',
                                   string="Checklist", help="Checklist")
    state = fields.Selection(string='Status', required=True, readonly=True,
                             copy=False, tracking=True,
                             selection=[('todo', 'To Do'),
                                        ('in_progress', 'In Progress'),
                                        ('done', 'Done'),
                                        ('cancel', 'Cancelled')],
                             default='todo', help="State")

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
