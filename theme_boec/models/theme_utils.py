# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################
from odoo import models


class ThemeUtils(models.AbstractModel):
    _inherit = 'theme.utils'

    def _theme_boec_post_copy(self, mod):
        self.enable_view('theme_boec.boec_header')
        self.disable_view('website_sale.products_add_to_cart')
        self.disable_view('website_sale_comparison.add_to_compare')
        self.disable_view('website_sale.product_buy_now')
        self.disable_view('website_sale_wishlist.add_to_wishlist')
        self.disable_view('website_sale.add_grid_or_list_option')
        self.disable_view('website_sale.products_list_view')
        self.disable_view('website_sale.alternative_products')
        self.disable_view('website_sale.product_buy_now')
        self.disable_view('website_sale.product_comment')
        self.disable_view('website_sale.product_picture_magnify_both')
        self.disable_view('website_sale.product_variants')
        self.disable_view('website_sale_comparison.product_attributes_body')
        self.disable_view('website_sale.ecom_show_extra_fields')
        self.disable_view('website_sale.product_custom_text')
        self.disable_view('website_sale_wishlist.product_add_to_wishlist')
        self.disable_view('website_blog.opt_posts_loop_show_author')
        self.disable_view('website_blog.opt_posts_loop_show_stats')
        self.disable_view('website_blog.opt_posts_loop_show_stats')
        self.disable_view('website_blog.opt_blog_list_view')
        self.disable_view('website_blog.opt_blog_cards_design')
        self.disable_view('website_blog.opt_blog_cover_post')
        self.disable_view('website_blog.opt_blog_cover_post_fullwidth_design')
        self.disable_view('website_blog.opt_blog_post_breadcrumb')
        self.disable_view('website_blog.opt_blog_post_sidebar')
