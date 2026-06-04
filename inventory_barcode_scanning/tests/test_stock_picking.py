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
#
###############################################################################

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'barcode_scanning')
class TestStockPickingBarcode(TransactionCase):
    """Tests for the barcode field and _onchange_barcode on stock.picking."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── warehouse / locations ──────────────────────────────────────────
        cls.warehouse = cls.env.ref('stock.warehouse0')
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.customer_location = cls.env.ref('stock.stock_location_customers')

        # ── picking type (outgoing) ────────────────────────────────────────
        cls.picking_type_out = cls.warehouse.out_type_id

        # ── products with distinct barcodes ───────────────────────────────
        cls.product_a = cls.env['product.product'].create({
            'name': 'Product Alpha',
            'type': 'consu',
            'barcode': 'BARCODE_ALPHA',
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Product Beta',
            'type': 'consu',
            'barcode': 'BARCODE_BETA',
        })
        cls.product_no_barcode = cls.env['product.product'].create({
            'name': 'Product No Barcode',
            'type': 'consu',
        })

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def _make_picking(self, products_qty=None):
        """Create a confirmed outgoing picking with optional move lines.
        products_qty: list of (product, qty) tuples """
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        for product, qty in (products_qty or []):
            self.env['stock.move'].create({
                'picking_id': picking.id,
                'product_id': product.id,
                'product_uom_qty': qty,
                'quantity': qty,
                'product_uom': product.uom_id.id,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
            })
        return picking

    def test_picking_has_barcode_field(self):
        """ Field: stock.picking has 'barcode' char field"""
        picking = self._make_picking()
        self.assertIn(
            'barcode',
            self.env['stock.picking']._fields,
            "stock.picking must expose a 'barcode' field",
        )
        # Default value should be falsy (empty / None)
        self.assertFalse(
            picking.barcode,
            "Newly created picking should have no barcode set",
        )

    def test_onchange_barcode_increments_quantity(self):
        """ Onchange: scanning a barcode that matches a move → qty += 1"""
        picking = self._make_picking([(self.product_a, 2)])
        move = picking.move_ids[0]
        self.assertEqual(move.quantity, 2)

        picking.barcode = 'BARCODE_ALPHA'
        result = picking._onchange_barcode()

        self.assertEqual(
            move.quantity, 3,
            "Scanning a matching barcode should increment move quantity by 1",
        )
        self.assertFalse(
            result,
            "No warning should be returned when the barcode matches a move",
        )


    def test_onchange_barcode_multiple_scans(self):
        """ Onchange: scanning same barcode twice increments by 2 total"""
        picking = self._make_picking([(self.product_a, 0)])
        move = picking.move_ids[0]

        for _ in range(3):
            picking.barcode = 'BARCODE_ALPHA'
            picking._onchange_barcode()

        self.assertEqual(
            move.quantity, 3,
            "Three scans of the same barcode should add 3 to move quantity",
        )


    def test_onchange_barcode_product_not_in_order_warning(self):
        """Product exists in catalogue but is not in the current picking."""
        picking = self._make_picking([(self.product_a, 1)])

        picking.barcode = 'BARCODE_BETA'   # product_b is not in this picking
        result = picking._onchange_barcode()

        self.assertIsNotNone(result, "Should return a dict with a warning")
        self.assertIn('warning', result)
        self.assertIn('message', result['warning'])
        self.assertIn(
            'not available in the order',
            result['warning']['message'],
        )


    def test_onchange_barcode_unknown_barcode_warning(self):
        """ Onchange: barcode matches no product at all → warning"""
        picking = self._make_picking([(self.product_a, 1)])

        picking.barcode = 'UNKNOWN_BARCODE_XYZ'
        result = picking._onchange_barcode()

        self.assertIsNotNone(result)
        self.assertIn('warning', result)
        self.assertEqual(result['warning']['title'], 'Warning !')
        self.assertIn(
            'No product is available for this barcode',
            result['warning']['message'],
        )


    def test_onchange_empty_barcode_no_action(self):
        """ Onchange: empty barcode → no action, no warning"""
        picking = self._make_picking([(self.product_a, 5)])
        move = picking.move_ids[0]

        picking.barcode = ''
        result = picking._onchange_barcode()

        self.assertEqual(
            move.quantity, 5,
            "Empty barcode must not modify any move quantity",
        )
        self.assertFalse(result, "Empty barcode should not return a warning")


    def test_onchange_barcode_no_moves_warning(self):
        """Picking with no moves: valid barcode should warn 'not in order'."""
        picking = self._make_picking()   # no products

        picking.barcode = 'BARCODE_ALPHA'
        result = picking._onchange_barcode()

        self.assertIn('warning', result or {})


    def test_onchange_barcode_only_matching_move_updated(self):
        """ Onchange: only the matching move's quantity changes"""
        picking = self._make_picking([
            (self.product_a, 1),
            (self.product_b, 1),
        ])
        move_a = picking.move_ids.filtered(
            lambda m: m.product_id == self.product_a
        )
        move_b = picking.move_ids.filtered(
            lambda m: m.product_id == self.product_b
        )

        picking.barcode = 'BARCODE_ALPHA'
        picking._onchange_barcode()

        self.assertEqual(move_a.quantity, 2, "product_a move should be +1")
        self.assertEqual(move_b.quantity, 1, "product_b move must not change")