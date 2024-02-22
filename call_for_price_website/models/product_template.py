# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Nikhil M (odoo@cybrosys.com)
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


    price_call = fields.Boolean(string="Call for Price",
                                help="This will hide the price and add to cart button"
                                     "from shop and customer can request by"
                                     "calling for price")

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1.0,parent_combination=False, only_template=False,):
        """To update the call for price value of the product to website."""
        # Call the parent method to get the initial combination_info
        combination_info = super(ProductTemplate,
                                 self)._get_combination_info(
            combination=combination, product_id=product_id,
            add_qty=add_qty,parent_combination=parent_combination,
            only_template=only_template)
        combination_info['price_call'] = self.price_call
        return combination_info

    def _website_show_quick_add(self):
        """ Hide the option to quick add cart in shop if price call is enabled"""
        if self.price_call:
            return False
        else:
            return super(ProductTemplate, self)._website_show_quick_add()

    def _search_render_results_prices(self, mapping, combination_info):
        """ Hide price when the product is searched if the price call is enabled."""
        # Call the super method to get the original values
        price, list_price = super(ProductTemplate, self)._search_render_results_prices(mapping, combination_info)

        if combination_info['price_call']:
            price = 'Not Available For Sale'
        # Return the modified values
        return price, list_price
