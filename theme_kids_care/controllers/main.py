# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class KidsCareController(http.Controller):
    """
    Controller for the Kids Care theme.
    Handles redirection for specific shop categories and provides a robust
    cart update mechanism.
    """

    @http.route('/shop/baby_tshirt', type='http', auth="public", website=True)
    def baby_tshirt_redirect(self, **post):
        """ Redirects the user to the 'BABY T-SHIRT' category page. """
        category = request.env.ref('theme_kids_care.public_category_baby_tshirt', raise_if_not_found=False)
        if not category:
            category = request.env['product.public.category'].sudo().search([('name', '=', 'BABY T-SHIRT')], limit=1)
        if category:
            return request.redirect('/shop/category/%s' % request.env['ir.http']._slug(category))
        return request.redirect('/shop')

    @http.route('/shop/baby_feeding', type='http', auth="public", website=True)
    def baby_feeding_redirect(self, **post):
        """ Redirects the user to the 'BABY FEEDING' category page. """
        category = request.env.ref('theme_kids_care.public_category_baby_feeding', raise_if_not_found=False)
        if not category:
            category = request.env['product.public.category'].sudo().search([('name', '=', 'BABY FEEDING')], limit=1)
        if category:
            return request.redirect('/shop/category/%s' % request.env['ir.http']._slug(category))
        return request.redirect('/shop')

    @http.route('/shop/baby_toys', type='http', auth="public", website=True)
    def baby_toys_redirect(self, **post):
        """ Redirects the user to the 'BABY TOYS' category page. """
        category = request.env.ref('theme_kids_care.public_category_baby_toys', raise_if_not_found=False)
        if not category:
            category = request.env['product.public.category'].sudo().search([('name', '=', 'BABY TOYS')], limit=1)
        if category:
            return request.redirect('/shop/category/%s' % request.env['ir.http']._slug(category))
        return request.redirect('/shop')

    @http.route(['/shop/cart/update', '/shop/cart/update/http'], type='http', auth="public", methods=['GET', 'POST'], website=True, csrf=False)
    def cart_update_http(self, **kw):
        """
        Robust HTTP route for cart updates.
        Also handles fallbacks for the native route and ensures the user is
        redirected to the cart after the update.
        """
        product_id = kw.get('product_id')
        if not product_id:
            return request.redirect("/shop")
        add_qty = kw.get('add_qty', 1)
        order = request.cart or request.website._create_cart()
        order._cart_add(
            product_id=int(product_id),
            quantity=float(add_qty),
        )
        return request.redirect("/shop/cart")

    @http.route('/shop/wishlist/toggle', type='jsonrpc', auth="public", website=True)
    def toggle_wishlist(self, product_id, **kw):
        """ Toggle wishlist for a given product_id. """
        product_id = int(product_id)
        Wishlist = request.env['product.wishlist']
        if request.website.is_public_user():
            Wishlist = Wishlist.sudo()
            partner_id = False
        else:
            partner_id = request.env.user.partner_id.id

        # Check if the product is already in the wishlist
        existing_wish = Wishlist.current().filtered(lambda w: w.product_id.id == product_id)
        if existing_wish:
            # Remove it
            wish_id = existing_wish[0].id
            if not partner_id:
                wish_ids = request.session.get('wishlist_ids') or []
                if wish_id in wish_ids:
                    request.session['wishlist_ids'].remove(wish_id)
                    request.session.touch()
            existing_wish.unlink()
            return {'action': 'removed'}
        else:
            # Add it
            product = request.env['product.product'].browse(product_id)
            price = product._get_combination_info_variant()['price']
            wish = Wishlist._add_to_wishlist(
                request.pricelist.id,
                request.website.currency_id.id,
                request.website.id,
                price,
                product_id,
                partner_id
            )
            if not partner_id:
                request.session['wishlist_ids'] = request.session.get('wishlist_ids', []) + [wish.id]
            return {'action': 'added'}


class KidsCareWebsiteSale(WebsiteSale):

    def _shop_lookup_products(self, options, post, search, website):
        fuzzy_search_term, product_count, search_result = super()._shop_lookup_products(options, post, search, website)
        
        # Sort wishlist items first
        if 'product.wishlist' in request.env:
            wish_tmpl_ids = set(request.env['product.wishlist'].current().product_id.product_tmpl_id.ids)
            if wish_tmpl_ids:
                # Separate wishlist products and others
                wish_products = search_result.filtered(lambda p: p.id in wish_tmpl_ids)
                other_products = search_result.filtered(lambda p: p.id not in wish_tmpl_ids)
                # Re-concat them: wish products first, then others
                search_result = wish_products + other_products
                
        return fuzzy_search_term, product_count, search_result

