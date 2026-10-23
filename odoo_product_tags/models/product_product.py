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
import ast
from odoo import Command, api, models


class ProductProduct(models.Model):
    """Inherited the class Product Variants for passing the product Tags."""
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        """Inherited for passing the default product Tags."""
        res = super().create(vals_list)
        pro_tag = self.env['ir.config_parameter'].sudo().get_str(
            'odoo_product_tags.product_tag_ids')
        if pro_tag:
            try:
                tag_ids = ast.literal_eval(pro_tag)
            except (ValueError, SyntaxError):
                tag_ids = []
            if tag_ids:
                for product in res:
                    if not product.product_tag_ids:
                        product.product_tag_ids = [Command.set(tag_ids)]
        return res


    def action_apply_product_tags(self):
        """Applying product tags"""
        return {
            'name': 'Apply Product Tag',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.multiple.tag',
            'context': {
                'default_product_ids': self.ids,
                'default_is_product': True,
            },
            'target': 'new',
        }

