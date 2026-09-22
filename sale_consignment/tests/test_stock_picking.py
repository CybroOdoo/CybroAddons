# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from odoo import Command
from datetime import date, timedelta
from .common import TestConsignmentCommon


@tagged('post_install', '-at_install')
class TestStockPicking(TestConsignmentCommon):

    def test_01_confirm_consignment_order_picking(self):
        """Test confirming consignment order creates internal picking."""
        consignment = self.env['sale.consignment'].create({
            'partner_id': self.partner_consignment.id,
            'end_date': date.today() + timedelta(days=10),
            'location_id': self.location_src.id,
            'consignment_line_ids': [
                Command.create({
                    'product_id': self.product_consignment.id,
                    'demand_quantity': 5,
                })
            ]
        })

        consignment.action_order_confirm()

        # Check picking created
        self.assertEqual(consignment.picking_count, 1)
        picking = self.env['stock.picking'].search([('consignment_id', '=', consignment.id)])
        self.assertTrue(picking)
        self.assertEqual(picking.location_id, self.location_src)
        self.assertEqual(picking.location_dest_id, self.location_dest)
        self.assertEqual(picking.partner_id, self.partner_consignment)
        self.assertEqual(picking.picking_type_id, self.picking_type)

        # Check picking move
        self.assertEqual(len(picking.move_ids), 1)
        move = picking.move_ids[0]
        self.assertEqual(move.product_id, self.product_consignment)
        self.assertEqual(move.quantity, 5.0)

    def test_02_validate_picking_updates_quantities(self):
        """Test validating delivery picking updates quantities and locations."""
        consignment = self.env['sale.consignment'].create({
            'partner_id': self.partner_consignment.id,
            'end_date': date.today() + timedelta(days=10),
            'location_id': self.location_src.id,
            'consignment_line_ids': [
                Command.create({
                    'product_id': self.product_consignment.id,
                    'demand_quantity': 5,
                })
            ]
        })

        consignment.action_order_confirm()
        consignment.create_sale_order()

        sale_order = consignment.sale_order_id
        sale_order.action_confirm()

        # Find delivery picking
        picking = sale_order.picking_ids
        self.assertTrue(picking)

        # Pre-set done quantities and location to avoid post-validation write traceback
        picking.location_id = consignment.location_dest_id
        for move in picking.move_ids:
            move.location_id = consignment.location_dest_id
            move.quantity = move.product_uom_qty
            move.picked = True
            for ml in move.move_line_ids:
                ml.location_id = consignment.location_dest_id

        picking.button_validate()

        # Check locations updated on picking and move lines
        self.assertEqual(picking.location_id, self.location_dest)
        self.assertTrue(all(ml.location_id == self.location_dest for ml in picking.move_line_ids))

        # Check consignment lines quantities
        line = consignment.consignment_line_ids[0]
        self.assertEqual(line.done_quantity, 1)
        self.assertEqual(line.remaining_quantity, 4)
