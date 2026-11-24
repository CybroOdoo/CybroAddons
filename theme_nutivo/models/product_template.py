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


class ProductTemplate(models.Model):
    """Values of the Nutivo product cards."""
    _inherit = 'product.template'

    def _nutivo_card_values(self, addons=True):
        """Return what a Nutivo product card shows for this product.

        The pack sizes of the card are the variants of the product, sorted
        by price, each with its price for the current visitor.

        :param bool addons: also give the optional products (the quick view).
        :return: the origin, notes, badge, rating and sizes of the card.
        :rtype: dict
        """
        self.ensure_one()
        sizes = []
        for variant in self.product_variant_ids:
            info = variant._get_combination_info_variant()
            sizes.append({
                'product_id': variant.id,
                'label': ', '.join(
                    variant.product_template_attribute_value_ids.mapped(
                        'name')),
                'price': info['price'],
                'price_str': self.env.website._nutivo_price(
                    info['price'], info['currency']),
                'available': variant._is_add_to_cart_allowed()
                and not variant._is_sold_out(),
                'custom_ptav_ids': variant.product_template_attribute_value_ids
                .filtered('is_custom').ids,
            })
        sizes.sort(key=lambda size: (not size['available'], size['price']))
        ribbon = self.sudo().website_ribbon_id
        category = self.public_categ_ids[:1]
        # The review figures are public on the shop, as on the product page.
        rating = self.sudo()
        return {
            'origin': category.name or '',
            'notes': self.description_sale or '',
            'badge': ribbon.name or '',
            'badge_gold': bool(ribbon) and 'best' in ribbon.name.lower(),
            'rating': round(rating.rating_avg, 1),
            'reviews': rating.rating_count,
            'rating_pct': round(rating.rating_avg / 5 * 100, 1),
            'sizes': sizes,
            'configurable': self._nutivo_needs_options(),
            'needs_page': self._nutivo_needs_page(),
            'extra_options': self._nutivo_extra_options(),
            'addons': self._nutivo_addons() if addons else [],
        }

    def _nutivo_addons(self):
        """Return the optional products the quick view offers with this one.

        :return: the card values of each published optional product, with
            the product itself under ``product``.
        :rtype: list
        """
        self.ensure_one()
        result = []
        for optional in self.sudo().optional_product_ids:
            if not (optional.is_published and optional.sale_ok):
                continue
            optional = optional.with_env(self.env)
            values = optional._nutivo_card_values(addons=False)
            result.append({'product': optional, 'values': values})
        return result

    def _nutivo_needs_page(self):
        """Tell whether the product can only be configured on its own page.

        Combos, and optional products that ask for a custom text or are
        combos themselves, cannot be chosen from a quick view.

        :rtype: bool
        """
        self.ensure_one()
        product = self.sudo()
        return bool(product.type == 'combo' or any(
            optional.type == 'combo' or any(
                optional.valid_product_template_attribute_line_ids
                .product_template_value_ids.mapped('is_custom'))
            for optional in product.optional_product_ids))

    def _nutivo_extra_options(self):
        """Return the options that do not make a variant, for the quick view.

        They are the attributes set to never create variants: the choice is
        kept on the order line. A custom value asks the visitor for a text.

        :return: one dict per attribute with its values.
        :rtype: list
        """
        self.ensure_one()
        result = []
        for line in self.sudo().valid_product_template_attribute_line_ids:
            if line.attribute_id.create_variant != 'no_variant':
                continue
            values = []
            for ptav in line.product_template_value_ids.filtered(
                    'ptav_active'):
                values.append({
                    'id': ptav.id,
                    'name': ptav.name,
                    'is_custom': ptav.is_custom,
                    'price_extra': (
                        self.env.website._nutivo_price(ptav.price_extra)
                        if ptav.price_extra else ''),
                })
            if values:
                result.append({'name': line.attribute_id.name,
                               'values': values})
        return result

    def _nutivo_needs_options(self):
        """Tell whether the product cannot be added to the cart from a card.

        Products with optional products, custom or dynamic values, or a
        combo must be configured on their own page, as in the shop.

        :rtype: bool
        """
        self.ensure_one()
        product = self.sudo()
        return bool(
            product.optional_product_ids
            or product.type == 'combo'
            or product.attribute_line_ids.filtered(
                lambda line: line.attribute_id.create_variant == 'no_variant'
                or any(line.value_ids.mapped('is_custom'))))
