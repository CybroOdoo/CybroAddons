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
"""Unit tests for the stock.picking model extensions."""

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestStockPicking(TransactionCase):
    """Test cases for stock.picking action_view_products method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

    def test_action_view_products(self):
        """Test action_view_products returns the correct action dictionary."""
        action = self.picking.action_view_products()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'product.product')
        self.assertEqual(action.get('view_mode'), 'kanban,list,form')
        self.assertNotIn('view_type', action, "Deprecated view_type must not be present")
        self.assertEqual(action.get('context', {}).get('picking_id'), self.picking.id)
        self.assertEqual(action.get('context', {}).get('default_picking_id'), self.picking.id)
        domain = action.get('domain', [])
        self.assertIn(('type', 'in', ['consu', 'combo']), domain)
