# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ProjectStage(models.Model):
    """Model to link project stages with task templates and subtasks."""
    _name = "project.stage"
    _description = "Project Stage"
    _order = "sequence, id"

    project_template_id = fields.Many2one(
        comodel_name="project.task.template",string="Project Template",
        help="Select a project task template to use for this stage.")
    project_stage_id = fields.Many2one(
        comodel_name="project.task.type",
        string="Project Stage",required=True,help="Select the project stage.")
    task_ids = fields.Many2many(
        comodel_name="project.sub.task",string="Subtasks",
        help="Subtasks associated with this stage.")
    sequence = fields.Integer(
        related="project_stage_id.sequence",readonly=False,
        help = "Defines the order of this stage.")
