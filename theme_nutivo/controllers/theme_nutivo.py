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
from odoo.http import Controller, request, route
from odoo.tools import str2bool

from odoo.addons.website_sale.controllers.wishlist import ProductWishlist

# Sort keys of the product grids, as offered by their sort menu.
SORT_KEYS = {
    'price-asc': (lambda values: values['sizes'][0]['price'], False),
    'price-desc': (lambda values: values['sizes'][0]['price'], True),
    'rating': (lambda values: (values['rating'], values['reviews']), True),
    'popular': (lambda values: values['reviews'], True),
}
MAX_CARDS = 24
MAX_CHIPS = 12


class NutivoStore(Controller):
    """Serve the dynamic parts of the Nutivo storefront.

    Only the presentation lives here: products, prices, taxes, the cart and
    the wishlist are the eCommerce records of the visitor.
    """

    def _render(self, template, values):
        """Render a theme template with the website rendering context."""
        return request.env['ir.ui.view']._render_template(template, values)

    def _wished_templates(self):
        """Return the products of the wishlist of the visitor."""
        return request.env['product.wishlist'].current().product_id.product_tmpl_id

    def _product_cards(self, products):
        """Return the card values of the products that can be sold."""
        cards = []
        for product in products:
            values = product._nutivo_card_values()
            if values['sizes']:
                cards.append({'product': product, 'values': values})
        return cards

    def _find_category(self, category):
        """Return the public category matching an id or a name."""
        Category = request.env['product.public.category']
        if not category or category == 'all':
            return Category
        if str(category).isdigit():
            return Category.search([
                ('id', '=', int(category)),
                *request.env.website.website_domain(),
            ], limit=1)
        return Category.search([
            ('name', 'ilike', category),
            *request.env.website.website_domain(),
        ], limit=1)

    @route('/theme_nutivo/products', type='jsonrpc', auth='public',
           website=True, sitemap=False, readonly=True)
    def products(self, category=None, limit=8, sort='featured',
                 card='product', chips=False, max_categories=5):
        """Render the product cards of a Nutivo product grid.

        :param category: id or name of a shop category, or 'all'.
        :param int limit: the maximum number of cards.
        :param str sort: featured, price-asc, price-desc, rating or popular.
        :param str card: 'product' or 'hamper', the card design.
        :param bool chips: also render the category chips of the grid.
        :param int max_categories: the maximum number of category chips.
        :return: the cards, and the chips when asked.
        :rtype: dict
        """
        website = request.env.website
        limit = max(1, min(int(limit or 8), MAX_CARDS))
        domain = list(website.sale_product_domain())
        category_rec = self._find_category(category)
        if category_rec:
            domain.append(('public_categ_ids', 'child_of', category_rec.id))
        products = request.env['product.template'].search(
            domain, order='website_sequence, id', limit=MAX_CARDS * 2)
        cards = self._product_cards(products)
        if sort in SORT_KEYS:
            key, reverse = SORT_KEYS[sort]
            cards.sort(key=lambda c: key(c['values']), reverse=reverse)
        result = {
            'html': self._render('theme_nutivo.product_cards', {
                'cards': cards[:limit],
                'card_design': 'hamper' if card == 'hamper' else 'product',
                'wished': self._wished_templates(),
                'with_quick_view': card != 'hamper',
            }),
        }
        if str2bool(str(chips), False):
            max_chips = max(1, min(int(max_categories or 5), MAX_CHIPS))
            Product = request.env['product.template']
            categories = request.env['product.public.category']
            for category_rec in categories.search([
                ('parent_id', '=', False),
                *website.website_domain(),
            ]):
                if Product.search_count([
                    ('public_categ_ids', 'child_of', category_rec.id),
                    *website.sale_product_domain(),
                ], limit=1):
                    categories |= category_rec
                if len(categories) >= max_chips:
                    break
            result['chips'] = self._render('theme_nutivo.category_chips', {
                'categories': categories,
            })
        return result

    @route('/theme_nutivo/quick_view', type='jsonrpc', auth='public',
           website=True, sitemap=False, readonly=True)
    def quick_view(self, product_template_id):
        """Render the quick view of a product the visitor can buy.

        :param int product_template_id: the product to show.
        :return: the quick view content, empty if the product is not available.
        :rtype: str
        """
        product = request.env['product.template'].search([
            ('id', '=', int(product_template_id)),
            *request.env.website.sale_product_domain(),
        ], limit=1)
        cards = self._product_cards(product)
        if not cards:
            return ''
        return self._render('theme_nutivo.quick_view_content', {
            'card': cards[0],
            'wished': self._wished_templates(),
            'free_shipping': request.env.website._nutivo_free_shipping_amount(),
            'currency': request.env.website.currency_id,
        })

    @route('/theme_nutivo/bag', type='jsonrpc', auth='public',
           website=True, sitemap=False)
    def bag(self):
        """Render the bag drawer from the current website cart.

        :return: the drawer content and the number of items in the cart.
        :rtype: dict
        """
        website = request.env.website
        order_sudo = request.cart
        empty_lines = request.env['sale.order.line']
        lines = order_sudo.website_order_line if order_sudo else empty_lines
        currency = order_sudo.currency_id if order_sudo else website.currency_id
        subtotal = sum(line._get_cart_display_price() for line in lines
                       if line.price_unit >= 0)
        discount = -sum(line._get_cart_display_price() for line in lines
                        if line.price_unit < 0)
        delivery_lines = order_sudo.order_line.filtered('is_delivery') \
            if order_sudo else empty_lines
        free_at = website._nutivo_free_shipping_amount()
        after_discount = subtotal - discount
        checkout_href = '/shop/checkout?try_skip_step=true'
        if lines:
            checkout_href = website._get_checkout_step_values(
                '/shop/cart', order_sudo)['next_website_checkout_step_href']
        in_bag = lines.product_id.product_tmpl_id
        # Accessories of the products in the bag come first, then the top
        # products of the shop; nothing already in the bag is suggested.
        suggestions = request.env['product.product'].browse(
            [p.id for p in order_sudo._cart_accessories()]
        ).filtered(
            lambda product: product.product_tmpl_id not in in_bag
        )[:3] if lines else request.env['product.product']
        if len(suggestions) < 3:
            others = request.env['product.template'].search([
                ('id', 'not in', (in_bag | suggestions.product_tmpl_id).ids),
                *website.sale_product_domain(),
            ], order='website_sequence, id', limit=3 - len(suggestions))
            suggestions |= others.product_variant_id
        count = order_sudo.cart_quantity if order_sudo else 0
        return {
            'html': self._render('theme_nutivo.bag_content', {
                'order': order_sudo,
                'lines': lines,
                'count': count,
                'currency': currency,
                'subtotal': subtotal,
                'discount': discount,
                'shipping': sum(delivery_lines.mapped('price_total')),
                'has_shipping': bool(delivery_lines),
                'taxes': order_sudo.amount_tax
                if order_sudo and website.show_line_subtotals_tax_selection
                == 'tax_excluded' else 0.0,
                'total': order_sudo.amount_total if order_sudo else 0.0,
                'free_at': free_at,
                'remaining': max(0.0, free_at - after_discount),
                'meter_pct': min(100.0, after_discount / free_at * 100)
                if free_at else 0,
                'suggestions': suggestions,
                'checkout_href': checkout_href,
                'redirect': request.httprequest.referrer or '/shop',
            }),
            'cart_quantity': count,
        }

    @route('/theme_nutivo/wishlist', type='jsonrpc', auth='public',
           website=True, sitemap=False)
    def wishlist(self):
        """Render the products saved in the wishlist of the visitor.

        :return: the drawer content, the saved variants and their number.
        :rtype: dict
        """
        wishes = request.env['product.wishlist'].current()
        return {
            'html': self._render('theme_nutivo.wishlist_content', {
                'wishes': wishes,
                'cards': {
                    card['product'].id: card['values']
                    for card in self._product_cards(
                        wishes.product_id.product_tmpl_id)
                },
            }),
            'product_ids': wishes.product_id.ids,
        }

    @route('/theme_nutivo/wishlist/toggle', type='jsonrpc', auth='public',
           website=True, sitemap=False)
    def wishlist_toggle(self, product_id):
        """Save a product to the wishlist, or remove it if it is saved.

        The wishlist routes of the eCommerce do the work, so the rules of
        the public and signed in visitors are the standard ones.

        :param int product_id: a variant of the product, as `product.product`.
        :return: whether the product is now saved, and the saved variants.
        :rtype: dict
        """
        product = request.env['product.product'].browse(int(product_id)).exists()
        if not product:
            return {'on': False, 'product_ids': []}
        wishlist_controller = ProductWishlist()
        wishes = request.env['product.wishlist'].current().filtered(
            lambda w: w.product_id.product_tmpl_id == product.product_tmpl_id)
        if wishes:
            for wish in wishes:
                wishlist_controller.remove_from_wishlist(wish.id)
        else:
            wishlist_controller.add_to_wishlist(product.id)
        return {
            'on': not wishes,
            'product_ids': request.env['product.wishlist'].current().product_id.ids,
        }

