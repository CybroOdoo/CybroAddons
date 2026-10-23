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
"""Unit tests for purchase.report model in product_brand_purchase."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPurchaseReport(TransactionCase):
    """Test cases for 'purchase.report' model in product_brand_purchase."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['product.brand'].create({
            'name': 'Report Brand',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Report Product',
            'brand_id': cls.brand.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Report Vendor',
        })
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_qty': 5.0,
                    'price_unit': 50.0,
                })
            ]
        })
        cls.purchase_order.button_confirm()

    def test__select_list(self):
        """Test _select_list includes brand_id in query fields."""
        query = self.env['purchase.order.line']._search([])
        select_list = self.env['purchase.report']._select_list(query.table)
        self.assertIsInstance(select_list, list)
        self.assertTrue(any('brand_id' in str(sql) for sql in select_list))

        # Verify data is readable in purchase.report with brand_id
        report = self.env['purchase.report'].search([
            ('order_id', '=', self.purchase_order.id)
        ], limit=1)
        if report:
            self.assertEqual(report.brand_id, self.brand)

    test_select_list = test__select_list

    def test__groupby_list(self):
        """Test _groupby_list includes brand_id in GROUP BY fields."""
        query = self.env['purchase.order.line']._search([])
        groupby_list = self.env['purchase.report']._groupby_list(query.table)
        self.assertIsInstance(groupby_list, list)
        self.assertTrue(any('brand_id' in str(sql) for sql in groupby_list))

    test_groupby_list = test__groupby_list
