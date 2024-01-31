# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul P I (odoo@cybrosys.com)
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
from odoo import api, fields, models


class ProjectProject(models.Model):
    """Inherits the project Model for adding new fields and functions"""
    _inherit = "project.project"

    progressbar = fields.Float(string='Progress Bar',
                               compute='_compute_progress_bar',
                               help='Calculate the progress of the task '
                                    'based on the task stage')
    is_progress_bar = fields.Boolean(string='Is Progress Bar',
                                     help='Status of the task based the '
                                          'stage')

    @api.depends()
    def _compute_progress_bar(self):
        """Compute functionality for the task based on the progress bar"""
        for rec in self:
            progressbar_tasks = rec.task_ids.filtered(
                lambda progress: progress.stage_id.is_progress_stage == True)
            if progressbar_tasks:
                rec.progressbar = (sum(progressbar_tasks.mapped(
                    'progress_bar'))) / len(progressbar_tasks)
            else:
                rec.progressbar = 0
