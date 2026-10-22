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
"""Unit tests for pos.config stock transfer features."""
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosConfigStockTransfer(TransactionCase):
    """Test pos.config stock transfer methods and workflow."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company

        # Ensure current user has stock group permissions
        self.env.user.group_ids |= self.env.ref('stock.group_stock_user')

        # Find or create a warehouse for the company
        self.warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.company.id)], limit=1
        )
        if not self.warehouse:
            self.warehouse = self.env['stock.warehouse'].create({
                'name': 'Test Warehouse',
                'code': 'TWH',
                'company_id': self.company.id,
            })

        # Locations
        self.stock_location = self.warehouse.lot_stock_id
        self.dest_location = self.env['stock.location'].create({
            'name': 'Test Destination Location',
            'usage': 'internal',
            'location_id': self.warehouse.view_location_id.id,
            'company_id': self.company.id,
        })

        # Picking types
        self.picking_type = self.warehouse.int_type_id
        if not self.picking_type:
            self.picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'internal'),
                ('warehouse_id', '=', self.warehouse.id),
            ], limit=1)

        self.in_type = self.warehouse.in_type_id
        if not self.in_type:
            self.in_type = self.env['stock.picking.type'].search([
                ('code', '=', 'incoming'),
                ('warehouse_id', '=', self.warehouse.id),
            ], limit=1)

        self.out_type = self.warehouse.out_type_id
        if not self.out_type:
            self.out_type = self.env['stock.picking.type'].search([
                ('code', '=', 'outgoing'),
                ('warehouse_id', '=', self.warehouse.id),
            ], limit=1)

        # Products
        self.product_a = self.env['product.product'].create({
            'name': 'Test Product A',
            'is_storable': True,
            'list_price': 100.0,
        })
        self.product_b = self.env['product.product'].create({
            'name': 'Test Product B',
            'is_storable': True,
            'list_price': 50.0,
        })

        # Quantities in stock
        self.env['stock.quant']._update_available_quantity(
            self.product_a, self.stock_location, 50.0
        )
        self.env['stock.quant']._update_available_quantity(
            self.product_b, self.stock_location, 50.0
        )

        # POS Config
        self.pos_config = self.env['pos.config'].create({
            'name': 'Stock Transfer Test POS',
            'stock_transfer': True,
        })

    def test_get_stock_transfer_list(self):
        """Test retrieving picking types, locations, and default warehouse stock."""
        data = self.pos_config.get_stock_transfer_list()
        self.assertIn('picking_type', data)
        self.assertIn('location', data)
        self.assertIn('wh_stock', data)

        self.assertIsInstance(data['picking_type'], list)
        self.assertIsInstance(data['location'], list)
        self.assertTrue(len(data['picking_type']) > 0)
        self.assertTrue(len(data['location']) > 0)
        self.assertEqual(data['wh_stock'], self.warehouse.lot_stock_id.id)

    def test_create_transfer_draft(self):
        """Test creating a stock transfer in 'draft' state."""
        lines = {
            'pro_id': [self.product_a.id],
            'qty': [5],
        }
        res = self.pos_config.create_transfer(
            self.pos_config.id,
            str(self.picking_type.id),
            str(self.stock_location.id),
            str(self.dest_location.id),
            'draft',
            lines,
        )
        self.assertTrue(res.get('id'))
        self.assertTrue(res.get('name'))

        picking = self.env['stock.picking'].browse(res['id'])
        self.assertEqual(picking.state, 'draft')
        self.assertEqual(picking.picking_type_id.id, self.picking_type.id)
        self.assertEqual(picking.location_id.id, self.stock_location.id)
        self.assertEqual(picking.location_dest_id.id, self.dest_location.id)
        self.assertEqual(len(picking.move_ids), 1)
        self.assertEqual(picking.move_ids.product_id.id, self.product_a.id)
        self.assertEqual(picking.move_ids.product_uom_qty, 5.0)

    def test_create_transfer_assigned(self):
        """Test creating a stock transfer in 'assigned' (ready) state."""
        lines = {
            'pro_id': [self.product_a.id],
            'qty': [3],
        }
        res = self.pos_config.create_transfer(
            self.pos_config.id,
            str(self.picking_type.id),
            str(self.stock_location.id),
            str(self.dest_location.id),
            'assigned',
            lines,
        )
        self.assertTrue(res.get('id'))

        picking = self.env['stock.picking'].browse(res['id'])
        self.assertEqual(picking.state, 'assigned')

    def test_create_transfer_done(self):
        """Test creating a stock transfer in 'done' (validated) state."""
        lines = {
            'pro_id': [self.product_a.id],
            'qty': [2],
        }
        res = self.pos_config.create_transfer(
            self.pos_config.id,
            str(self.picking_type.id),
            str(self.stock_location.id),
            str(self.dest_location.id),
            'done',
            lines,
        )
        self.assertTrue(res.get('id'))

        picking = self.env['stock.picking'].browse(res['id'])
        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking.move_ids.quantity, 2.0)

    def test_create_transfer_multiple_products(self):
        """Test creating a stock transfer with multiple products."""
        lines = {
            'pro_id': [self.product_a.id, self.product_b.id],
            'qty': [4, 7],
        }
        res = self.pos_config.create_transfer(
            self.pos_config.id,
            str(self.picking_type.id),
            str(self.stock_location.id),
            str(self.dest_location.id),
            'draft',
            lines,
        )
        picking = self.env['stock.picking'].browse(res['id'])
        self.assertEqual(len(picking.move_ids), 2)
        quantities = {move.product_id.id: move.product_uom_qty for move in picking.move_ids}
        self.assertEqual(quantities[self.product_a.id], 4.0)
        self.assertEqual(quantities[self.product_b.id], 7.0)

    def test_create_transfer_fallback_locations(self):
        """Test location fallback when source_id or dest_id are empty strings."""
        lines = {
            'pro_id': [self.product_a.id],
            'qty': [1],
        }
        res = self.pos_config.create_transfer(
            self.pos_config.id,
            str(self.picking_type.id),
            '',
            '',
            'draft',
            lines,
        )
        self.assertTrue(res.get('id'))
        picking = self.env['stock.picking'].browse(res['id'])
        self.assertTrue(picking.location_id)
        self.assertTrue(picking.location_dest_id)

    def test_create_transfer_incoming(self):
        """Test incoming transfer correctly sets vendor source and warehouse dest."""
        lines = {
            'pro_id': [self.product_a.id],
            'qty': [5],
        }
        res = self.pos_config.create_transfer(
            self.pos_config.id,
            str(self.in_type.id),
            '',
            str(self.stock_location.id),
            'draft',
            lines,
        )
        self.assertTrue(res.get('id'))
        picking = self.env['stock.picking'].browse(res['id'])
        self.assertEqual(picking.picking_type_id.id, self.in_type.id)
        self.assertEqual(picking.location_id.id, self.in_type.default_location_src_id.id)
        self.assertEqual(picking.location_dest_id.id, self.stock_location.id)

    def test_create_transfer_outgoing(self):
        """Test outgoing transfer correctly sets warehouse source and customer dest."""
        lines = {
            'pro_id': [self.product_a.id],
            'qty': [3],
        }
        res = self.pos_config.create_transfer(
            self.pos_config.id,
            str(self.out_type.id),
            str(self.stock_location.id),
            '',
            'draft',
            lines,
        )
        self.assertTrue(res.get('id'))
        picking = self.env['stock.picking'].browse(res['id'])
        self.assertEqual(picking.picking_type_id.id, self.out_type.id)
        self.assertEqual(picking.location_id.id, self.stock_location.id)
        self.assertEqual(picking.location_dest_id.id, self.out_type.default_location_dest_id.id)

    def test_create_transfer_disabled_setting(self):
        """Test that UserError is raised when stock_transfer is disabled on pos.config."""
        self.pos_config.stock_transfer = False
        lines = {
            'pro_id': [self.product_a.id],
            'qty': [1],
        }
        with self.assertRaises(UserError):
            self.pos_config.create_transfer(
                self.pos_config.id,
                str(self.picking_type.id),
                str(self.stock_location.id),
                str(self.dest_location.id),
                'draft',
                lines,
            )

    def test_create_transfer_unauthorized_user(self):
        """Test that AccessError is raised when user lacks stock.group_stock_user."""
        unauth_user = self.env['res.users'].create({
            'name': 'Unauthorized Stock POS User',
            'login': 'unauth_stock_pos_user',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('point_of_sale.group_pos_user').id,
            ])],
        })
        lines = {
            'pro_id': [self.product_a.id],
            'qty': [1],
        }
        with self.assertRaises(AccessError):
            self.pos_config.with_user(unauth_user).create_transfer(
                self.pos_config.id,
                str(self.picking_type.id),
                str(self.stock_location.id),
                str(self.dest_location.id),
                'draft',
                lines,
            )
