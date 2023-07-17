# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vivek @ cybrosys,(odoo@cybrosys.com)
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
from odoo import fields, models


class ClassicStoreConfig(models.Model):
    """
    Creating 'name', 'max_price', 'trending_product_ids', field in
    classic.store.config settings
    """
    _name = 'classic.store.config'
    _description = 'Configuration model for theme classic store'

    name = fields.Char(string='Name',
                       help="Name field in classic store config settings")
    max_price = fields.Integer(string="Maximum Price", default=100000,
                               help="Maximum amount to apply in product filter")
    trending_product_ids = fields.Many2many('product.template',
                                            string="Trending Products",
                                            help="Manually enter trending "
                                                 "products or leave the field "
                                                 "blank to automatically "
                                                 "add the trending products.",
                                            domain=[
                                                ('is_published', '=', True)])


class ThemeClassicStore(models.AbstractModel):
    """
    This class extends the 'theme.utils' abstract model to provide
    theme-specific functionalities.
    """
    _inherit = 'theme.utils'

    def _theme_classic_store_post_copy(self, mod):
        """
        Disable certain views in the website sale and wishlist functionality
        of the Odoo e-commerce module for the "Classic" theme.
        This method disables certain views related to features such as product
        comparison, grid or list views, adding products to the cart or wishlist,
        displaying product attributes and variants, displaying recommended or
        recently viewed products, and other product-related features in the
        e-commerce website.
        """
        self.disable_view('website_sale_comparison.add_to_compare')
        self.disable_view('website_sale_comparison.product_attributes_body')
        self.disable_view('website_sale.add_grid_or_list_option')
        self.disable_view('website_sale.products_add_to_cart')
        self.disable_view('website_sale_comparison.add_to_compare')
        self.disable_view('website_sale.product_buy_now')
        self.disable_view('website_sale_wishlist.add_to_wishlist')
        self.disable_view('website_sale.add_grid_or_list_option')
        self.disable_view('website_sale.products_list_view')
        self.disable_view('website_sale.product_buy_now')
        self.disable_view('website_sale.product_comment')
        self.disable_view('website_sale.product_variants')
        self.disable_view('website_sale_comparison.product_attributes_body')
        self.disable_view('website_sale.ecom_show_extra_fields')
        self.disable_view('website_sale.product_custom_text')
        self.disable_view('website_sale_wishlist.product_add_to_wishlist')
