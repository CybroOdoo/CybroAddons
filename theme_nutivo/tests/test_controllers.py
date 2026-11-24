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
from odoo.tests import HttpCase, tagged

from odoo.addons.theme_nutivo.controllers.theme_nutivo import NutivoStore
from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon


@tagged('post_install', '-at_install')
class TestNutivoStore(WebsiteSaleCommon):
    """Test the product grid, search, quick view, bag and wishlist routes."""

    @classmethod
    def setUpClass(cls):
        """Apply the theme and put the test product in a shop category."""
        super().setUpClass()
        theme = cls.env['ir.module.module'].search(
            [('name', '=', 'theme_nutivo')], limit=1)
        theme._theme_load(cls.website)
        cls.category = cls.env['product.public.category'].create({
            'name': 'Nutivo Test Nuts',
        })
        cls.template = cls.product.product_tmpl_id
        cls.template.write({
            'public_categ_ids': [(6, 0, cls.category.ids)],
            'description_sale': 'Crisp and buttery',
        })

    def test_products_all(self):
        """The grid renders the published products as Nutivo cards."""
        with MockRequest(self.env, website=self.website):
            result = NutivoStore().products(category='all', limit=8)
        self.assertIn('nv-pcard', result['html'])
        self.assertNotIn('chips', result)

    def test_products_category_and_chips(self):
        """A category, by id or name, keeps its products; chips are given
        when asked."""
        with MockRequest(self.env, website=self.website):
            by_id = NutivoStore().products(
                category=self.category.id, chips=True)
            by_name = NutivoStore().products(category='Nutivo Test Nuts')
        expected = 'data-product="{}"'.format(self.template.id)
        self.assertIn(expected, by_id['html'])
        self.assertIn(expected, by_name['html'])
        self.assertIn('chips', by_id)

    def test_products_sort_and_hamper(self):
        """Every sort key and the hamper design render."""
        with MockRequest(self.env, website=self.website):
            for sort in ('featured', 'price-asc', 'price-desc', 'rating',
                         'popular', 'unknown'):
                result = NutivoStore().products(sort=sort, card='hamper')
                self.assertTrue(result['html'])

    def test_quick_view(self):
        """A published product renders, an unknown one gives nothing."""
        with MockRequest(self.env, website=self.website):
            controller = NutivoStore()
            self.assertTrue(controller.quick_view(self.template.id))
            self.assertEqual(controller.quick_view(0), '')

    def test_bag_empty(self):
        """The bag of a new visitor is empty and suggests products."""
        with MockRequest(self.env, website=self.website):
            result = NutivoStore().bag()
        self.assertEqual(result['cart_quantity'], 0)
        self.assertTrue(result['html'])

    def test_bag_with_lines(self):
        """The bag of a cart with lines gives its quantity and checkout."""
        with MockRequest(
                self.env, website=self.website, sale_order_id=self.cart.id):
            result = NutivoStore().bag()
        self.assertEqual(result['cart_quantity'], self.cart.cart_quantity)
        self.assertIn('nv-bag', result['html'])

    def test_wishlist_empty(self):
        """The wishlist of a new visitor is empty."""
        with MockRequest(self.env, website=self.website):
            result = NutivoStore().wishlist()
        self.assertEqual(result['product_ids'], [])
        self.assertTrue(result['html'])

    def test_wishlist_toggle_unknown(self):
        """An unknown product is never saved."""
        with MockRequest(self.env, website=self.website):
            result = NutivoStore().wishlist_toggle(0)
        self.assertEqual(result, {'on': False, 'product_ids': []})


@tagged('post_install', '-at_install')
class TestNutivoShopPage(HttpCase):
    """Test that the shop page is the standard one with the theme blocks."""

    def test_shop_page(self):
        """The shop renders the standard grid and the theme zones."""
        theme = self.env['ir.module.module'].search(
            [('name', '=', 'theme_nutivo')], limit=1)
        theme._theme_load(self.env['website'].search([], limit=1))
        self.env['product.template'].create({
            'name': 'Nutivo Shop Page Test',
            'is_published': True,
            'list_price': 12.0,
        })
        response = self.url_open('/shop')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_wsale_products_grid_table_wrapper', response.text)
        self.assertIn('Shop the', response.text)
        # The banner and the call to action sit in editable zones of the
        # theme, so the builder can drop blocks around them.
        self.assertIn('id="oe_structure_nutivo_shop_top"', response.text)
        self.assertIn('id="oe_structure_nutivo_shop_bottom"', response.text)

    def test_shop_tile(self):
        """The tiles keep the standard markup and add the pack sizes, the
        Add button and the quick view of the theme cards."""
        theme = self.env['ir.module.module'].search(
            [('name', '=', 'theme_nutivo')], limit=1)
        theme._theme_load(self.env['website'].search([], limit=1))
        product = self.env['product.template'].create({
            'name': 'Nutivo Tile Test',
            'is_published': True,
            'list_price': 12.0,
        })
        page = self.url_open('/shop').text
        self.assertIn('oe_product_cart', page)
        self.assertIn('Nutivo Tile Test', page)
        self.assertIn('nv-tile-quick', page)
        self.assertIn('data-add', page)
        self.assertIn('data-product="%s"' % product.id, page)


@tagged('post_install', '-at_install')
class TestNutivoConfirmation(HttpCase):
    """Test the order confirmation page of the theme."""

    def test_confirmation_design(self):
        """The confirmation page shows the Nutivo hero, cards and items."""
        website = self.env['website'].browse(1)
        self.env['ir.module.module'].search(
            [('name', '=', 'theme_nutivo')], limit=1)._theme_load(website)
        product = self.env['product.product'].create({
            'name': 'Nutivo Confirmation Test',
            'is_published': True,
            'list_price': 12.0,
        })
        order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.partner_admin').id,
            'website_id': website.id,
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 2})],
        })
        order.action_confirm()
        self.authenticate('admin', 'admin', session_extra={'sale_last_order_id': order.id})
        page = self.url_open('/shop/confirmation').text
        for marker in ('nv-ck-done__hero', 'nv-ck-done__grid',
                       'nv-ck-done__items', 'Track your order'):
            self.assertIn(marker, page)


@tagged('post_install', '-at_install')
class TestNutivoHeader(HttpCase):
    """The header stays the standard one: every builder template renders."""

    def test_header_templates(self):
        """Each header template of the website builder renders the home page
        with the announcement bar and the cart link wired to the bag."""
        website = self.env['website'].browse(1)
        self.env['ir.module.module'].search(
            [('name', '=', 'theme_nutivo')], limit=1)._theme_load(website)
        View = self.env['ir.ui.view'].with_context(
            website_id=website.id, active_test=False)
        default = View.search([('key', '=', 'website.template_header_default')])
        templates = View.search([('key', 'in', [
            'website.template_header_hamburger',
            'website.template_header_boxed',
            'website.template_header_stretch',
            'website.template_header_vertical',
            'website.template_header_sidebar',
            'website.template_header_sales_one',
            'website.template_header_search',
        ])])
        self.assertTrue(templates)
        for template in templates:
            (default | templates).write({'active': False})
            template.write({'active': True})
            page = self.url_open('/').text
            self.assertIn('nv-announce', page, template.key)
            self.assertIn('data-open="cart"', page, template.key)
