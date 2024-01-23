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


class TaskChecklist(models.Model):
    """
    Model representing a task checklist.
    """
    _name = 'task.checklist'
    _description = 'Task checklist'

    name = fields.Char(string='Name', help='Name of the checklist')
    description = fields.Char(string='Description',
                              help='Description of the checklist')
    task_id = fields.Many2one('project.task', string='Task',
                              help='Name of the Task')
    checklist_ids = fields.One2many('checklist.item', 'checklist_id',
                                    string='CheckList Items', required=True,
                                    help='Items of checklist')
