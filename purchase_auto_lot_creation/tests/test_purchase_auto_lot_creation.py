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
from odoo import Command
from odoo.tests import tagged
from odoo.addons.purchase_stock.tests.common import PurchaseTestCommon


@tagged('post_install', '-at_install')
class TestPurchaseAutoLotCreation(PurchaseTestCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure vendor is approved if contact approval is in environment
        if 'state' in cls.vendor._fields:
            cls.vendor.write({'state': 'approve'})
        # Create lot-tracked product
        cls.product_lot = cls.env['product.product'].create({
            'name': 'Lot Tracked Product',
            'is_storable': True,
            'tracking': 'lot',
            'default_code': 'LOT-PROD',
        })
        # Create serial-tracked product
        cls.product_serial = cls.env['product.product'].create({
            'name': 'Serial Tracked Product',
            'is_storable': True,
            'tracking': 'serial',
            'default_code': 'SER-PROD',
        })
        # Create non-tracked product
        cls.product_none = cls.env['product.product'].create({
            'name': 'Non Tracked Product',
            'is_storable': True,
            'default_code': 'NON-TRACK',
        })

    def test_01_auto_lot_generation_on_confirm(self):
        """ Test automatic lot creation on PO confirmation without lot. """
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_lot.id,
                    'product_qty': 10.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        line = po.order_line[0]
        self.assertTrue(line.is_lot_product)
        self.assertFalse(line.lot_id)

        po.button_confirm()

        # Check lot_id was auto-generated on the line
        self.assertTrue(line.lot_id)
        self.assertEqual(line.lot_id.line_id, line)
        self.assertIn(po.name, line.lot_id.name)

        # Check stock moves and move lines
        picking = po.picking_ids
        self.assertTrue(picking)
        moves = picking.move_ids
        self.assertEqual(len(moves), 1)
        move_lines = moves.move_line_ids
        self.assertTrue(move_lines)
        self.assertEqual(move_lines[0].lot_name, line.lot_id.name)
        self.assertEqual(move_lines[0].quantity, 10.0)

    def test_02_custom_lot_manual_specification(self):
        """ Test manual custom lot is preserved on confirmation. """
        custom_lot = self.env['custom.stock.lot'].create({
            'name': 'MANUAL-LOT-1234',
        })
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_lot.id,
                    'product_qty': 5.0,
                    'price_unit': 50.0,
                    'lot_id': custom_lot.id,
                }),
            ],
        })
        line = po.order_line[0]
        self.assertEqual(line.lot_id, custom_lot)
        self.assertEqual(custom_lot.line_id, line)

        po.button_confirm()

        self.assertEqual(line.lot_id.name, 'MANUAL-LOT-1234')
        picking = po.picking_ids
        move_lines = picking.move_ids.move_line_ids
        self.assertTrue(move_lines)
        self.assertEqual(move_lines[0].lot_name, 'MANUAL-LOT-1234')
        self.assertEqual(move_lines[0].quantity, 5.0)

    def test_03_serial_tracking_product_split(self):
        """ Test serial product generates 1 move line per unit (qty 1.0). """
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_serial.id,
                    'product_qty': 3.0,
                    'price_unit': 200.0,
                }),
            ],
        })
        line = po.order_line[0]
        self.assertTrue(line.is_lot_product)

        po.button_confirm()

        picking = po.picking_ids
        move_lines = picking.move_ids.move_line_ids
        self.assertEqual(len(move_lines), 3)
        self.assertEqual([ml.quantity for ml in move_lines], [1.0, 1.0, 1.0])
        serial_names = [ml.lot_name for ml in move_lines]
        self.assertEqual(
            len(set(serial_names)), 3, "All serial names should be unique"
        )
        for sn in serial_names:
            self.assertTrue(sn.startswith(line.lot_id.name))

    def test_04_non_tracked_product(self):
        """ Test that non-tracked product does not generate lot. """
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_none.id,
                    'product_qty': 4.0,
                    'price_unit': 25.0,
                }),
            ],
        })
        line = po.order_line[0]
        self.assertFalse(line.is_lot_product)
        self.assertFalse(line.lot_id)

        po.button_confirm()

        self.assertFalse(line.lot_id)
        picking = po.picking_ids
        move_lines = picking.move_ids.move_line_ids
        if move_lines:
            self.assertFalse(any(ml.lot_name for ml in move_lines))

    def test_05_custom_stock_lot_inverse_sync(self):
        """ Test two-way sync between PO line and custom.stock.lot. """
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_lot.id,
                    'product_qty': 1.0,
                    'price_unit': 10.0,
                }),
            ],
        })
        line = po.order_line[0]
        # Create lot setting line_id
        lot = self.env['custom.stock.lot'].create({
            'name': 'SYNC-TEST-001',
            'line_id': line.id,
        })
        self.assertEqual(line.lot_id, lot)

        # Create another lot and update via line.lot_id
        lot2 = self.env['custom.stock.lot'].create({
            'name': 'SYNC-TEST-002',
        })
        line.lot_id = lot2
        self.assertEqual(lot2.line_id, line)

    def test_06_serial_tracking_uom_conversion(self):
        """ Test serial splitting when line uses multi-unit UoM (Dozen). """
        uom_dozen = self.env.ref('uom.product_uom_dozen')
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_serial.id,
                    'product_qty': 1.0,
                    'uom_id': uom_dozen.id,
                    'price_unit': 120.0,
                }),
            ],
        })
        po.button_confirm()
        move_lines = po.picking_ids.move_ids.move_line_ids
        self.assertEqual(len(move_lines), 12)
        self.assertTrue(all(ml.quantity == 1.0 for ml in move_lines))
