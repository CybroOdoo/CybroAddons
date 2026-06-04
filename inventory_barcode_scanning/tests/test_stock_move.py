# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.

###############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install', 'barcode_scanning')
class TestStockMoveBarcode(TransactionCase):
    """Tests for barcode field and onchanges on stock.move."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.warehouse = cls.env.ref('stock.warehouse0')
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        cls.product_with_barcode = cls.env['product.product'].create({
            'name': 'Move Product With Barcode',
            'type': 'consu',
            'barcode': 'MOVE_BARCODE_001',
        })
        cls.product_no_barcode = cls.env['product.product'].create({
            'name': 'Move Product No Barcode',
            'type': 'consu',
        })

        cls.picking = cls.env['stock.picking'].create({
            'picking_type_id': cls.picking_type_out.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
        })

    def _new_move(self, extra_vals=None):
        vals = {
            'picking_id': self.picking.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'product_uom': self.uom_unit.id,
        }
        if extra_vals:
            vals.update(extra_vals)
        return self.env['stock.move'].new(vals)

    def test_onchange_barcode_scan_sets_product(self):
        """Onchange: scanning barcode on move sets product_id"""
        move = self._new_move()
        move.barcode = 'MOVE_BARCODE_001'
        move._onchange_barcode_scan()
        self.assertEqual(
            move.product_id.id,
            self.product_with_barcode.id,
            "Scanning a known barcode on a move should set its product_id",
        )

    def test_onchange_barcode_scan_unknown_leaves_product_empty(self):
        """Onchange: scanning unknown barcode → product_id remains empty"""
        move = self._new_move()
        move.barcode = 'TOTALLY_UNKNOWN_BARCODE'
        move._onchange_barcode_scan()
        self.assertFalse(
            move.product_id,
            "Unknown barcode should leave product_id unset (empty recordset)",
        )

    def test_onchange_product_fills_barcode(self):
        """Onchange: selecting a product auto-fills its barcode"""
        move = self._new_move()
        move.product_id = self.product_with_barcode
        move._onchange_product()
        self.assertEqual(
            move.barcode,
            'MOVE_BARCODE_001',
            "Selecting a product should sync its barcode to the move's barcode field",
        )

    def test_onchange_product_no_barcode_leaves_field_unchanged(self):
        """Onchange: selecting a product with no barcode → barcode unchanged"""
        move = self._new_move()
        move.barcode = 'OLD_BARCODE'
        move.product_id = self.product_no_barcode
        move._onchange_product()
        self.assertEqual(
            move.barcode,
            'OLD_BARCODE',
            "Product without barcode should not overwrite move's barcode field",
        )

    def test_barcode_and_product_sync_round_trip(self):
        """Scan → product set; switch product → barcode updated."""
        move = self._new_move()
        move.barcode = 'MOVE_BARCODE_001'
        move._onchange_barcode_scan()
        self.assertEqual(move.product_id, self.product_with_barcode)
        move._onchange_product()
        self.assertEqual(move.barcode, 'MOVE_BARCODE_001')