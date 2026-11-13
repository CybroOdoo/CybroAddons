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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDoneQuantityAutoFill(TransactionCase):
    """Test suite for Done Quantity Auto Fill module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Locations
        cls.customer_loc = cls.env.ref('stock.stock_location_customers')
        cls.supplier_loc = cls.env.ref('stock.stock_location_suppliers')
        cls.stock_loc = cls.env.ref('stock.stock_location_stock')

        # Picking types
        cls.warehouse = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.company.id)
        ], limit=1)
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.picking_type_in = cls.warehouse.in_type_id

        # Products
        cls.product_a = cls.env['product.product'].create({
            'name': 'Test Product A',
            'is_storable': True,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Test Product B',
            'is_storable': True,
        })
        cls.product_c = cls.env['product.product'].create({
            'name': 'Test Product C',
            'is_storable': True,
        })

        # Add initial inventory: 15 for product_a, 4 for product_b, 0 for product_c
        cls.env['stock.quant']._update_available_quantity(
            cls.product_a, cls.stock_loc, 15.0
        )
        cls.env['stock.quant']._update_available_quantity(
            cls.product_b, cls.stock_loc, 4.0
        )

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Warehouse Partner',
        })

    def _create_outgoing_picking(self):
        """Helper to create an outgoing transfer with test moves."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
            'partner_id': self.partner.id,
            'move_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 10.0,
                    'location_id': self.stock_loc.id,
                    'location_dest_id': self.customer_loc.id,
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'product_uom_qty': 10.0,
                    'location_id': self.stock_loc.id,
                    'location_dest_id': self.customer_loc.id,
                }),
                Command.create({
                    'product_id': self.product_c.id,
                    'product_uom_qty': 10.0,
                    'location_id': self.stock_loc.id,
                    'location_dest_id': self.customer_loc.id,
                }),
            ],
        })
        picking.action_confirm()
        return picking

    def _create_incoming_picking(self):
        """Helper to create an incoming transfer (Receipt)."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.stock_loc.id,
            'partner_id': self.partner.id,
            'move_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 8.0,
                    'location_id': self.supplier_loc.id,
                    'location_dest_id': self.stock_loc.id,
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'product_uom_qty': 6.0,
                    'location_id': self.supplier_loc.id,
                    'location_dest_id': self.stock_loc.id,
                }),
            ],
        })
        picking.action_confirm()
        return picking

    def test_01_select_and_unselect_all(self):
        """Verify action_select_all selects all moves and action_unselect_all unselects them."""
        picking = self._create_outgoing_picking()

        self.assertFalse(picking.select_all_toggle)
        self.assertFalse(any(picking.move_ids.mapped('product_select')))

        # Select all
        picking.action_select_all()
        self.assertTrue(picking.select_all_toggle)
        self.assertTrue(all(picking.move_ids.mapped('product_select')))

        # Unselect all
        picking.action_unselect_all()
        self.assertFalse(picking.select_all_toggle)
        self.assertFalse(any(picking.move_ids.mapped('product_select')))

    def test_02_select_all_toggle_follows_manual_line_selection(self):
        """Verify select_all_toggle accurately reflects manual line selections."""
        picking = self._create_outgoing_picking()
        moves = picking.move_ids

        # Initially unselected
        self.assertFalse(picking.select_all_toggle)

        # Select some lines manually
        moves[0].product_select = True
        self.assertFalse(
            picking.select_all_toggle,
            "Toggle should remain False when only some lines are selected."
        )

        # Select all remaining lines manually
        for move in moves[1:]:
            move.product_select = True
        self.assertTrue(
            picking.select_all_toggle,
            "Toggle should become True when all lines are selected manually."
        )

        # Unselect one line manually
        moves[0].product_select = False
        self.assertFalse(
            picking.select_all_toggle,
            "Toggle should revert to False when any line is unselected."
        )

        # Empty picking
        empty_picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
        })
        self.assertFalse(
            empty_picking.select_all_toggle,
            "Toggle must be False for pickings with no lines."
        )

    def test_03_action_fill_done_qty_outgoing_full_and_partial(self):
        """Verify action_fill_done_qty respects available stock and handles partial availability."""
        picking = self._create_outgoing_picking()
        moves = picking.move_ids
        move_a = moves.filtered(lambda m: m.product_id == self.product_a)
        move_b = moves.filtered(lambda m: m.product_id == self.product_b)
        move_c = moves.filtered(lambda m: m.product_id == self.product_c)

        # Select move_a (available 15 >= demand 10), move_b (available 4 < demand 10), and move_c (available 0)
        move_a.product_select = True
        move_b.product_select = True
        move_c.product_select = True

        picking.action_fill_done_qty()

        # move_a: full demand filled
        self.assertEqual(
            move_a.quantity, 10.0,
            "Full demand should be filled when forecast availability is sufficient."
        )
        # move_b: partial demand filled to available quantity
        self.assertEqual(
            move_b.quantity, 4.0,
            "Only available quantity should be filled when stock is partially available."
        )
        # move_c: 0 quantity filled because no stock is available
        self.assertEqual(
            move_c.quantity, 0.0,
            "No quantity should be filled when forecast availability is 0."
        )

    def test_04_action_fill_done_qty_unselected_lines_ignored(self):
        """Verify that unselected move lines are untouched by action_fill_done_qty."""
        picking = self._create_outgoing_picking()
        picking.move_ids.write({'quantity': 0.0})
        moves = picking.move_ids
        move_a = moves.filtered(lambda m: m.product_id == self.product_a)
        move_b = moves.filtered(lambda m: m.product_id == self.product_b)

        # Only select move_a; leave move_b unselected
        move_a.product_select = True
        move_b.product_select = False

        picking.action_fill_done_qty()

        self.assertEqual(move_a.quantity, 10.0)
        self.assertEqual(
            move_b.quantity, 0.0,
            "Unselected line quantity must remain 0.0."
        )

    def test_05_action_fill_done_qty_incoming(self):
        """Verify action_fill_done_qty on incoming transfers fills the demand for selected moves."""
        picking = self._create_incoming_picking()
        picking.move_ids.write({'quantity': 0.0})
        moves = picking.move_ids
        move_a = moves.filtered(lambda m: m.product_id == self.product_a)
        move_b = moves.filtered(lambda m: m.product_id == self.product_b)

        # Select only move_a
        move_a.product_select = True
        move_b.product_select = False

        picking.action_fill_done_qty()

        self.assertEqual(
            move_a.quantity, 8.0,
            "Incoming transfer should fill full demand for selected move."
        )
        self.assertEqual(
            move_b.quantity, 0.0,
            "Unselected incoming move should remain 0.0."
        )

    def test_06_action_unfill_done_qty(self):
        """Verify action_unfill_done_qty resets quantity to 0.0 for selected lines only."""
        picking = self._create_incoming_picking()
        moves = picking.move_ids
        move_a = moves.filtered(lambda m: m.product_id == self.product_a)
        move_b = moves.filtered(lambda m: m.product_id == self.product_b)

        # Select all and fill done quantities
        picking.action_select_all()
        picking.action_fill_done_qty()
        self.assertEqual(move_a.quantity, 8.0)
        self.assertEqual(move_b.quantity, 6.0)

        # Unselect all, then select only move_a to unfill
        picking.action_unselect_all()
        move_a.product_select = True
        move_b.product_select = False

        picking.action_unfill_done_qty()

        self.assertEqual(
            move_a.quantity, 0.0,
            "Selected move quantity must be reset to float 0.0."
        )
        self.assertIsInstance(
            move_a.quantity, float,
            "Quantity field must be float, not string."
        )
        self.assertEqual(
            move_b.quantity, 6.0,
            "Unselected move quantity must remain unchanged."
        )

    def test_07_batch_multi_picking(self):
        """Verify actions function correctly when called on multi-record picking sets."""
        picking_1 = self._create_outgoing_picking()
        picking_2 = self._create_incoming_picking()
        pickings = picking_1 | picking_2

        # Batch select all
        pickings.action_select_all()
        self.assertTrue(all(pickings.mapped('select_all_toggle')))
        self.assertTrue(all(pickings.mapped('move_ids.product_select')))

        # Batch fill done qty
        pickings.action_fill_done_qty()
        self.assertTrue(any(move.quantity > 0 for move in picking_1.move_ids))
        self.assertTrue(any(move.quantity > 0 for move in picking_2.move_ids))

        # Batch unfill done qty
        pickings.action_unfill_done_qty()
        self.assertTrue(all(move.quantity == 0.0 for move in pickings.move_ids))

        # Batch unselect all
        pickings.action_unselect_all()
        self.assertFalse(any(pickings.mapped('select_all_toggle')))
        self.assertFalse(any(pickings.mapped('move_ids.product_select')))
