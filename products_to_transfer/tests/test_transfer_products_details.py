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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Unit tests for the transfer.products.details wizard."""

from datetime import timedelta
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestTransferProductsDetails(TransactionCase):
    """Test cases for transfer.products.details wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Consumable Product',
            'type': 'consu',
        })
        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.picking_type = cls.env['stock.picking.type'].search([
            ('warehouse_id', '=', cls.warehouse.id),
            ('code', '=', 'outgoing'),
        ], limit=1)
        cls.picking = cls.env['stock.picking'].create({
            'picking_type_id': cls.picking_type.id,
            'location_id': cls.picking_type.default_location_src_id.id,
            'location_dest_id': cls.picking_type.default_location_dest_id.id,
        })

    def test_default_methods(self):
        """Test _default_product_id and _default_picking_id context resolution."""
        wizard = self.env['transfer.products.details'].with_context(
            default_product_id=self.product.id,
            default_picking_id=self.picking.id,
        ).new({})
        self.assertEqual(wizard.product_id, self.product)
        self.assertEqual(wizard.picking_id, self.picking)
        self.assertEqual(wizard.qty, 1.0)
        self.assertEqual(wizard.date_from, fields.Date.today() - timedelta(days=30))

    def test_action_add_to_transfer(self):
        """Test action_add_to_transfer creates and updates stock moves."""
        wizard = self.env['transfer.products.details'].create({
            'product_id': self.product.id,
            'picking_id': self.picking.id,
            'qty': 4.0,
        })
        wizard.action_add_to_transfer()

        move = self.picking.move_ids.filtered(lambda m: m.product_id == self.product)
        self.assertTrue(move)
        self.assertEqual(move.product_uom_qty, 4.0)

        # Calling again updates quantity
        wizard2 = self.env['transfer.products.details'].create({
            'product_id': self.product.id,
            'picking_id': self.picking.id,
            'qty': 6.0,
        })
        wizard2.action_add_to_transfer()
        self.assertEqual(move.product_uom_qty, 10.0)

    def test_action_add_to_transfer_no_picking(self):
        """Test validation error when picking is missing on unsaved wizard."""
        wizard = self.env['transfer.products.details'].new({
            'product_id': self.product.id,
            'picking_id': False,
            'qty': 1.0,
        })
        with self.assertRaises(ValidationError):
            wizard.action_add_to_transfer()

    def test_onchange_date_from(self):
        """Test _onchange_date_from correctly populates transfer history."""
        # Create a done picking with move for this product
        partner = self.env['res.partner'].create({'name': 'History Partner'})
        done_picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type.id,
            'location_id': self.picking_type.default_location_src_id.id,
            'location_dest_id': self.picking_type.default_location_dest_id.id,
            'partner_id': partner.id,
            'date_done': fields.Datetime.now(),
        })
        move = self.env['stock.move'].create({
            'product_id': self.product.id,
            'product_uom_qty': 12.0,
            'uom_id': self.product.uom_id.id,
            'location_id': self.picking_type.default_location_src_id.id,
            'location_dest_id': self.picking_type.default_location_dest_id.id,
            'picking_id': done_picking.id,
            'state': 'done',
        })

        wizard = self.env['transfer.products.details'].new({
            'product_id': self.product.id,
            'picking_id': self.picking.id,
            'date_from': fields.Date.today() - timedelta(days=10),
        })
        wizard._onchange_date_from()
        self.assertTrue(wizard.transfer_history_ids)
        history_line = wizard.transfer_history_ids[0]
        self.assertEqual(history_line.qty, 12.0)
        self.assertEqual(history_line.partner_id, partner)
        self.assertEqual(history_line.picking, done_picking.name)
