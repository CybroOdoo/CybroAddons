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
from odoo.tests import TransactionCase


class TestForceAvailability(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Force Availability Test Product',
            'is_storable': True,
        })
        cls.picking_type = cls.env.ref('stock.picking_type_out')
        cls.source_location = cls.picking_type.default_location_src_id
        cls.destination_location = cls.picking_type.default_location_dest_id

    def _create_picking(self, quantity):
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type.id,
            'location_id': self.source_location.id,
            'location_dest_id': self.destination_location.id,
            'move_ids': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': quantity,
                'uom_id': self.product.uom_id.id,
                'location_id': self.source_location.id,
                'location_dest_id': self.destination_location.id,
            })],
        })
        return picking

    def test_action_sets_done_quantity_and_flag(self):
        picking = self._create_picking(3)
        move = picking.move_ids

        picking.action_force_availability()

        self.assertEqual(move.quantity, 3)
        self.assertTrue(picking.is_available)

    def test_action_handles_multiple_pickings(self):
        first_picking = self._create_picking(2)
        second_picking = self._create_picking(5)
        pickings = first_picking | second_picking

        pickings.action_force_availability()

        self.assertEqual(first_picking.move_ids.quantity, 2)
        self.assertEqual(second_picking.move_ids.quantity, 5)
        self.assertTrue(all(pickings.mapped('is_available')))
