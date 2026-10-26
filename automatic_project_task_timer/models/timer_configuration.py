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


class TimerConfiguration(models.Model):
    """Timer configuration model to configure the automatic timer
    stage for each project."""
    _name = 'timer.configuration'
    _description = 'Timer Configuration'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        help='Configure the project to activate the timer.'
    )
    stage_ids = fields.Many2many(
        'project.task.type',
        string='Stages',
        help='Stages of the selected project.'
    )
    stage_id = fields.Many2one(
        'project.task.type',
        string='Stage',
        domain="[('id', 'in', stage_ids)]",
        required=True,
        help='Set the stage to activate the timer.'
    )

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """Set the domain for stage_id to stages of the selected project."""
        if self.project_id:
            stages = self.env['project.task.type'].search([
                ('project_ids', 'in', self.project_id.id)
            ])
            self.stage_ids = stages
        else:
            self.stage_ids = self.env['project.task.type']
        if self.stage_id and self.stage_id not in self.stage_ids:
            self.stage_id = False

    @api.model_create_multi
    def create(self, vals_list):
        """Set the status stage for all tasks in the corresponding project."""
        records = super().create(vals_list)
        for record in records:
            if record.project_id and record.stage_id:
                tasks = self.env['project.task'].search([
                    ('project_id', '=', record.project_id.id),
                    ('stage_id', '=', record.stage_id.id),
                ])
                tasks.write({'is_status_stage': True})
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' in vals or 'project_id' in vals:
            for record in self:
                if record.project_id and record.stage_id:
                    tasks = self.env['project.task'].search([
                        ('project_id', '=', record.project_id.id),
                        ('stage_id', '=', record.stage_id.id),
                    ])
                    tasks.write({'is_status_stage': True})
        return res
