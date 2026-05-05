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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class TimerConfiguration(models.Model):
    """Timer configuration model for configure the automatic timer
    stage to activate the timer, Each project have different stages,
    based on the configured stage for each project the timer will be runs."""
    _name = 'timer.configuration'
    _description = 'Timer Configuration'

    project_id = fields.Many2one('project.project', string='Project',
                                 help='Configure the project to activate the '
                                      'timer')
    stage_ids = fields.Many2many('project.task.type',
                                 string='Stages',
                                 help='To set the domain for stages')
    stage_id = fields.Many2one('project.task.type', string='Stage',
                               help='Set the stage to activate the timer',
                               domain="[('id', 'in', stage_ids)]",
                               required=True)

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """To set the domain for stage_id field to select the stages
         from the stages of the selected project"""
        data = []
        for rec in self.env['project.task.type'].search([]):
            if self.project_id.id in rec.project_ids.ids:
                data.append(rec.id)
        self.stage_ids = data


    @api.model
    def create(self, vals_list):
        """To set the status stage for all the tasks in the corresponding
            project, so that the warning message will pop-ups when the form
            opens. For that supering the ORM Create method to get the corresponding
            project. """
        records = super(TimerConfiguration, self).create(vals_list)

        for vals, record in zip(vals_list, records):
            project = self.env['project.project'].sudo().browse(vals.get('project_id'))
            if project:
                tasks = self.env['project.task'].search([('project_id', '=', project.id)])
                for task in tasks:
                    if task.stage_id.id == vals.get('stage_id'):
                        task.write({'is_status_stage': True})
                    else:
                        task.write({'is_status_stage': False})

        return records
