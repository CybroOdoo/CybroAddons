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
class TestPurchaseOrderLine(TransactionCase):
    """Test cases for 'purchase.order.line' model in barcode_scanning_sale_purchase."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Purchase Barcode Test Partner',
        })
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Test Purchase Product A',
            'barcode': '2222333344445',
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Test Purchase Product B',
            'barcode': '6666777788889',
        })
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })

    def test__onchange_barcode_scan(self):
        """Test _onchange_barcode_scan updates product_id according to barcode_scan."""
        line = self.env['purchase.order.line'].new({
            'order_id': self.purchase_order.id,
            'product_id': self.product_1.id,
        })
        # 1. Update barcode_scan with product_2's barcode
        line.barcode_scan = self.product_2.barcode
        line._onchange_barcode_scan()
        self.assertEqual(line.product_id, self.product_2)

        # 2. Update with non-existent barcode
        line.barcode_scan = '9999999999999'
        line._onchange_barcode_scan()
        self.assertFalse(line.product_id)

        # 3. Barcode scan is False / empty -> product_id remains unchanged
        line.product_id = self.product_1
        line.barcode_scan = False
        line._onchange_barcode_scan()
        self.assertEqual(line.product_id, self.product_1)

    test_onchange_barcode_scan = test__onchange_barcode_scan
