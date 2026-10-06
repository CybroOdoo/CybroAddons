# -*- coding: utf-8 -*-
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
from odoo.http import request, route


class VeloraCart(http.Controller):
    """Controller handling side-panel cart drawer AJAX / JSON-RPC requests."""

    @route('/theme_velora/cart/data', type='jsonrpc', auth='public', website=True)
    def cart_data(self):
        """Fetch and return shopping cart items, totals, and currency configuration.

        Returns:
            dict: JSON data structure containing line items, subtotal, cart quantity,
                  currency symbol, and currency position.
        """
        order = request.cart
        if not order or not order.order_line:
            return {
                'items': [],
                'subtotal': 0,
                'cart_quantity': 0,
                'currency_symbol': request.website.currency_id.symbol or '$',
                'currency_position': request.website.currency_id.position or 'before',
            }

        items = []
        for line in order.order_line.filtered(lambda l: not l.is_delivery and not getattr(l, 'is_reward_line', False)):
            product = line.product_id
            items.append({
                'line_id': line.id,
                'product_id': product.id,
                'name': line.name_short if hasattr(line, 'name_short') else product.display_name,
                'price': line.price_reduce_taxinc,
                'quantity': int(line.product_uom_qty),
                'subtotal': line.price_subtotal,
                'image_url': f'/web/image/product.product/{product.id}/image_128',
            })

        return {
            'items': items,
            'subtotal': order.amount_total,
            'cart_quantity': order.cart_quantity,
            'currency_symbol': order.currency_id.symbol or '$',
            'currency_position': order.currency_id.position or 'before',
        }

    @route('/theme_velora/cart/update_qty', type='jsonrpc', auth='public', website=True)
    def update_qty(self, line_id, quantity):
        """Update the quantity of a specific order line in the active shopping cart.

        Args:
            line_id (int|str): ID of the sale order line to update.
            quantity (int|str): Target quantity for the line item.

        Returns:
            dict: Updated cart payload as returned by `cart_data()`.
        """
        order = request.cart
        if order:
            line = order.order_line.filtered(lambda l: l.id == int(line_id))
            if line:
                if int(quantity) <= 0:
                    line.unlink()
                else:
                    line.product_uom_qty = int(quantity)
                order._verify_cart_after_update()
        return self.cart_data()

    @route('/theme_velora/cart/remove', type='jsonrpc', auth='public', website=True)
    def remove_item(self, line_id):
        """Remove an order line from the active shopping cart.

        Args:
            line_id (int|str): ID of the sale order line to remove.

        Returns:
            dict: Updated cart payload as returned by `cart_data()`.
        """
        order = request.cart
        if order:
            line = order.order_line.filtered(lambda l: l.id == int(line_id))
            if line:
                line.unlink()
                order._verify_cart_after_update()
        return self.cart_data()


class VeloraPages(http.Controller):
    """Controller rendering custom website pages for Theme Velora."""

    @route('/bestsellers', type='http', auth='public', website=True, sitemap=True)
    def bestsellers(self, **kw):
        """Render the Bestsellers page.

        Returns:
            http.Response: Rendered QWeb template 'theme_velora.theme_velora_bestsellers'.
        """
        return request.render('theme_velora.theme_velora_bestsellers')

    @route('/collections', type='http', auth='public', website=True, sitemap=True)
    def collections(self, **kw):
        """Render the Product Collections page.

        Returns:
            http.Response: Rendered QWeb template 'theme_velora.template_collections'.
        """
        return request.render('theme_velora.template_collections')

    @route('/about', type='http', auth='public', website=True, sitemap=True)
    def about(self, **kw):
        """Render the About Us page.

        Returns:
            http.Response: Rendered QWeb template 'theme_velora.theme_velora_aboutus'.
        """
        return request.render('theme_velora.theme_velora_aboutus')

    @route('/theme_velora/category/<string:name>', type='http', auth='public', website=True, sitemap=False)
    def fragrance_category_redirect(self, name, **kw):
        """Redirect to the matching product public category in shop by name."""
        clean_name = (name or '').strip()
        category = request.env['product.public.category'].sudo().search([
            ('name', '=ilike', clean_name)
        ], limit=1)
        if category:
            return request.redirect(f'/shop/category/{category.id}')
        return request.redirect(f'/shop?search={clean_name}')

    @route('/theme_velora/newsletter/subscribe', type='jsonrpc', auth='public', website=True)
    def newsletter_subscribe(self, email=None, **kw):
        """Handle newsletter subscription and store contact if mailing contact model is present."""
        if not email or '@' not in email:
            return {'success': False, 'error': 'Invalid email address.'}
        try:
            if 'mailing.contact' in request.env:
                clean_email = email.strip()
                contact = request.env['mailing.contact'].sudo().search([('email', '=ilike', clean_email)], limit=1)
                if not contact:
                    request.env['mailing.contact'].sudo().create({
                        'email': clean_email,
                        'name': clean_email.split('@')[0],
                    })
        except Exception:
            pass
        return {'success': True}


