# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inheriting product template model for adding the field price_call into
    the combination_info"""
    _inherit = 'product.template'

    def _get_combination_info(self, combination=False, product_id=False,
                              add_qty=1, pricelist=False,
                              parent_combination=False,
                              only_template=False):
        # Call the parent method to get the initial combination_info
        combination_info = super(ProductTemplate,
                                 self)._get_combination_info(
            combination=combination, product_id=product_id,
            add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template)

        if combination_info.get('product_id'):
            product = self.env['product.product'].browse(
                combination_info['product_id'])
            combination_info['price_call'] = product.price_call
        return combination_info


class ProductProduct(models.Model):
    """Inheriting product variants model for adding a field that will hide
    price from website"""
    _inherit = 'product.product'

    price_call = fields.Boolean(string="Call for Price",
                                help="This will hide the price and cart button"
                                     "from shop and customer can request by "
                                     "calling for price")
