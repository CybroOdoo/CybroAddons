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
class TestStock(TransactionCase):
    """Test suite for stock move and picking sequences."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_type = cls.env.ref(
            'stock.picking_type_out',
            raise_if_not_found=False,
        ) or cls.env['stock.picking.type'].search([], limit=1)
        cls.customer_loc = cls.env.ref(
            'stock.stock_location_customers',
            raise_if_not_found=False,
        ) or cls.env['stock.location'].search(
            [('usage', '=', 'customer')],
            limit=1,
        )
        cls.stock_loc = cls.env.ref(
            'stock.stock_location_stock',
            raise_if_not_found=False,
        ) or cls.env['stock.location'].search(
            [('usage', '=', 'internal')],
            limit=1,
        )

        cls.product_a = cls.env['product.product'].create({
            'name': 'Stock Product A',
            'is_storable': True,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Stock Product B',
            'is_storable': True,
        })
        cls.product_c = cls.env['product.product'].create({
            'name': 'Stock Product C',
            'is_storable': True,
        })

    def test_stock_move_sequence_numbers(self):
        """Test sequential line numbers computed on picking stock moves."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
            'move_ids': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 5,
                    'uom_id': self.product_a.uom_id.id,
                    'location_id': self.stock_loc.id,
                    'location_dest_id': self.customer_loc.id,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_uom_qty': 10,
                    'uom_id': self.product_b.uom_id.id,
                    'location_id': self.stock_loc.id,
                    'location_dest_id': self.customer_loc.id,
                }),
                (0, 0, {
                    'product_id': self.product_c.id,
                    'product_uom_qty': 15,
                    'uom_id': self.product_c.uom_id.id,
                    'location_id': self.stock_loc.id,
                    'location_dest_id': self.customer_loc.id,
                }),
            ],
        })

        moves = picking.move_ids
        self.assertEqual(len(moves), 3)
        self.assertEqual(moves[0].sequence_number, 1)
        self.assertEqual(moves[1].sequence_number, 2)
        self.assertEqual(moves[2].sequence_number, 3)

    def test_stock_picking_onchange(self):
        """Test _onchange_move_ids_without_package updates sequence numbers."""
        picking = self.env['stock.picking'].new({
            'picking_type_id': self.picking_type.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
            'move_ids': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1,
                    'uom_id': self.product_a.uom_id.id,
                    'location_id': self.stock_loc.id,
                    'location_dest_id': self.customer_loc.id,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_uom_qty': 2,
                    'uom_id': self.product_b.uom_id.id,
                    'location_id': self.stock_loc.id,
                    'location_dest_id': self.customer_loc.id,
                }),
            ],
        })
        picking._onchange_move_ids_without_package()
        moves = picking.move_ids
        self.assertEqual(moves[0].sequence_number, 1)
        self.assertEqual(moves[1].sequence_number, 2)

    def test_stock_move_without_picking(self):
        """Test sequence number for a move without an assigned picking."""
        move = self.env['stock.move'].create({
            'product_id': self.product_a.id,
            'product_uom_qty': 1,
            'uom_id': self.product_a.uom_id.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
        })
        self.assertEqual(move.sequence_number, 0)
