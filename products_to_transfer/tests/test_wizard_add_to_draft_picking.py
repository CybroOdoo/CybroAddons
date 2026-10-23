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
"""Unit tests for the wizard.add.to.draft.picking wizard."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestWizardAddToDraftPicking(TransactionCase):
    """Test cases for wizard.add.to.draft.picking model."""

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

    def test_action_add_to_transfer_success(self):
        """Test adding product with custom qty to draft picking."""
        wizard = self.env['wizard.add.to.draft.picking'].create({
            'product_id': self.product.id,
            'picking_id': self.picking.id,
            'qty': 5.0,
        })
        wizard.action_add_to_transfer()

        move = self.picking.move_ids.filtered(lambda m: m.product_id == self.product)
        self.assertTrue(move)
        self.assertEqual(move.product_uom_qty, 5.0)

        # Calling again adds to existing move
        wizard_repeat = self.env['wizard.add.to.draft.picking'].create({
            'product_id': self.product.id,
            'picking_id': self.picking.id,
            'qty': 3.0,
        })
        wizard_repeat.action_add_to_transfer()
        self.assertEqual(move.product_uom_qty, 8.0)

    def test_action_add_to_transfer_no_picking(self):
        """Test ValidationError raised if no picking is specified."""
        wizard = self.env['wizard.add.to.draft.picking'].create({
            'product_id': self.product.id,
            'picking_id': False,
            'qty': 1.0,
        })
        with self.assertRaises(ValidationError):
            wizard.action_add_to_transfer()
