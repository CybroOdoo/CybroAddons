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


class ProjectTask(models.Model):
    """Inherits the project Task Model for adding new fields and functions"""
    _inherit = "project.task"

    progress_bar = fields.Float(string='Progress Bar',
                                help='Calculate the progress of the task '
                                     'based on the task stage',
                                compute='_compute_progress_bar')
    stage_is_progress = fields.Boolean(related='stage_id.is_progress_stage',
                                       help='Status of the task based on the '
                                            'stage')

    @api.depends('stage_id.progress_bar')
    def _compute_progress_bar(self):
        """Compute functionality for the task based on the progress bar"""
        for rec in self:
            rec.progress_bar = rec.stage_id.progress_bar
