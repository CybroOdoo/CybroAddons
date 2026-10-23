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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWarehouseReportModels(TransactionCase):
    """Test model field extensions for warehouse reports."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for warehouse report models."""
        super().setUpClass()
        cls.category = cls.env['product.category'].create({
            'name': 'Test Inventory Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Inventory Product',
            'categ_id': cls.category.id,
        })
        cls.picking_type = cls.env['stock.picking.type'].search([], limit=1)

    def test_product_product_fields(self):
        """Verify product.product qty fields access and not force-stored."""
        self.assertIsInstance(self.product.outgoing_qty, float)
        self.assertIsInstance(self.product.incoming_qty, float)
        self.assertIsInstance(self.product.free_qty, float)
        self.assertIsNotNone(self.product.qty_available)
        self.assertFalse(self.env['product.product']._fields['qty_available'].store)

    def test_stock_picking_type_display_name(self):
        """Verify stock.picking.type display_name field access and not force-stored."""
        if self.picking_type:
            self.assertTrue(self.picking_type.display_name)
            self.assertFalse(self.env['stock.picking.type']._fields['display_name'].store)
