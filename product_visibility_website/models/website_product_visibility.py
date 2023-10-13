# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Neeraj Krishnan V M, Saneen K (<https://www.cybrosys.com>)
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
from odoo import fields, models, api


class ProductVisibility(models.Model):
    """Inherit res.partner for adding the fields for selecting the products"""
    _inherit = 'res.partner'

    filter_mode = fields.Selection(
        [('null', 'No Filter'), ('product_only', 'Product Wise'),
         ('categ_only', 'Category Wise')], string='Filter Mode', default='null',
        help="Select any mode")
    website_available_product_ids = fields.Many2many('product.template',
                                                     string='Available Product',
                                                     domain="[('is_published"
                                                            "', '=', True)]",
                                                     help='The website will '
                                                          'only display '
                                                          'products which are '
                                                          'within one'
                                                          'of the selected '
                                                          'category trees. If '
                                                          'no category is '
                                                          'specified,'
                                                          'all available '
                                                          'products will be '
                                                          'shown')
    website_available_cat_ids = fields.Many2many('product.public.category',
                                                 string='Available Product '
                                                        'Categories',
                                                 help='The website will only '
                                                      'display products which '
                                                      'are selected.'
                                                      'If no product is '
                                                      'specified,'
                                                      'all available products '
                                                      'will be shown')

    @api.onchange("filter_mode")
    def onchange_filter_mod(self):
        """Function for viewing the modes and product/category"""
        if self.filter_mode == 'null':
            self.website_available_cat_ids = None
            self.website_available_product_ids = None
