# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import http
from odoo.http import request

class ReflectController(http.Controller):

    @http.route(['/theme_reflect/newsletter/subscribe'], type='http', auth='public', website=True, csrf=False)
    def newsletter_subscribe(self, email=None, **post):
        """
        Fallback newsletter subscription endpoint.
        """
        redirect_url = request.httprequest.referrer or '/'
        if not email or '@' not in email:
            return request.redirect(redirect_url)
        try:
            Contact = request.env['mailing.contact'].sudo()
            existing = Contact.search([('email', '=', email)], limit=1)
            if not existing:
                Contact.create({'email': email})
            return request.redirect('/contactus-thank-you')
        except Exception:
            return request.redirect('/contactus-thank-you')

    @http.route(['/shop/cart/sidebar_html'], type='json', auth="public", website=True)
    def cart_sidebar_html(self, **post):
        """Returns the HTML for the cart sidebar content."""
        values = {
            'website': request.website,
        }
        return request.env['ir.ui.view']._render_template("theme_reflect.cart_sidebar_content", values)

    @http.route(['/theme_reflect/get_categories'], type='json', auth="public", website=True)
    def get_categories(self, **post):
        """Returns HTML for the category grid."""
        categories = request.env['product.public.category'].search([
            ('parent_id', '=', False),
            ('image_1920', '!=', False)
        ], limit=4)
        values = {
            'categories': categories,
        }
        return request.env['ir.ui.view']._render_template("theme_reflect.s_reflect_category_grid_content", values)

    @http.route(['/theme_reflect/get_new_arrivals'], type='json', auth="public", website=True)
    def get_new_arrivals(self, **post):
        """Returns HTML for the new arrivals grid."""
        products = request.env['product.template'].search([
            ('is_published', '=', True),
            ('website_id', 'in', (False, request.website.id))
        ], order='create_date desc', limit=4)
        products_in_wishlist = request.env['product.template']
        if 'product.wishlist' in request.env:
            try:
                products_in_wishlist = request.env['product.wishlist'].current().product_id.product_tmpl_id
            except Exception:
                pass
        values = {
            'products': products,
            'products_in_wishlist': products_in_wishlist,
        }
        return request.env['ir.ui.view']._render_template("theme_reflect.s_reflect_new_arrivals_content", values)

    @http.route(['/theme_reflect/get_product_highlight'], type='json', auth="public", website=True)
    def get_product_highlight(self, **post):
        """Returns HTML for the product highlight (Best Sellers)."""
        products = request.env['product.template'].search([
            ('is_published', '=', True),
            ('website_id', 'in', (False, request.website.id))
        ], order='write_date desc', limit=4)
        products_in_wishlist = request.env['product.template']
        if 'product.wishlist' in request.env:
            try:
                products_in_wishlist = request.env['product.wishlist'].current().product_id.product_tmpl_id
            except Exception:
                pass
        values = {
            'products': products,
            'products_in_wishlist': products_in_wishlist,
        }
        return request.env['ir.ui.view']._render_template("theme_reflect.s_reflect_product_highlight_content", values)
