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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStockMove(TransactionCase):
    """Test cases for 'stock.move' model in barcode_scanning_sale_purchase."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Test Stock Product A',
            'barcode': '3333444455556',
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Test Stock Product B',
            'barcode': '7777888899990',
        })
        cls.location_src = cls.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if not cls.location_src:
            cls.location_src = cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        cls.location_dest = cls.env.ref('stock.stock_location_customers', raise_if_not_found=False)
        if not cls.location_dest:
            cls.location_dest = cls.env['stock.location'].search([('usage', '=', 'customer')], limit=1)

    def test__onchange_barcode_scan(self):
        """Test _onchange_barcode_scan updates product_id according to barcode_scan."""
        move = self.env['stock.move'].new({
            'product_id': self.product_1.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        # 1. Update barcode_scan with product_2's barcode
        move.barcode_scan = self.product_2.barcode
        move._onchange_barcode_scan()
        self.assertEqual(move.product_id, self.product_2)

        # 2. Update with non-existent barcode
        move.barcode_scan = '9999999999999'
        move._onchange_barcode_scan()
        self.assertFalse(move.product_id)

        # 3. Barcode scan is False / empty -> product_id remains unchanged
        move.product_id = self.product_1
        move.barcode_scan = False
        move._onchange_barcode_scan()
        self.assertEqual(move.product_id, self.product_1)

    test_onchange_barcode_scan = test__onchange_barcode_scan
