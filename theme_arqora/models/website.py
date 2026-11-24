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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from urllib.parse import urlencode

from odoo import fields, models


class Website(models.Model):
    """Data of the dynamic blocks of the Arqora home page."""
    _inherit = 'website'

    prevent_sale_for = fields.Selection(
        selection_add=[('quote_only', 'Products Marked as Request a Quote')],
        ondelete={'quote_only': 'set default'})

    def _prevent_product_sale(self, product_or_template, is_zero_price_product):
        """Also prevent the sale of the products marked Request a Quote.

        :param product_or_template: the product.product or product.template.
        :param bool is_zero_price_product: whether its price is zero.
        :return: whether selling the product online is prevented.
        :rtype: bool
        """
        if self.prevent_sale and self.prevent_sale_for == 'quote_only':
            return self._arqora_is_quote_only(product_or_template)
        return super()._prevent_product_sale(
            product_or_template, is_zero_price_product)

    def _arqora_is_quote_only(self, product_or_template):
        """Tell whether a product is sold on quotation only.

        :param product_or_template: the product.product or product.template.
        :rtype: bool
        """
        template = product_or_template
        if product_or_template._name == 'product.product':
            template = product_or_template.product_tmpl_id
        return bool(template.quote_only)

    def _arqora_quote_url(self, product=None, finish=''):
        """Build the link of the Request a Quote button.

        It opens the contact form on the architect tab, with the product
        (and the finish) the visitor asks a quote for.

        :param product: the product.template of the quotation.
        :param str finish: the name of the chosen finish.
        :rtype: str
        """
        base_url = self.contact_us_link_url or '/contactus'
        query = {'type': 'architect'}
        if product:
            query['product'] = product.id
        if finish:
            query['finish'] = finish
        return '{}?{}'.format(base_url, urlencode(query))

    def _arqora_price(self, amount, currency=None):
        """Format a price the way the Arqora cards show it.

        Whole amounts are shown without decimals, with the thousands
        separated (``€2,450``).

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

    def _arqora_collections(self, limit=6):
        """Return the top level shop categories shown as lamp tiles.

        :param int limit: the maximum number of categories.
        :return: one dict per published category that has products, with its
            name, link, picture, number of products and lowest price.
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
            products = Product.search([
                ('public_categ_ids', 'child_of', category.id),
                *self.sale_product_domain(),
            ], order='website_sequence, id')
            if not products:
                continue
            if category.image_128:
                image = '/web/image/product.public.category/{}/image_1024'.format(
                    category.id)
            else:
                image = '/web/image/product.template/{}/image_1024'.format(
                    products[0].id)
            prices = [price for price in products.mapped('list_price') if price]
            result.append({
                'name': category.name,
                'url': category.website_url,
                'image': image,
                'count': len(products),
                'from_price': self._arqora_price(min(prices)) if prices else '',
            })
            if len(result) >= limit:
                break
        return result

    def _arqora_signature(self, limit=5):
        """Return the products of the Objects of Light mosaic.

        :param int limit: the maximum number of products.
        :return: the first published products, one dict each.
        :rtype: list
        """
        self.ensure_one()
        products = self.env['product.template'].search(
            self.sale_product_domain(), order='website_sequence, id',
            limit=limit)
        return [{
            'name': product.name,
            'url': product.website_url,
            'image': '/web/image/product.template/{}/image_1024'.format(product.id),
            'category': product.public_categ_ids[:1].name or '',
            'tagline': product.description_sale or '',
            'price': self._arqora_price(product.list_price),
        } for product in products]
