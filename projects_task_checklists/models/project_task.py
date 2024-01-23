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
from odoo import api, fields, models


class ProjectTask(models.Model):
    """Inheriting project_task model to add checklist fields"""
    _inherit = 'project.task'

    start_date = fields.Datetime(string='Start Date', help="Start Date")
    end_date = fields.Datetime(string='End Date', help="End Date")
    progress = fields.Float(compute='_compute_progress', string='Progress in %',
                            help="Progress in %")
    checklist_ids = fields.Many2many('task.checklist',
                                     compute='_compute_checklist_ids',
                                     string='Checklist',
                                     help="Checklist items")
    checklist_id = fields.Many2one('task.checklist',
                                   string='Checklist',
                                   help="Select Checklist")
    checklists_ids = fields.One2many('checklist.item.line',
                                     'projects_id',
                                     string='CheckList Items', required=True,
                                     help='Add checklist items')

    @api.onchange('checklist_id')
    def _onchange_checklist_id(self):
        """Triggered when the 'checklist_id' field is changed. It searches
         for the corresponding task checklist based on the name and updates
         the 'checklists_ids' field with checklist items. :return: None"""
        checklist = self.env['task.checklist'].search(
            [('name', '=', self.checklist_id.name)])
        self.checklists_ids = False
        self.checklists_ids = [(0, 0, {
            'check_list_item_id': rec.id,
            'state': 'todo',
            'checklist_id': self.checklist_id.id,
        }) for rec in checklist.checklist_ids]

    def _compute_checklist_ids(self):
        """Compute method that updates the 'checklist_ids' field for each
         record. It retrieves task checklists related to the current record
          and assigns them to the 'checklist_ids' field. :return: None"""
        for rec in self:
            self.checklist_ids = self.env['task.checklist'].search(
                [('task_id', '=', rec.id)])

    def _compute_progress(self):
        """Compute method that calculates the progress percentage for each
         record. It iterates through the associated checklist items and
         calculates the percentage of completed activities based on their
          states. The 'progress' field is updated accordingly. :return: None"""
        for rec in self:
            total_completed = 0
            for activity in rec.checklists_ids:
                if activity.state in ['cancel', 'done', 'in_progress']:
                    total_completed += 1
            if total_completed:
                rec.progress = float(total_completed) / len(
                    rec.checklists_ids) * 100
            else:
                rec.progress = 0.0
