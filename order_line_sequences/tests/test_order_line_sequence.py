# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOrderLineSequence(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestOrderLineSequence, cls).setUpClass()

        # Create partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })

        # Create products
        cls.product_a = cls.env['product.product'].create({
            'name': 'Test Product A',
            'list_price': 10.0,
            'standard_price': 5.0,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Test Product B',
            'list_price': 20.0,
            'standard_price': 10.0,
        })

        # Find or create warehouse/locations for Stock Picking test
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        if not cls.warehouse:
            cls.warehouse = cls.env['stock.warehouse'].create({
                'name': 'Test Warehouse',
                'code': 'TWH',
                'partner_id': cls.partner.id,
            })
        cls.picking_type = cls.env['stock.picking.type'].search([
            ('warehouse_id', '=', cls.warehouse.id),
            ('code', '=', 'outgoing')
        ], limit=1)
        if not cls.picking_type:
            cls.picking_type = cls.env['stock.picking.type'].create({
                'name': 'Test Delivery',
                'sequence_code': 'TDEL',
                'code': 'outgoing',
                'warehouse_id': cls.warehouse.id,
            })
        cls.location_src = cls.picking_type.default_location_src_id or cls.warehouse.lot_stock_id
        cls.location_dest = cls.picking_type.default_location_dest_id or cls.env.ref('stock.stock_location_customers', raise_if_not_found=False)
        if not cls.location_dest:
            cls.location_dest = cls.env['stock.location'].create({
                'name': 'Customer Location',
                'usage': 'customer',
            })

    def test_sale_order_line_sequence(self):
        """Test sequence number calculation on sale order lines."""
        # Create a sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1,
                    'price_unit': 10.0,
                    'sequence': 10,
                }),
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'First Section',
                    'sequence': 20,
                }),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'First Note',
                    'sequence': 30,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_uom_qty': 2,
                    'price_unit': 20.0,
                    'sequence': 40,
                }),
            ]
        })

        # Read the lines in order of their sequence
        lines = sale_order.order_line.sorted(key=lambda l: l.sequence)
        self.assertEqual(len(lines), 4)

        # Check calculated sequence numbers
        # Line 1: Product A -> Should be 1
        self.assertEqual(lines[0].sequence_number, 1)

        # Line 2: Section -> Should be 2, but sequence_number increment += 0
        self.assertEqual(lines[1].sequence_number, 2)

        # Line 3: Note -> Should be 2, sequence_number increment += 0
        self.assertEqual(lines[2].sequence_number, 2)

        # Line 4: Product B -> Should be 2, sequence_number increment += 1
        self.assertEqual(lines[3].sequence_number, 2)

        # Add one more product to ensure sequence increments to 3
        extra_line = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 1,
            'price_unit': 10.0,
            'sequence': 50,
        })
        self.assertEqual(extra_line.sequence_number, 3)

    def test_purchase_order_line_sequence(self):
        """Test sequence number calculation on purchase order lines."""
        # Create a purchase order
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_qty': 1,
                    'price_unit': 5.0,
                    'sequence': 10,
                }),
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'First Section',
                    'sequence': 20,
                    'product_qty': 0.0,
                }),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'First Note',
                    'sequence': 30,
                    'product_qty': 0.0,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_qty': 2,
                    'price_unit': 10.0,
                    'sequence': 40,
                }),
            ]
        })

        # Read the lines in order of their sequence
        lines = purchase_order.order_line.sorted(key=lambda l: l.sequence)
        self.assertEqual(len(lines), 4)

        # Check calculated sequence numbers
        # Line 1: Product A -> Should be 1
        self.assertEqual(lines[0].sequence_number, 1)

        # Line 2: Section -> Should be 2
        self.assertEqual(lines[1].sequence_number, 2)

        # Line 3: Note -> Should be 2
        self.assertEqual(lines[2].sequence_number, 2)

        # Line 4: Product B -> Should be 2
        self.assertEqual(lines[3].sequence_number, 2)

        # Add one more product to ensure sequence increments to 3
        extra_line = self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'product_id': self.product_a.id,
            'product_qty': 1,
            'price_unit': 5.0,
            'sequence': 50,
        })
        self.assertEqual(extra_line.sequence_number, 3)

    def test_stock_move_sequence(self):
        """Test sequence number calculation on stock moves and the onchange method on picking."""
        # Create a picking
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'move_ids': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom': self.product_a.uom_id.id,
                    'product_uom_qty': 1,
                    'location_id': self.location_src.id,
                    'location_dest_id': self.location_dest.id,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_uom': self.product_b.uom_id.id,
                    'product_uom_qty': 2,
                    'location_id': self.location_src.id,
                    'location_dest_id': self.location_dest.id,
                }),
            ]
        })

        # Trigger sequence_number computation
        moves = picking.move_ids
        self.assertEqual(len(moves), 2)
        moves.invalidate_recordset(['sequence_number'])
        moves.mapped('sequence_number')
        # Check computed values
        self.assertEqual(moves[0].sequence_number, 1)
        self.assertEqual(moves[1].sequence_number, 2)

        # Test the onchange method _onchange_move_ids_without_package
        # We manually modify sequence_number to simulate a clean state
        for move in moves:
            move.sequence_number = 0

        # Run onchange
        picking._onchange_move_ids_without_package()
        self.assertEqual(moves[0].sequence_number, 1)
        self.assertEqual(moves[1].sequence_number, 2)
