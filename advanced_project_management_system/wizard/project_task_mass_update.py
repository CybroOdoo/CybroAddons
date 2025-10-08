# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ProjectTaskMassUpdate(models.TransientModel):
    """ Wizard for mass task details updates"""
    _name = "project.task.mass.update"
    _description = "Task mass update"

    is_update_assign_to = fields.Boolean(string="Update Assign To",
                                         help="For updating task assignees")
    is_update_deadline = fields.Boolean(string='Update Deadline',
                                        help="For updating task deadline")
    is_update_project = fields.Boolean(string='Update Project',
                                       help="for updating project details")
    is_update_stage = fields.Boolean(string='Update Stage',
                                     help="for updating task stage")
    is_update_tags = fields.Boolean(string='Update Tags',
                                    help="for updating task tags")
    user_ids = fields.Many2many('res.users', string='Assign To',
                                help="FOr updating users")
    deadline = fields.Date(string='Deadline',
                           help="For updating task deadline")
    project_id = fields.Many2one('project.project', string='Project',
                                 help="For updating projects in a task")
    stage_id = fields.Many2one('project.task.type', string='stage',
                               help="For updating task stage",
                               domain=[('fold', '=', True)])
    tag_ids = fields.Many2many('project.tags', string='Tags',
                               help="FOr updating task tags")

    def update_task_details(self):
        """ Function to update task information coming from the wizard """
        if self.user_ids:
            for task in self.env['project.task'].browse(
                    self._context['active_ids']):
                task.update({
                    'user_ids': self.user_ids.ids,
                })
        if self.deadline:
            for task in self.env['project.task'].browse(
                    self._context['active_ids']):
                task.update({
                    'date_deadline': self.deadline,
                })
        if self.project_id:
            for task in self.env['project.task'].browse(
                    self._context['active_ids']):
                task.update({
                    'project_id': self.project_id.id,
                })
        if self.stage_id:
            for task in self.env['project.task'].browse(
                    self._context['active_ids']):
                task.update({
                    'stage_id': self.stage_id.id,
                })
        if self.tag_ids:
            for task in self.env['project.task'].browse(
                    self._context['active_ids']):
                task.update({
                    'tag_ids': self.tag_ids.ids,
                })
