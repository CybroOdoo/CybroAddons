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
from odoo import api, fields, models


class ProjectProject(models.Model):
    """Inherits the project Model for adding new fields and functions"""
    _inherit = "project.project"

    progressbar = fields.Float(string='Progress Bar',
                               compute='_compute_progress_bar',
                               help='Calculate the overall progress of the '
                                    'project based on the task stage')
    is_progress_bar = fields.Boolean(string='Is Progress Bar',
                                     help='Status of the project progress bar '
                                          'based on the stage')

    @api.depends('task_ids.stage_id.is_progress_stage', 'task_ids.progress_bar')
    def _compute_progress_bar(self):
        """Compute functionality for the task based on the progress bar"""
        for rec in self:
            progressbar_tasks = rec.task_ids.filtered(
                lambda progress: progress.stage_id.is_progress_stage)
            if progressbar_tasks:
                rec.progressbar = (sum(progressbar_tasks.mapped(
                    'progress_bar'))) / len(progressbar_tasks)
            else:
                rec.progressbar = 0.0
