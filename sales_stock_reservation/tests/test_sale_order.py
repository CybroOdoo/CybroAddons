# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestSaleOrderReservation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrderReservation, cls).setUpClass()
        # Create a basic partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner SO',
        })
        
        # Create a product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product SO',
            'type': 'consu',
            'is_storable': True,
        })
        
        # Set up locations for testing
        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        if not cls.warehouse:
            cls.warehouse = cls.env['stock.warehouse'].create({
                'name': 'Test Warehouse',
                'code': 'TWH',
            })
        cls.source_location = cls.warehouse.lot_stock_id
        
        try:
            cls.dest_location = cls.env.ref('sales_stock_reservation.sale_stock_reservation')
        except ValueError:
            cls.dest_location = cls.env['stock.location'].create({
                'name': 'Test Stock Reservation Location',
                'location_id': cls.warehouse.view_location_id.id,
            })
            
        cls.env['ir.config_parameter'].sudo().set_param(
            'sales_stock_reservation.source_location_id', cls.source_location.id
        )
        cls.env['ir.config_parameter'].sudo().set_param(
            'sales_stock_reservation.destination_location_id', cls.dest_location.id
        )

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_uom_qty': 5.0,
                })
            ]
        })

    def test_action_create_stock_reservation(self):
        """Test action_create_stock_reservation returns correct action dictionary."""
        action = self.sale_order.action_create_stock_reservation()
        self.assertEqual(action.get('res_model'), 'sale.stock.reservation')
        self.assertEqual(action.get('context', {}).get('default_sale_order_id'), self.sale_order.id)
        
        # Verify the default_stock_reservation_ids contains correct data
        lines = action.get('context', {}).get('default_stock_reservation_ids', [])
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0][2]['product_id'], self.product.id)
        self.assertEqual(lines[0][2]['quantity'], 5.0)

    def test_action_cancel_reservation(self):
        """Test action_cancel_reservation cancels reservation moves and updates status."""
        # Create a stock move to associate with reserved stock
        move = self.env['stock.move'].create({
            'name': 'Test Move SO',
            'location_id': self.source_location.id,
            'location_dest_id': self.dest_location.id,
            'product_id': self.product.id,
            'product_uom_qty': 5.0,
            'product_uom': self.product.uom_id.id,
        })
        move._action_confirm()
        
        reserved_stock = self.env['stock.reserved'].create({
            'order_line_name': 'Test Line SO',
            'product_id': self.product.id,
            'reserved_quantity': 5.0,
            'sale_order_id': self.sale_order.id,
            'status': 'reserved',
            'move_id': move.id,
        })
        
        self.sale_order.reserved_stock_ids = [(6, 0, reserved_stock.ids)]
        self.sale_order.state_reservation = 'reserved'
        
        # Cancel reservation
        self.sale_order.action_cancel_reservation()
        self.assertEqual(self.sale_order.state_reservation, 'cancel')
        self.assertEqual(reserved_stock.status, 'cancelled')
        self.assertEqual(move.state, 'cancel')

    def test_action_confirm(self):
        """Test action_confirm cancels reservation and confirms order."""
        # Create a stock move to associate with reserved stock
        move = self.env['stock.move'].create({
            'name': 'Test Move SO 2',
            'location_id': self.source_location.id,
            'location_dest_id': self.dest_location.id,
            'product_id': self.product.id,
            'product_uom_qty': 5.0,
            'product_uom': self.product.uom_id.id,
        })
        move._action_confirm()
        
        reserved_stock = self.env['stock.reserved'].create({
            'order_line_name': 'Test Line SO 2',
            'product_id': self.product.id,
            'reserved_quantity': 5.0,
            'sale_order_id': self.sale_order.id,
            'status': 'reserved',
            'move_id': move.id,
        })
        
        self.sale_order.reserved_stock_ids = [(6, 0, reserved_stock.ids)]
        self.sale_order.state_reservation = 'reserved'
        
        # Confirm Sale Order
        self.sale_order.action_confirm()
        
        # Reservation should be cancelled
        self.assertEqual(self.sale_order.state_reservation, 'cancel')
        self.assertEqual(reserved_stock.status, 'cancelled')
        self.assertEqual(move.state, 'cancel')
        
        # Sale Order state should be 'sale' (confirmed)
        self.assertEqual(self.sale_order.state, 'sale')
