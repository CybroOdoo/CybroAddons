# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    """Inherit 'res.partner' for adding the fields for selecting the products"""
    _inherit = 'res.partner'

    filter_mode = fields.Selection(
        [('null', 'No Filter'),('product_only', 'Product Wise'),
         ('categ_only', 'Category Wise')], string='Filter Mode', default="null",
        help="Select any mode")
    website_available_product_ids = fields.Many2many(
        'product.template', string='Available Product',
        domain="[('is_published', '=', True)]",
        help="The website will only display products which are selected. "
             "If no product is specified, all available products will be shown")
    website_available_cat_ids = fields.Many2many(
        'product.public.category', string='Available Product Categories',
        help="The website will only display products which are within one "
             "of the selected category trees. If no category is specified, "
             "all available products will be shown")
   
    @api.onchange('filter_mode')
    def _onchange_filter_mode(self):
        for rec in self:
            if rec.filter_mode == 'null' or not rec.filter_mode:
                rec.website_available_cat_ids = False
                rec.website_available_product_ids = False
            elif rec.filter_mode == 'product_only':
                rec.website_available_cat_ids = False
            elif rec.filter_mode == 'categ_only':
                rec.website_available_product_ids = False
