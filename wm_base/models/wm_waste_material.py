# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class WmWasteMaterial(models.Model):
    """Master data model for specific waste material products and recovery properties."""
    _name = 'wm.waste.material'
    _description = 'Waste Material'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    category_ids = fields.Many2many(
        'wm.waste.category',
        relation='waste_category_material_rel',
        column1='material_id',
        column2='category_id',
        string='Categories'
    )
    is_waste_material = fields.Boolean(string='Is Waste Material', default=False)
    compliance_code_id = fields.Many2one('wm.compliance.code', string='Compliance Code')
    category_id = fields.Many2one('wm.waste.category', string='Primary Category')
    hazardous = fields.Boolean(string='Hazardous', default=False)
    recyclable = fields.Boolean(string='Recyclable', default=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    color = fields.Integer(string='Color', default=0)
