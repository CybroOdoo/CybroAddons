# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _


class TaskChecklist(models.Model):
    _name = 'task.checklist'

    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
    task_ids = fields.Many2one('project.task', string='Task')
    project_id = fields.Many2one('project.project', string='Project')

    checklist_ids = fields.One2many('checklist.item', 'checklist_id', string='CheckList Items', required=True)


class CheckListItem(models.Model):
    _name = 'checklist.item'
    _description = "Checklist Item"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=1)
    description = fields.Char()
    checklist_id = fields.Many2one('task.checklist')


class ChecklistItemLine(models.Model):
    _name = 'checklist.item.line'
    _description = 'Checklist Item Line'

    check_list_item_id = fields.Many2one('checklist.item', required=True)
    description = fields.Char()
    projects_id = fields.Many2one('project.task')
    checklist_id = fields.Many2one('task.checklist')
    state = fields.Selection(string='Status', required=True, readonly=True, copy=False, tracking=True, selection=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='todo', )

    def approve_and_next(self):
        self.state = 'in_progress'

    def mark_completed(self):
        self.state = 'done'

    def mark_canceled(self):
        self.state = 'cancel'

    def reset_stage(self):
        self.state = 'todo'


class ChecklistProgress(models.Model):
    _inherit = 'project.task'

    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    progress = fields.Float(compute='_compute_progress', string='Progress in %')
    checklist_ids = fields.Many2many('task.checklist', compute='_compute_checklist_ids')
    checklist_id = fields.Many2one('task.checklist')
    checklists = fields.One2many('checklist.item.line', 'projects_id', string='CheckList Items', required=True)

    @api.onchange('checklist_id')
    def _onchange_project_id(self):
        checklist = self.env['task.checklist'].search([('name', '=', self.checklist_id.name)])
        self.checklists = False
        self.checklists = [(0, 0, {
            'check_list_item_id': rec.id,
            'state': 'todo',
            'checklist_id': self.checklist_id.id,
        }) for rec in checklist.checklist_ids]

    def _compute_checklist_ids(self):
        for rec in self:
            self.checklist_ids = self.env['task.checklist'].search([('task_ids', '=', rec.id)])

    def _compute_progress(self):
        for rec in self:
            total_completed = 0
            for activity in rec.checklists:
                if activity.state in ['cancel', 'done', 'in_progress']:
                    total_completed += 1
            if total_completed:
                rec.progress = float(total_completed) / len(rec.checklists) * 100

            else:
                rec.progress = 0.0
