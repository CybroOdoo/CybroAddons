# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models

# Free shipping threshold shown by the bag drawer, in the website currency.
FREE_SHIPPING_PARAM = 'theme_nutivo.free_shipping_amount'
FREE_SHIPPING_DEFAULT = 999.0


class Website(models.Model):
    """Data of the Nutivo header and bag drawer."""
    _inherit = 'website'

    def _nutivo_categories(self, limit=None):
        """Return the top level shop categories shown by the Shop menu.

        Each entry gives the name, link, picture, product count and a short
        description built from the names of the first products.

        :param int limit: keep only the first categories that have products.
        :return: one dict per published top level category.
        :rtype: list
        """
        self.ensure_one()
        Product = self.env['product.template']
        categories = self.env['product.public.category'].search([
            ('parent_id', '=', False),
            *self.website_domain(),
        ])
        result = []
        for category in categories:
            domain = [
                ('public_categ_ids', 'child_of', category.id),
                *self.sale_product_domain(),
            ]
            products = Product.search(domain, limit=3)
            if not products:
                continue
            names = products.mapped('name')
            description = ', '.join(names)
            if Product.search_count(domain, limit=4) > 3:
                description = self.env._('%s & more', description)
            if category.image_128:
                image = '/web/image/product.public.category/{}/image_256'.format(
                    category.id)
            else:
                image = '/web/image/product.template/{}/image_256'.format(
                    products[0].id)
            result.append({
                'name': category.name,
                'url': category.website_url,
                'image': image,
                'count': Product.search_count(domain),
                'description': description,
            })
            if limit and len(result) >= limit:
                break
        return result

    def _nutivo_attribute_value_count(self, value):
        """Count the products of the shop that have an attribute value.

        It is the figure next to the options of the shop filters.

        :param value: a `product.attribute.value` record.
        :rtype: int
        """
        self.ensure_one()
        return self.env['product.template'].search_count([
            ('attribute_line_ids.value_ids', '=', value.id),
            *self.sale_product_domain(),
        ])

    def _nutivo_price(self, amount, currency=None):
        """Format a price the way the Nutivo cards show it.

        The symbol is set against the figure (``₹1,399``). Whole amounts are
        shown without decimals, other amounts with the decimals of the
        currency (``₹458.85``).

        :param float amount: the price.
        :param currency: the currency, the website one by default.
        :rtype: str
        """
        currency = currency or self.currency_id
        amount = currency.round(amount)
        if currency.is_zero(amount - round(amount)):
            figure = '{:,}'.format(int(round(amount)))
        else:
            figure = '{:,.{}f}'.format(amount, currency.decimal_places)
        if currency.position == 'after':
            return '{}\N{NO-BREAK SPACE}{}'.format(figure, currency.symbol)
        return '{}{}'.format(currency.symbol, figure)

    def _nutivo_free_shipping_amount(self):
        """Return the order amount from which the bag drawer announces free
        shipping, 0 when the meter is disabled.

        :rtype: float
        """
        value = self.env['ir.config_parameter'].sudo().get_float(
            FREE_SHIPPING_PARAM, FREE_SHIPPING_DEFAULT)
        return max(value, 0.0)

    def _nutivo_account_menu(self):
        """Return the data of the account dropdown of the header.

        :return: the initials, name and email of the user, the latest order
            with its delivery stage, and the number of orders in progress.
        :rtype: dict
        """
        self.ensure_one()
        partner = self.env.user.partner_id
        words = [w for w in (partner.name or '').split() if w[:1].isalpha()]
        initials = ''.join(w[0] for w in (words[:1] + words[-1:] if len(words) > 1 else words[:1]))
        orders = self.env['sale.order'].sudo().search([
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('state', 'in', ('sale', 'done', 'cancel')),
        ], order='date_order desc, id desc', limit=20)
        stages = []
        for order in orders:
            # The delivered quantities of the order lines tell the progress:
            # the inventory app fills them from the deliveries, and without it
            # they are entered by hand on the order.
            lines = order.order_line.filtered(
                lambda line: line.product_id and not line.is_delivery
                and not line.display_type and line.product_uom_qty)
            delivered = sum(min(line.qty_delivered, line.product_uom_qty) for line in lines)
            ordered = sum(lines.mapped('product_uom_qty'))
            pickings = order.picking_ids.filtered(lambda pick: pick.state != 'cancel') \
                if 'picking_ids' in order._fields else []
            if order.state == 'cancel':
                stage = (self.env._('Cancelled'), 'cancelled', 0)
            elif lines and delivered >= ordered or order.state == 'done':
                stage = (self.env._('Delivered'), 'delivered', 100)
            elif delivered:
                stage = (self.env._('Shipped'), 'active', 66)
            elif any(p.state == 'assigned' for p in pickings):
                stage = (self.env._('Packed'), 'active', 33)
            else:
                stage = (self.env._('Order placed'), 'active', 8)
            stages.append(stage)
        latest = None
        if orders:
            latest = {
                'name': orders[0].name,
                'url': orders[0].get_portal_url(),
                'label': stages[0][0],
                'tone': stages[0][1],
                'pct': stages[0][2],
            }
        return {
            'initials': initials.upper(),
            'name': partner.name or '',
            'first_name': words[0] if words else '',
            'email': partner.email or self.env.user.login,
            'latest': latest,
            'active': sum(1 for stage in stages if stage[1] == 'active'),
            'internal': self.env.user._is_internal(),
        }
