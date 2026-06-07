# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anupriya Ashok (odoo@cybrosys.com)
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
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Inherits the model product.template to extend and add fields"""
    _inherit = 'product.template'

    is_a_parts = fields.Boolean(
        'Is a Mobile Part', default=False,
        help="Specify if the product is a mobile part or not.")
    brand_name = fields.Many2one('mobile.brand', string="Brand",
                                 help="Select a mobile brand for the part.")
    allowed_model_ids = fields.Many2many('brand.model', compute='_compute_allowed_model_ids')
    model_name = fields.Many2one('brand.model', string="Model Name",
                                 help="Select a model for the part.")
    model_colour = fields.Char(string="Colour", help="Colour for the part.")
    extra_descriptions = fields.Text(string="Note", help="Extra description "
                                                         "for the part.")

    @api.depends('brand_name')
    def _compute_allowed_model_ids(self):
        """Compute allowed models filtered by selected brand."""
        for rec in self:
            if rec.brand_name:
                rec.allowed_model_ids = self.env['brand.model'].search([
                    ('mobile_brand_name', '=', rec.brand_name.id)
                ]).ids
            else:
                rec.allowed_model_ids = self.env['brand.model'].search([]).ids
