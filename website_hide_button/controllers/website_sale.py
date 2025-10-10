# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSaleInherit(WebsiteSale):
    """class to hide price, add to cart and quantity"""

    def should_show_price_for_current_website(self):
        """
        Check if price should be SHOWN for the current website
        Returns: True if price should be shown, False if should be hidden
        """
        # If hide_price setting is not enabled, show price
        if not request.env['ir.config_parameter'].sudo().get_param('website_hide_button.hide_price'):
            return True

        hide_type = request.env['ir.config_parameter'].sudo().get_param('website_hide_button.hide_type')
        website_ids_param = request.env['ir.config_parameter'].sudo().get_param('website_hide_button.website_ids') or ''
        website_ids = [int(w) for w in website_ids_param.split(',') if w]
        current_website = request.env['website'].get_current_website()

        if hide_type == 'all':
            # Hide price on ALL websites
            return False
        else:
            # Hide price only on specific websites
            if current_website.id in website_ids:
                return False  # Hide on this website
            else:
                return True  # Show on other websites

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/
        page/<int:page>'''
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        """Method for finding log in user or not in shop page """
        res = super().shop(page, category, search, min_price,
                           max_price, ppg, **post)
        res.qcontext.update({
            'login_user': request.env.user._is_public() and request.env[
                'ir.config_parameter'].sudo().get_param('website_hide_button.hide_cart'),
            'show_price': self.should_show_price_for_current_website()  # True = show, False = hide
        })
        return res

    def _prepare_product_values(self, product, category, search, **kwargs):
        """Method for finding log in user or not in product page """
        res = super(WebsiteSaleInherit, self)._prepare_product_values(product,
                                                                      category,
                                                                      search,
                                                                      **kwargs)
        res['show_price'] =self.should_show_price_for_current_website()
        res['login_user'] = True if request.env.user._is_public() and \
                                    request.env[
                                        'ir.config_parameter'].sudo().get_param(
                                        'website_hide_button.hide_cart') else False
        return res

    @http.route()
    def shop_payment(self, **post):
        """  Restrict public visitors from accessing payment page so that SO
        creation will be disabled   """
        user = http.request.env.user
        if (
                not user._is_public() or user._is_public() and not request.env.user._is_public() and self.should_show_price_for_current_website()) and user.has_group(
            'base.group_portal') or \
                user.has_group('base.group_user'):
            res = super(WebsiteSaleInherit, self).shop_payment(**post)
            return res
        return request.redirect("/")
