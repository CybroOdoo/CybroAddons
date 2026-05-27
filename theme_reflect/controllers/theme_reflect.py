# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class ReflectWebsiteSale(WebsiteSale):
    @http.route()
    def shop_payment_confirmation(self, **post):
        """Inherit confirmation route and inject extra template flag."""
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            values = self._prepare_shop_payment_confirmation_values(order)
            values.update({'hide_cart': True})
            return request.render('website_sale.confirmation', values)
        return request.redirect(self._get_shop_path())

    @http.route(
        ['/shop/new', '/shop/new/page/<int:page>'],
        type='http',
        auth='public',
        website=True,
        sitemap=WebsiteSale.sitemap_shop,
    )
    def shop_new(self):
        """ Controller to fetch the latest website product """
        website = request.website
        products = request.env['product.template'].with_context(website_id=website.id).search(
            [('is_published', '=', True), ('sale_ok', '=', True)],
            order='create_date desc, id desc',
            limit=15,
        )
        return request.render('theme_reflect.new_in_products_page', {
            'products': products,
            'website': website,
        })

    @http.route('/shop/new/wishlist/remove', type='jsonrpc', auth='public', website=True)
    def shop_new_wishlist_remove(self, product_id, **kwargs):
        """ Wishlist remove from the new in page """
        wish = request.env['product.wishlist'].current().filtered(
            lambda w: w.product_id.id == int(product_id)
        )[:1]
        if wish:
            if request.website.is_public_user():
                wish_ids = request.session.get('wishlist_ids') or []
                if wish.id in wish_ids:
                    request.session['wishlist_ids'].remove(wish.id)
                    request.session.touch()
                wish.sudo().unlink()
            else:
                wish.unlink()
        return True
