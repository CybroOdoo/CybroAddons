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
import logging
import re

from odoo import Command, http
from odoo.http import request, route

_logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class VeloraCart(http.Controller):
    """Controller handling side-panel cart drawer JSON-RPC requests."""

    def _empty_cart_payload(self):
        website = getattr(request, 'website', None)
        currency = (website and website.currency_id) or request.env.company.currency_id
        return {
            'items': [],
            'subtotal': 0,
            'cart_quantity': 0,
            'currency_symbol': currency.symbol or '$',
            'currency_position': currency.position or 'before',
        }

    @route('/theme_velora/cart/data', type='jsonrpc', auth='public', website=True)
    def cart_data(self):
        """Return the cart lines, totals and currency configuration."""
        order = request.cart
        if not order or not order.order_line:
            return self._empty_cart_payload()

        items = []
        lines = order.order_line.filtered(
            lambda line: not line.is_delivery and not getattr(line, 'is_reward_line', False)
        )
        for line in lines:
            product = line.product_id
            items.append({
                'line_id': line.id,
                'product_id': product.id,
                'name': line.name_short,
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
        """Update the quantity of a line in the active cart.

        Goes through the standard cart API so stock and pricing checks run.
        """
        order = request.cart
        if order:
            line = order.order_line.filtered(lambda rec: rec.id == int(line_id))
            if line:
                quantity = int(quantity)
                if quantity <= 0:
                    line.unlink()
                    order._verify_cart_after_update()
                else:
                    order._cart_update_line_quantity(line_id=line.id, quantity=quantity)
        return self.cart_data()

    @route('/theme_velora/cart/remove', type='jsonrpc', auth='public', website=True)
    def remove_item(self, line_id):
        """Remove a line from the active cart."""
        order = request.cart
        if order:
            line = order.order_line.filtered(lambda rec: rec.id == int(line_id))
            if line:
                line.unlink()
                order._verify_cart_after_update()
        return self.cart_data()


class VeloraPages(http.Controller):
    """Helper endpoints for Theme Velora.

    The /about, /bestsellers and /collections pages are served by the
    theme.website.page records, so they have no controller routes here.
    """

    @route('/theme_velora/category/<string:name>', type='http', auth='public',
           website=True, sitemap=False)
    def fragrance_category_redirect(self, name, **kw):
        """Redirect to the matching public category in the shop, by name."""
        clean_name = (name or '').strip()
        category = request.env['product.public.category'].sudo().search([
            ('name', '=ilike', clean_name),
        ], limit=1)
        if category:
            return request.redirect(f'/shop/category/{category.id}')
        return request.redirect(f'/shop?search={clean_name}')

    @route('/theme_velora/newsletter/subscribe', type='jsonrpc', auth='public', website=True)
    def newsletter_subscribe(self, email=None, **kw):
        """Store the subscriber as a mailing contact.

        Returns ``success: True`` only when the contact exists afterwards.
        """
        clean_email = (email or '').strip()
        if not EMAIL_PATTERN.match(clean_email):
            return {'success': False, 'error': 'Invalid email address.'}
        try:
            mailing_list = request.env.ref(
                'theme_velora.mailing_list_velora_circle', raise_if_not_found=False)
            list_commands = [Command.link(mailing_list.id)] if mailing_list else []
            contacts = request.env['mailing.contact'].sudo()
            contact = contacts.search([('email', '=ilike', clean_email)], limit=1)
            if contact:
                if list_commands:
                    contact.write({'list_ids': list_commands})
            else:
                contacts.create({
                    'email': clean_email,
                    'name': clean_email.split('@')[0],
                    'list_ids': list_commands,
                })
        except Exception:
            _logger.exception("Newsletter subscription failed for %s", clean_email)
            return {'success': False, 'error': 'Subscription failed. Please try again.'}
        return {'success': True}