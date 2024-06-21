# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models , api


class ProjectTaskTemplate(models.Model):
    """A model to define task templates for projects."""
    _name = 'project.task.template'
    _description = 'Project Task Template'

    name = fields.Char(string='Template Name', translate=True,
                       help='Name for the task template.')
    task_ids = fields.One2many(
        'project.sub.task', 'project_template_id',
        string='Tasks',
        help='List of the tasks associated with this template.')
    stage_ids = fields.One2many(
        'project.stage', 'project_template_id',
        string='Stages',
        help='List of the stages associated with this template.')


class ProjectStage(models.Model):
    """A model to define task templates for projects."""
    _name = 'project.stage'
    _order = "sequence,id"

    project_template_id = fields.Many2one(
        'project.task.template', string='Project Template',
        help='Select a project task template to use for this task.')
    project_stage_id = fields.Many2one(
        'project.task.type', string='Project Stage',
        help='Select a project stage. ',required=True)
    task_ids = fields.Many2many(
        'project.sub.task',
        help='Choose the tasks corresponding to each stage')

    sequence = fields.Integer(related="project_stage_id.sequence",readonly=False)


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    project_template_id = fields.Many2one(
        'project.task.template')
