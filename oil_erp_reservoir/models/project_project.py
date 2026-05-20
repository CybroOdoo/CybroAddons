# -*- coding: utf-8 -*-
#############################################################################
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

class Project(models.Model):
    """
    Extends 'project.project' to link it directly with an oil reservoir and 
    enforce industrial-specific project stages.
    """
    _inherit = 'project.project'

    reservoir_id = fields.Many2one(
        'oil.reservoir',
        string='Reservoir',
        help="Oil reservoir linked to this upstream project.")
    stage_id_domain = fields.Char(
        compute='_compute_stage_id_domain',
        store=False,
        help="Dynamic domain restricting available stages for oil and gas projects.")

    @api.depends('is_oil_gas_project')
    def _compute_stage_id_domain(self):
        """
        Restricts available project stages to reservoir-specific ones if the 
        project is marked as an oil and gas project.
        """
        for project in self:
            if project.is_oil_gas_project:
                project.stage_id_domain = "[('is_oil_project_stage', '=', True)]"
            else:
                project.stage_id_domain = "[]"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sets the default exploration stage for new oil and gas projects.
        """
        # Get the first Oil & Gas project stage for the default
        oil_gas_project_stage = self.env.ref(
            'oil_erp_reservoir.project_stage_exploration', raise_if_not_found=False)

        for vals in vals_list:
            if vals.get('is_oil_gas_project'):
                if oil_gas_project_stage:
                    vals['stage_id'] = oil_gas_project_stage.id

        return super().create(vals_list)

    def write(self, vals):
        """
        Synchronizes the linked reservoir's stage if the project stage changes.
        """
        res = super().write(vals)
        if 'stage_id' in vals:
            for project in self:
                if project.reservoir_id and project.reservoir_id.stage_id != project.stage_id:
                    project.reservoir_id.stage_id = project.stage_id.id
        return res
