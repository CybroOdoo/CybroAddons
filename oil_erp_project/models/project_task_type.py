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

class ProjectTaskType(models.Model):
    """
    Extends 'project.task.type' to include industry-specific stage flags, 
    such as production and closure indicators.
    """
    _inherit = 'project.task.type'

    is_oil_gas_task_stage = fields.Boolean('Is Oil Gas Task Stage',
                                           help='Designate this stage for use in oil and gas well task pipelines.')
    is_production = fields.Boolean(
        string='Is Production Stage',
        help='Show the production recording button on tasks in this stage.',
    )
    is_closed = fields.Boolean('Is Closed', help='Mark this stage as a closing stage where tasks are considered complete.')

    @api.model
    def default_get(self, fields_list):
        """
        Overrides default_get to set is_oil_gas_task_stage
        when creating a stage from an Oil ERP project.
        """
        res = super().default_get(fields_list)
        project_id = self.env.context.get('default_project_id')
        if project_id:
            project = self.env['project.project'].browse(project_id)
            if project.is_oil_gas_project:
                res['is_oil_gas_task_stage'] = True
        return res
