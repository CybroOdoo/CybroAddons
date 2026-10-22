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
"""Test suite for stock.picking model extensions."""
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestStockPicking(TransactionCase):
    """Test suite covering inter-company stock transfer generation on picking validation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company_a = cls.env['res.company'].create({
            'name': 'Picking Test Company A',
        })
        cls.company_b = cls.env['res.company'].create({
            'name': 'Picking Test Company B',
        })

        cls.customer_loc = cls.env.ref('stock.stock_location_customers')
        cls.supplier_loc = cls.env.ref('stock.stock_location_suppliers')

        cls.warehouse_a = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.company_a.id)
        ], limit=1)
        if not cls.warehouse_a:
            cls.warehouse_a = cls.env['stock.warehouse'].create({
                'name': 'Warehouse A',
                'code': 'WHA',
                'company_id': cls.company_a.id,
            })

        cls.warehouse_b = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.company_b.id)
        ], limit=1)
        if not cls.warehouse_b:
            cls.warehouse_b = cls.env['stock.warehouse'].create({
                'name': 'Warehouse B',
                'code': 'WHB',
                'company_id': cls.company_b.id,
            })

        cls.picking_type_out_a = cls.env['stock.picking.type'].search([
            ('warehouse_id', '=', cls.warehouse_a.id),
            ('code', '=', 'outgoing'),
        ], limit=1)
        if not cls.picking_type_out_a:
            cls.picking_type_out_a = cls.env['stock.picking.type'].create({
                'name': 'Delivery Orders A',
                'code': 'outgoing',
                'warehouse_id': cls.warehouse_a.id,
                'company_id': cls.company_a.id,
                'sequence_code': 'OUT',
                'default_location_src_id': cls.warehouse_a.lot_stock_id.id,
                'default_location_dest_id': cls.customer_loc.id,
            })

        cls.picking_type_in_a = cls.env['stock.picking.type'].search([
            ('warehouse_id', '=', cls.warehouse_a.id),
            ('code', '=', 'incoming'),
        ], limit=1)
        if not cls.picking_type_in_a:
            cls.picking_type_in_a = cls.env['stock.picking.type'].create({
                'name': 'Receipts A',
                'code': 'incoming',
                'warehouse_id': cls.warehouse_a.id,
                'company_id': cls.company_a.id,
                'sequence_code': 'IN',
                'default_location_src_id': cls.supplier_loc.id,
                'default_location_dest_id': cls.warehouse_a.lot_stock_id.id,
            })

        cls.picking_type_internal_a = cls.env['stock.picking.type'].search([
            ('warehouse_id', '=', cls.warehouse_a.id),
            ('code', '=', 'internal'),
        ], limit=1)
        if not cls.picking_type_internal_a:
            cls.picking_type_internal_a = cls.env['stock.picking.type'].create({
                'name': 'Internal Transfers A',
                'code': 'internal',
                'warehouse_id': cls.warehouse_a.id,
                'company_id': cls.company_a.id,
                'sequence_code': 'INT',
                'default_location_src_id': cls.warehouse_a.lot_stock_id.id,
                'default_location_dest_id': cls.warehouse_a.lot_stock_id.id,
            })

        cls.picking_type_out_b = cls.env['stock.picking.type'].search([
            ('warehouse_id', '=', cls.warehouse_b.id),
            ('code', '=', 'outgoing'),
        ], limit=1)
        if not cls.picking_type_out_b:
            cls.picking_type_out_b = cls.env['stock.picking.type'].create({
                'name': 'Delivery Orders B',
                'code': 'outgoing',
                'warehouse_id': cls.warehouse_b.id,
                'company_id': cls.company_b.id,
                'sequence_code': 'OUT',
                'default_location_src_id': cls.warehouse_b.lot_stock_id.id,
                'default_location_dest_id': cls.customer_loc.id,
            })

        cls.picking_type_in_b = cls.env['stock.picking.type'].search([
            ('warehouse_id', '=', cls.warehouse_b.id),
            ('code', '=', 'incoming'),
        ], limit=1)
        if not cls.picking_type_in_b:
            cls.picking_type_in_b = cls.env['stock.picking.type'].create({
                'name': 'Receipts B',
                'code': 'incoming',
                'warehouse_id': cls.warehouse_b.id,
                'company_id': cls.company_b.id,
                'sequence_code': 'IN',
                'default_location_src_id': cls.supplier_loc.id,
                'default_location_dest_id': cls.warehouse_b.lot_stock_id.id,
            })

        cls.product = cls.env['product.product'].create({
            'name': 'Intercompany Transfer Product',
            'is_storable': True,
        })

        cls.company_b.write({
            'enable_inter_company_transfer': True,
            'destination_warehouse_id': cls.warehouse_b.id,
            'apply_transfer_type': 'all',
        })

    def _create_outgoing_picking_a(self, qty=5.0):
        """Helper to create and confirm an outgoing picking in Company A."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_out_a.id,
            'location_id': self.warehouse_a.lot_stock_id.id,
            'location_dest_id': self.customer_loc.id,
            'partner_id': self.company_b.partner_id.id,
            'company_id': self.company_a.id,
        })
        self.env['stock.move'].create({
            'product_id': self.product.id,
            'product_uom_qty': qty,
            'uom_id': self.product.uom_id.id,
            'location_id': self.warehouse_a.lot_stock_id.id,
            'location_dest_id': self.customer_loc.id,
            'picking_id': picking.id,
            'company_id': self.company_a.id,
        })
        picking.action_confirm()
        return picking

    def _create_incoming_picking_a(self, qty=3.0):
        """Helper to create and confirm an incoming picking in Company A."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_in_a.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.warehouse_a.lot_stock_id.id,
            'partner_id': self.company_b.partner_id.id,
            'company_id': self.company_a.id,
        })
        self.env['stock.move'].create({
            'product_id': self.product.id,
            'product_uom_qty': qty,
            'uom_id': self.product.uom_id.id,
            'location_id': self.supplier_loc.id,
            'location_dest_id': self.warehouse_a.lot_stock_id.id,
            'picking_id': picking.id,
            'company_id': self.company_a.id,
        })
        picking.action_confirm()
        return picking

    def test_outgoing_picking_creates_counterpart_receipt(self):
        """Test that validating an outgoing picking creates a counterpart receipt in target company."""
        self.company_b.apply_transfer_type = 'all'
        self.env['stock.quant']._update_available_quantity(
            self.product, self.warehouse_a.lot_stock_id, 10.0
        )
        picking = self._create_outgoing_picking_a(qty=5.0)
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty

        picking.button_validate()
        self.assertEqual(picking.state, 'done')

        counterpart = self.env['stock.picking'].search([
            ('origin', '=', picking.name),
            ('company_id', '=', self.company_b.id),
        ])
        self.assertTrue(counterpart)
        self.assertEqual(counterpart.partner_id, self.company_a.partner_id)
        self.assertEqual(counterpart.picking_type_id.code, 'incoming')
        self.assertTrue(counterpart.auto_generated)
        self.assertEqual(len(counterpart.move_ids), 1)
        self.assertEqual(counterpart.move_ids.product_id, self.product)
        self.assertEqual(counterpart.move_ids.product_uom_qty, 5.0)

    def test_incoming_picking_creates_counterpart_delivery(self):
        """Test that validating an incoming picking creates a counterpart delivery in target company."""
        self.company_b.apply_transfer_type = 'incoming'
        picking = self._create_incoming_picking_a(qty=3.0)
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty

        picking.button_validate()
        self.assertEqual(picking.state, 'done')

        counterpart = self.env['stock.picking'].search([
            ('origin', '=', picking.name),
            ('company_id', '=', self.company_b.id),
        ])
        self.assertTrue(counterpart)
        self.assertEqual(counterpart.partner_id, self.company_a.partner_id)
        self.assertEqual(counterpart.picking_type_id.code, 'outgoing')
        self.assertTrue(counterpart.auto_generated)
        self.assertEqual(len(counterpart.move_ids), 1)
        self.assertEqual(counterpart.move_ids.product_id, self.product)
        self.assertEqual(counterpart.move_ids.product_uom_qty, 3.0)

    def test_no_counterpart_when_intercompany_disabled(self):
        """Test that no counterpart transfer is created if target company has transfers disabled."""
        self.company_b.enable_inter_company_transfer = False
        self.env['stock.quant']._update_available_quantity(
            self.product, self.warehouse_a.lot_stock_id, 10.0
        )
        picking = self._create_outgoing_picking_a(qty=2.0)
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty

        picking.button_validate()
        self.assertEqual(picking.state, 'done')

        counterpart = self.env['stock.picking'].search([
            ('origin', '=', picking.name),
            ('company_id', '=', self.company_b.id),
        ])
        self.assertFalse(counterpart)

    def test_no_counterpart_when_operation_type_mismatches(self):
        """Test that no counterpart is created when apply_transfer_type does not match operation."""
        self.company_b.apply_transfer_type = 'incoming'
        self.env['stock.quant']._update_available_quantity(
            self.product, self.warehouse_a.lot_stock_id, 10.0
        )
        picking = self._create_outgoing_picking_a(qty=2.0)
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty

        picking.button_validate()
        self.assertEqual(picking.state, 'done')

        counterpart = self.env['stock.picking'].search([
            ('origin', '=', picking.name),
            ('company_id', '=', self.company_b.id),
        ])
        self.assertFalse(counterpart)

    def test_auto_generated_picking_does_not_retrigger(self):
        """Test that auto-generated pickings do not trigger recursive counterpart creation."""
        picking = self._create_outgoing_picking_a(qty=1.0)
        picking.auto_generated = True
        self.env['stock.quant']._update_available_quantity(
            self.product, self.warehouse_a.lot_stock_id, 10.0
        )
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty

        picking.button_validate()
        self.assertEqual(picking.state, 'done')

        counterpart = self.env['stock.picking'].search([
            ('origin', '=', picking.name),
            ('company_id', '=', self.company_b.id),
        ])
        self.assertFalse(counterpart)

    def test_multi_record_button_validate(self):
        """Test that validating multiple pickings in batch executes without singleton errors."""
        self.env['stock.quant']._update_available_quantity(
            self.product, self.warehouse_a.lot_stock_id, 20.0
        )
        picking1 = self._create_outgoing_picking_a(qty=2.0)
        picking2 = self._create_outgoing_picking_a(qty=3.0)
        pickings = picking1 | picking2

        pickings.action_assign()
        for move in pickings.move_ids:
            move.quantity = move.product_uom_qty

        pickings.button_validate()
        self.assertTrue(all(p.state == 'done' for p in pickings))

        counterparts = self.env['stock.picking'].search([
            ('origin', 'in', pickings.mapped('name')),
            ('company_id', '=', self.company_b.id),
        ])
        self.assertEqual(len(counterparts), 2)

    def test_internal_transfer_raises_error(self):
        """Test that attempting intercompany transfer on internal picking raises UserError."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_internal_a.id,
            'location_id': self.warehouse_a.lot_stock_id.id,
            'location_dest_id': self.warehouse_a.lot_stock_id.id,
            'partner_id': self.company_b.partner_id.id,
            'company_id': self.company_a.id,
        })
        with self.assertRaises(UserError):
            picking.create_intercompany_transfer()
