# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inheriting res_config_settings model to set discount limit for
    product/product categories"""
    _inherit = 'res.config.settings'

    limit_discount = fields.Boolean(string="Discount Limit",
                                    help="Enable to apply limit" 
                                         "on discount limit",
                                    config_parameter='discount_limit.'
                                                     'limit_discount')
    apply_discount_limit = fields.Selection([
        ('product', 'Product'),
        ('product_category', 'Product Category')],
        string="Apply Discount Limit",
        related="pos_config_id.apply_discount_limit",
        readonly=False, help="Select product or product category option"
                             " to apply discount")

    @api.onchange('apply_discount_limit')
    def _onchange_apply_discount_limit(self):
        """
        setting the discount_limit for product or product categories field
         based on the apply_discount_limit option.
        """
        products = self.env['product.product'].search(
            [('available_in_pos', '=', True)])
        categories = self.env['pos.category'].search([])
        if self.apply_discount_limit == 'product':
            for product in products:
                product.pd_apply_limit = True
            for category in categories:
                category.apply_limit = False
        else:
            for category in categories:
                category.apply_limit = True
            for product in products:
                product.pd_apply_limit = False
