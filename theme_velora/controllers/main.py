# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request


class ThemeVeloraCart(http.Controller):
    """Serves the real Odoo cart content for the Velora header cart drawer."""

    @http.route('/theme_velora/cart_drawer', type='json', auth='public', website=True)
    def cart_drawer(self):
        order = request.website.sale_get_order()
        lines = []
        for line in (order.website_order_line if order else []):
            if not line.product_id:
                continue
            lines.append({
                'line_id': line.id,
                'product_id': line.product_id.id,
                'name': line.name_short or line.product_id.name,
                'qty': line._get_displayed_quantity(),
                'price': line._get_cart_display_price(),
                'image_url': f'/web/image/product.product/{line.product_id.id}/image_128',
            })
        try:
            cart_total = request.env['ir.ui.view']._render_template(
                'website_sale.total', {'website_sale_order': order}
            )
        except Exception:
            cart_total = ''
        return {
            'lines': lines,
            'website_sale.total': cart_total,
            'cart_quantity': order.cart_quantity if order else 0,
            'currency_symbol': order.currency_id.symbol if order else '$',
        }


class ThemeVeloraCollections(http.Controller):
    """Handles redirecting collection routes to Odoo eCommerce categories."""

    @http.route('/collections/<string:collection_name>', type='http', auth='public', website=True)
    def get_collection(self, collection_name, **kwargs):
        """Finds the matching eCommerce category and redirects, else falls back to all categories."""
        mapping = {
            'mens_collection': ['Mens collection', "Men's Collection", 'Mens Collection', 'men'],
            'womens_collection': ['womens collection', "Women's Collection", 'Womens Collection', 'women'],
            'unisex': ['Unisex', 'unisex'],
            'luxury_gift_sets': ['lexury gift sets', 'luxury gift sets', 'Luxury Gift Sets', 'gift sets', 'Gift Sets'],
            'limited_editions': ['Limited Editions', 'limited editions']
        }
        
        search_terms = mapping.get(collection_name, [collection_name])
        category = False
        
        # Try exact case-insensitive matches first
        for term in search_terms:
            category = request.env['product.public.category'].sudo().search([
                ('name', '=ilike', term)
            ], limit=1)
            if category:
                break
                
        # Try substring case-insensitive matches next
        if not category:
            for term in search_terms:
                category = request.env['product.public.category'].sudo().search([
                    ('name', 'ilike', term)
                ], limit=1)
                if category:
                    break
                    
        if category:
            return request.redirect(f'/shop/category/{category.id}')
        return request.redirect('/shop')

    @http.route('/collections/redirect', type='http', auth='public', website=True)
    def redirect_collection(self, name=None, **kwargs):
        """Finds the matching eCommerce category by frontend name and redirects, else falls back to shop."""
        if not name or not name.strip():
            return request.redirect('/shop')

        raw_name = name.strip()
        name_clean = raw_name.lower()
        search_terms = [raw_name, name_clean]

        cleaned = name_clean.replace("collection", "").replace("collections", "").replace("'s", "").replace("`s", "").strip()
        if cleaned and cleaned not in search_terms:
            search_terms.append(cleaned)

        if 'men' in name_clean:
            search_terms.extend(["Men's Collection", 'Mens Collection', 'men'])
        if 'women' in name_clean:
            search_terms.extend(["Women's Collection", 'Womens Collection', 'women'])
        if 'unisex' in name_clean:
            search_terms.extend(['unisex'])
        if 'gift' in name_clean:
            search_terms.extend(['Luxury Gift Sets', 'gift sets', 'gift'])
        if 'limited' in name_clean:
            search_terms.extend(['Limited Editions', 'limited'])

        Category = request.env['product.public.category'].sudo()
        category = False

        # 1. Try exact case-insensitive matches first
        for term in search_terms:
            if not term:
                continue
            category = Category.search([('name', '=ilike', term)], limit=1)
            if category:
                break

        # 2. Try substring case-insensitive matches next
        if not category:
            for term in search_terms:
                if not term or len(term) < 2:
                    continue
                category = Category.search([('name', 'ilike', term)], limit=1)
                if category:
                    break

        if category:
            return request.redirect(f'/shop/category/{category.id}')
        return request.redirect('/shop')



class ThemeVeloraAboutUs(http.Controller):

    @http.route(['/aboutus', '/about'], type='http', auth='public', website=True)
    def about_page_redirect(self, **kwargs):
        return request.redirect('/about-us', code=301)


class ThemeVeloraBestsellers(http.Controller):

    @http.route(['/bestsellers', '/best-sellers'], type='http', auth='public', website=True, sitemap=True)
    def bestsellers(self, **kw):
        return request.render('theme_velora.theme_velora_bestsellers')
