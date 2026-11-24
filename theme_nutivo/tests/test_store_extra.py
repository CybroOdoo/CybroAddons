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
from unittest.mock import patch

from odoo.tests import tagged

from odoo.addons.theme_nutivo.controllers.theme_nutivo import NutivoStore
from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon


@tagged('post_install', '-at_install')
class TestNutivoExtra(WebsiteSaleCommon):
    """Test the edge cases of the helpers, the bag, the chips and the
    account menu."""

    @classmethod
    def setUpClass(cls):
        """Apply the theme and keep the test product."""
        super().setUpClass()
        cls.env['ir.module.module'].search(
            [('name', '=', 'theme_nutivo')], limit=1)._theme_load(cls.website)
        cls.template = cls.product.product_tmpl_id.sudo()

    def _template(self):
        """Return the test product template with the rights to change it."""
        return self.env['product.template'].sudo().browse(self.template.id)

    def _category(self, name, products=1):
        """Create a shop category holding the given number of products."""
        category = self.env['product.public.category'].sudo().create(
            {'name': name})
        for index in range(products):
            self.env['product.template'].sudo().create({
                'name': '{} Product {}'.format(name, index),
                'is_published': True,
                'public_categ_ids': [(6, 0, category.ids)],
            })
        return category

    def test_theme_load_other_module(self):
        """Loading another theme leaves the Nutivo views alone."""
        other = self.env['ir.module.module'].search(
            [('name', '=', 'website_sale')], limit=1)
        with patch(
                'odoo.addons.website.models.ir_module_module.IrModuleModule.'
                '_theme_load', return_value=True):
            self.assertTrue(other._theme_load(self.website))

    def test_price_after_symbol(self):
        """A currency with the symbol after the figure keeps a space."""
        currency = self.env['res.currency'].sudo().create({
            'name': 'NTA', 'symbol': 'kr', 'position': 'after',
            'rounding': 0.01,
        })
        self.assertEqual(
            self.website._nutivo_price(10.0, currency), '10\N{NO-BREAK SPACE}kr')

    def test_attribute_value_count(self):
        """The count is the number of shop products having the value."""
        attribute = self.env['product.attribute'].sudo().create({
            'name': 'Nutivo Count', 'value_ids': [(0, 0, {'name': 'One'})],
        })
        value = attribute.value_ids
        self.assertEqual(self.website._nutivo_attribute_value_count(value), 0)
        self._template().write({'attribute_line_ids': [(0, 0, {
            'attribute_id': attribute.id, 'value_ids': [(6, 0, value.ids)],
        })]})
        self.assertEqual(self.website._nutivo_attribute_value_count(value), 1)

    def test_categories_details(self):
        """Empty categories are left out; more than three products add
        "& more"; a category image is used when there is one."""
        empty = self.env['product.public.category'].sudo().create(
            {'name': 'Nutivo Empty'})
        full = self._category('Nutivo Full', products=4)
        full.image_128 = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8Dw'
            'HwAFBQIAX8jx0gAAAABJRU5ErkJggg==')
        entries = {c['name']: c for c in self.website._nutivo_categories()}
        self.assertNotIn(empty.name, entries)
        self.assertIn('& more', entries['Nutivo Full']['description'])
        self.assertIn('product.public.category', entries['Nutivo Full']['image'])

    def test_extra_options_skips(self):
        """Attributes that make variants, or with no active value, are left
        out."""
        always = self.env['product.attribute'].sudo().create({
            'name': 'Nutivo Always',
            'value_ids': [(0, 0, {'name': 'A'}), (0, 0, {'name': 'B'})],
        })
        hidden = self.env['product.attribute'].sudo().create({
            'name': 'Nutivo Hidden', 'create_variant': 'no_variant',
            'value_ids': [(0, 0, {'name': 'H'})],
        })
        template = self.env['product.template'].sudo().create({
            'name': 'Nutivo Skips', 'is_published': True,
            'attribute_line_ids': [
                (0, 0, {'attribute_id': always.id,
                        'value_ids': [(6, 0, always.value_ids.ids)]}),
                (0, 0, {'attribute_id': hidden.id,
                        'value_ids': [(6, 0, hidden.value_ids.ids)]}),
            ],
        })
        template.attribute_line_ids.product_template_value_ids.filtered(
            lambda v: v.attribute_id == hidden).ptav_active = False
        self.assertFalse(template._nutivo_extra_options())

    def test_cards_skip_products_without_sizes(self):
        """A product without variants gives no card."""
        template = self.env['product.template'].sudo().create({
            'name': 'Nutivo No Variant', 'is_published': True})
        template.product_variant_ids.active = False
        with MockRequest(self.env, website=self.website) as request:
            cards = NutivoStore()._product_cards(
                request.env['product.template'].browse(template.id))
        self.assertEqual(cards, [])

    def test_chips_limit(self):
        """The chips skip empty categories and stop at the limit."""
        self.env['product.public.category'].sudo().create(
            {'name': 'Nutivo Chip Empty'})
        self._category('Nutivo Chip A')
        self._category('Nutivo Chip B')
        with MockRequest(self.env, website=self.website):
            result = NutivoStore().products(chips=True, max_categories=1)
        self.assertIn('chips', result)
        self.assertNotIn('Nutivo Chip B', result['chips'])
        self.assertNotIn('Nutivo Chip Empty', result['chips'])

    def test_bag_suggestions_full(self):
        """Three accessories of the bag are all that is suggested."""
        accessories = self.env['product.template'].sudo().create([
            {'name': 'Nutivo Accessory %s' % i, 'is_published': True}
            for i in range(3)])
        self._template().accessory_product_ids = [
            (6, 0, accessories.product_variant_ids.ids)]
        with MockRequest(
                self.env, website=self.website, sale_order_id=self.cart.id):
            result = NutivoStore().bag()
        for accessory in accessories:
            self.assertIn(accessory.name, result['html'])

    def test_wishlist_toggle(self):
        """A product is saved to the wishlist, then removed."""
        variant = self.product.sudo()
        with MockRequest(self.env, website=self.website):
            added = NutivoStore().wishlist_toggle(variant.id)
            self.assertTrue(added['on'])
            self.assertEqual(added['product_ids'], variant.ids)
            removed = NutivoStore().wishlist_toggle(variant.id)
        self.assertFalse(removed['on'])
        self.assertEqual(removed['product_ids'], [])

    def _order(self, state, delivered=0.0):
        """Create an order of the user in the given state."""
        order = self.env['sale.order'].sudo().create({
            'partner_id': self.env.user.partner_id.id,
            'website_id': self.website.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id, 'product_uom_qty': 2})],
        })
        order.state = state
        line = order.order_line
        if delivered:
            line.qty_delivered_method = 'manual'
            line.qty_delivered = delivered
        return order

    def test_account_menu_stages(self):
        """The latest order shows its stage; the active ones are counted."""
        self._order('cancel')
        self._order('sale', delivered=2.0)
        self._order('sale', delivered=1.0)
        self.assertEqual(
            self.website._nutivo_account_menu()['latest']['label'], 'Shipped')
        self.assertEqual(self.website._nutivo_account_menu()['active'], 1)
        self._order('sale')
        menu = self.website._nutivo_account_menu()
        self.assertIn(menu['latest']['label'], ('Order placed', 'Packed'))

    def test_account_menu_without_orders(self):
        """A user without orders has no latest order."""
        menu = self.website._nutivo_account_menu()
        self.assertIsNone(menu['latest'])
        self.assertEqual(menu['active'], 0)
