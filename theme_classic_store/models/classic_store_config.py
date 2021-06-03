# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields


class ClassicStoreConfig(models.Model):
    _name = 'classic_store.config'

    name = fields.Char('Name')
    max_price = fields.Integer(string="Maximum Price", default=100000,
                               help="Maximum amount to apply in product filter.")

    trending_product_ids = fields.Many2many('product.template',
                                            string="Trending Products",
                                            help="Manually enter trending "
                                                 "products or leave the field "
                                                 "blank to automatically "
                                                 "add the trending products.",
                                            domain=[
                                                ('is_published', '=', True)])


class ThemeClassicStore(models.AbstractModel):
    _inherit = 'theme.utils'

    def _theme_classic_store(self, mod):
        self.disable_view('website_sale_comparison.add_to_compare')
        self.disable_view('website_sale_comparison.product_attributes_body')
        self.disable_view('website_sale.add_grid_or_list_option')
        self.disable_view('website_sale.products_add_to_cart')
        self.disable_view('website_sale_comparison.add_to_compare')
        self.disable_view('website_sale.product_buy_now')
        self.disable_view('website_sale_wishlist.add_to_wishlist')
        self.disable_view('website_sale.add_grid_or_list_option')
        self.disable_view('website_sale.products_images_full')
        self.disable_view('website_sale.products_list_view')
        self.disable_view('website_sale.recommended_products')
        self.disable_view('website_sale.product_picture_magnify_auto')
        self.disable_view('website_sale.product_buy_now')
        self.disable_view('website_sale.product_comment')
        self.disable_view('website_sale.product_picture_magnify')
        self.disable_view('website_sale.product_variants')
        self.disable_view('website_sale_comparison.product_attributes_body')
        self.disable_view('website_sale.recently_viewed_products_product')
        self.disable_view('website_sale.ecom_show_extra_fields')
        self.disable_view('website_sale.product_custom_text')
        self.disable_view('website_sale_wishlist.product_add_to_wishlist')
