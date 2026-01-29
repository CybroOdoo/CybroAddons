# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sagarika B (odoo@cybrosys.com)
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
##############################################################################
"""project related models"""
from odoo import api, fields, models


class Project(models.Model):
    """inherit project.project"""
    _inherit = "project.project"

    project_short_code = fields.Char(string="Short Code", required=True,
                                     help="Set a short code here and this will"
                                          " be used to generate serial number "
                                          "for the project's tasks")
    sequence_id = fields.Many2one(
        'ir.sequence', 'Reference Sequence',
        check_company=True, copy=False)

    _sql_constraints = [
        ('project_code_uniq', 'unique(project_short_code, company_id)',
         'The project code must be unique per company!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """extend create method to create sequence"""
        for vals in vals_list:
            if 'sequence_id' not in vals or not vals['sequence_id']:
                vals['sequence_id'] = self.env['ir.sequence'].sudo().create({
                    'name': vals['name'] + ' Project Sequence',
                    'prefix': vals['project_short_code'] + '-', 'padding': 3,
                    'company_id': vals.get('company_id') or self.env.company.id,
                }).id
        return super().create(vals_list)
