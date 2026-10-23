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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for POS Orderline Search module."""

import os
from lxml import etree
import odoo.modules.module as module_utils
from odoo.tests.common import TransactionCase, tagged


def _simulate_orderline_search(orderlines, raw_search):
    """Simulate the client-side search logic in orderline_templates.js."""
    query = (raw_search or "").lower().strip()
    query_normalized = "".join(query.split())
    if not query:
        return []

    results = []
    for line in orderlines:
        product = line.product_id
        display_name = (line.name or product.display_name or "").lower()
        product_name = (product.name or "").lower()
        default_code = (product.default_code or "").lower()
        barcode = (product.barcode or "").lower()

        norm_display_name = "".join(display_name.split())
        norm_product_name = "".join(product_name.split())

        fields = [display_name, product_name, default_code, barcode]
        norm_fields = [norm_display_name, norm_product_name]

        if any(query in f for f in fields) or any(query_normalized in f for f in norm_fields):
            results.append(line)
    return results


@tagged('post_install', '-at_install')
class TestPosOrderlineSearch(TransactionCase):
    """Verify pos_orderline_search templates, assets, configuration and search logic."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and sample POS products."""
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Orderline Search Config',
        })

        cls.product_a = cls.env['product.product'].create({
            'name': 'Cheeseburger Special',
            'default_code': 'CHBUR01',
            'barcode': '123456789012',
            'available_in_pos': True,
            'list_price': 8.50,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'French Fries',
            'default_code': 'FFRIES01',
            'barcode': '987654321098',
            'available_in_pos': True,
            'list_price': 3.50,
        })
        cls.product_c = cls.env['product.product'].create({
            'name': 'Vanilla Milkshake',
            'default_code': 'VSHAKE01',
            'barcode': '555555555555',
            'available_in_pos': True,
            'list_price': 4.00,
        })

    def test_01_module_installed(self):
        """Verify module is installed and depends on point_of_sale."""
        module = self.env['ir.module.module'].search(
            [('name', '=', 'pos_orderline_search')], limit=1
        )
        self.assertTrue(module, "Module pos_orderline_search record should exist")
        self.assertEqual(module.state, 'installed', "pos_orderline_search should be installed")
        self.assertIn('point_of_sale', module.dependencies_id.mapped('name'))

    def test_02_manifest_metadata(self):
        """Verify manifest summary, license, and warning text consistency."""
        mod_path = module_utils.get_module_path('pos_orderline_search')
        self.assertTrue(mod_path)
        manifest_file = os.path.join(mod_path, '__manifest__.py')
        self.assertTrue(os.path.exists(manifest_file))
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest_content = f.read()

        manifest_data = eval(manifest_content)  # pylint: disable=eval-used
        self.assertEqual(manifest_data.get('license'), 'LGPL-3')
        self.assertEqual(manifest_data.get('depends'), ['point_of_sale'])
        self.assertIn('No products available.', manifest_data.get('description', ''))
        self.assertEqual(manifest_data.get('summary'), 'Search products in POS order lines')

    def test_03_static_files_existence(self):
        """Verify that required frontend assets exist on disk."""
        mod_path = module_utils.get_module_path('pos_orderline_search')
        xml_file = os.path.join(mod_path, 'static/src/xml/orderline_templates.xml')
        js_file = os.path.join(mod_path, 'static/src/js/orderline_templates.js')
        css_file = os.path.join(mod_path, 'static/src/css/search_product.css')
        banner_file = os.path.join(mod_path, 'static/description/banner.jpg')
        icon_file = os.path.join(mod_path, 'static/description/icon.png')
        html_file = os.path.join(mod_path, 'static/description/index.html')

        self.assertTrue(os.path.exists(xml_file))
        self.assertTrue(os.path.exists(js_file))
        self.assertTrue(os.path.exists(css_file))
        self.assertTrue(os.path.exists(banner_file))
        self.assertTrue(os.path.exists(icon_file))
        self.assertTrue(os.path.exists(html_file))

    def test_04_xml_subtemplate_and_clean_standards(self):
        """Verify XML sub-template, lack of autofocus, and Bootstrap 5 classes."""
        mod_path = module_utils.get_module_path('pos_orderline_search')
        xml_path = os.path.join(mod_path, 'static/src/xml/orderline_templates.xml')
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertNotIn('autofocus', content, "Inputs must not carry autofocus")
        self.assertNotIn('font-italic', content, "Bootstrap 4 'font-italic' should not be used")
        self.assertIn('fst-italic', content, "Bootstrap 5 'fst-italic' should be used")
        self.assertNotIn('search-clear-partner', content, "Copied class should not be present")
        self.assertIn('search-clear-btn', content, "search-clear-btn should be present")
        self.assertIn('t-name="pos_orderline_search.SearchBar"', content)
        self.assertIn('t-call="pos_orderline_search.SearchBar"', content)
        self.assertIn('No products available.', content, "Warning message must match manifest")

        # Ensure XML is well-formed
        tree = etree.fromstring(content.encode('utf-8'))
        self.assertEqual(tree.tag, 'templates')

    def test_05_js_patch_standards(self):
        """Verify JavaScript follows Odoo 20 conventions and searches order lines."""
        mod_path = module_utils.get_module_path('pos_orderline_search')
        js_path = os.path.join(mod_path, 'static/src/js/orderline_templates.js')
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()

        self.assertNotIn('/** @odoo-module **/', js_content)
        self.assertNotIn('this.state = proxy', js_content)
        self.assertIn('this.searchState = proxy', js_content)
        self.assertNotIn('product.product"]?.getAll()', js_content)
        self.assertIn('getOrderlines', js_content)
        self.assertNotIn('_keyPress', js_content)
        self.assertNotIn('_OnclickCancelSearch', js_content)

    def test_06_orderline_search_filters_current_order_only(self):
        """Verify that orderline search only matches products already added to the cart."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
            'user_id': self.env.uid,
        })
        order = self.env['pos.order'].create({
            'session_id': session.id,
            'lines': [
                (0, 0, {
                    'name': 'OL/001',
                    'product_id': self.product_a.id,
                    'price_unit': self.product_a.list_price,
                    'qty': 1.0,
                    'price_subtotal': self.product_a.list_price,
                    'price_subtotal_incl': self.product_a.list_price,
                }),
                (0, 0, {
                    'name': 'OL/002',
                    'product_id': self.product_b.id,
                    'price_unit': self.product_b.list_price,
                    'qty': 2.0,
                    'price_subtotal': self.product_b.list_price * 2,
                    'price_subtotal_incl': self.product_b.list_price * 2,
                }),
            ],
            'amount_tax': 0.0,
            'amount_total': 15.50,
            'amount_paid': 15.50,
            'amount_return': 0.0,
        })

        orderlines = order.lines
        self.assertEqual(len(orderlines), 2)

        # 1. Search for Cheeseburger (product_a in orderline)
        matches_name = _simulate_orderline_search(orderlines, "cheeseburger")
        self.assertEqual(len(matches_name), 1)
        self.assertEqual(matches_name[0].product_id, self.product_a)

        # 2. Search by default_code
        matches_code = _simulate_orderline_search(orderlines, "CHBUR01")
        self.assertEqual(len(matches_code), 1)
        self.assertEqual(matches_code[0].product_id, self.product_a)

        # 3. Search by barcode
        matches_barcode = _simulate_orderline_search(orderlines, "987654321098")
        self.assertEqual(len(matches_barcode), 1)
        self.assertEqual(matches_barcode[0].product_id, self.product_b)

        # 4. Search for Milkshake (product_c is in catalog, but NOT in orderlines)
        matches_c = _simulate_orderline_search(orderlines, "milkshake")
        self.assertEqual(len(matches_c), 0, "Products not in orderline must not appear")

        # 5. Search for non-existent item
        matches_none = _simulate_orderline_search(orderlines, "nonexistent")
        self.assertEqual(len(matches_none), 0)

        # 6. Empty search string
        matches_empty = _simulate_orderline_search(orderlines, "")
        self.assertEqual(matches_empty, [])
