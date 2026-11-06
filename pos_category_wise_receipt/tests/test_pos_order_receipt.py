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
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosOrderReceipt(TransactionCase):
    """Test category-wise receipt data generation and rendering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({'name': 'Test Main POS'})

        cls.categ_beverages = cls.env['pos.category'].create({'name': 'Beverages'})
        cls.categ_snacks = cls.env['pos.category'].create({'name': 'Snacks'})

        cls.product_soda = cls.env['product.product'].create({
            'name': 'Soda Can',
            'list_price': 3.50,
            'pos_categ_ids': [fields.Command.link(cls.categ_beverages.id)],
            'available_in_pos': True,
        })
        cls.product_juice = cls.env['product.product'].create({
            'name': 'Orange Juice',
            'list_price': 4.50,
            'pos_categ_ids': [fields.Command.link(cls.categ_beverages.id)],
            'available_in_pos': True,
        })
        cls.product_chips = cls.env['product.product'].create({
            'name': 'Potato Chips',
            'list_price': 2.00,
            'pos_categ_ids': [fields.Command.link(cls.categ_snacks.id)],
            'available_in_pos': True,
        })
        cls.product_misc = cls.env['product.product'].create({
            'name': 'Paper Bag',
            'list_price': 0.50,
            'available_in_pos': True,
        })

    def _create_pos_order(self, lines_data):
        session = self.env['pos.session'].create({'config_id': self.pos_config.id})
        order_lines = []
        total = 0.0
        for prod, qty, price in lines_data:
            subtotal = qty * price
            total += subtotal
            order_lines.append(fields.Command.create({
                'product_id': prod.id,
                'qty': qty,
                'price_unit': price,
                'price_subtotal': subtotal,
                'price_subtotal_incl': subtotal,
            }))
        return self.env['pos.order'].create({
            'session_id': session.id,
            'lines': order_lines,
            'amount_total': total,
            'amount_tax': 0.0,
            'amount_paid': total,
            'amount_return': 0.0,
        })

    def test_01_category_wise_receipt_data(self):
        """Test that order lines are grouped by category with correct subtotals."""
        order = self._create_pos_order([
            (self.product_soda, 2, 3.50),   # Beverages: 7.00
            (self.product_juice, 1, 4.50),  # Beverages: 4.50 -> Beverages Total: 11.50
            (self.product_chips, 3, 2.00),  # Snacks: 6.00 -> Snacks Total: 6.00
            (self.product_misc, 2, 0.50),   # No Category: 1.00 -> Total: 1.00
        ])
        data = order.order_receipt_generate_data(basic_receipt=False)
        self.assertIn('category_data', data)

        categories = data['category_data']
        self.assertEqual(len(categories), 3, "Expected 3 groups: Beverages, Snacks, and No Category")

        categ_map = {cat['category_name']: cat for cat in categories}
        self.assertIn('Beverages', categ_map)
        self.assertIn('Snacks', categ_map)
        self.assertIn('', categ_map)

        bev_group = categ_map['Beverages']
        self.assertEqual(bev_group['category_id'], self.categ_beverages.id)
        self.assertAlmostEqual(bev_group['subtotal'], 11.50)
        self.assertEqual(len(bev_group['lines']), 2)
        self.assertTrue(bev_group['subtotal_formatted'])

        snack_group = categ_map['Snacks']
        self.assertEqual(snack_group['category_id'], self.categ_snacks.id)
        self.assertAlmostEqual(snack_group['subtotal'], 6.00)
        self.assertEqual(len(snack_group['lines']), 1)

        misc_group = categ_map['']
        self.assertIsNone(misc_group['category_id'])
        self.assertAlmostEqual(misc_group['subtotal'], 1.00)
        self.assertEqual(len(misc_group['lines']), 1)

    def test_02_product_without_category(self):
        """Test receipt grouping when all items are uncategorized."""
        order = self._create_pos_order([
            (self.product_misc, 4, 0.50),
        ])
        data = order.order_receipt_generate_data()
        categories = data.get('category_data', [])
        self.assertEqual(len(categories), 1)
        self.assertIsNone(categories[0]['category_id'])
        self.assertEqual(categories[0]['category_name'], '')
        self.assertAlmostEqual(categories[0]['subtotal'], 2.00)

    def test_03_order_receipt_generate_html(self):
        """Test that HTML receipt renders category headers and subtotals."""
        order = self._create_pos_order([
            (self.product_soda, 1, 3.50),
            (self.product_chips, 2, 2.00),
        ])
        html = order.order_receipt_generate_html()
        self.assertIn('Beverages', html)
        self.assertIn('Snacks', html)
        self.assertIn('SUB TOTAL:', html)

    def test_04_basic_receipt(self):
        """Test order_receipt_generate_data with basic_receipt=True."""
        order = self._create_pos_order([
            (self.product_soda, 1, 3.50),
        ])
        data = order.order_receipt_generate_data(basic_receipt=True)
        self.assertIn('category_data', data)
        self.assertEqual(len(data['category_data']), 1)
        self.assertEqual(data['category_data'][0]['category_name'], 'Beverages')
