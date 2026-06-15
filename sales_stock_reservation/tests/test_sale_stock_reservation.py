# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from unittest.mock import patch

@tagged('post_install', '-at_install')
class TestSaleStockReservationWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleStockReservationWizard, cls).setUpClass()
        # Create a test customer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Wizard',
        })
        
        # Create a storable product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product Wizard',
            'type': 'consu',
            'is_storable': True,
        })
        
        # Set up locations
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
        
        # Create Sale Order
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_uom_qty': 10.0,
                })
            ]
        })
        
        # Add stock quantity for testing reservation assignment
        cls.env['stock.quant']._update_available_quantity(cls.product, cls.source_location, 20.0)

        # Create a user with a valid email for email notifications
        cls.test_user = cls.env['res.users'].create({
            'name': 'Wizard Test User',
            'login': 'wizard_test_user@example.com',
            'email': 'wizard_test_user@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_wizard_reservation_execution(self):
        """Test creating a stock reservation via the wizard with mocked request."""
        context = {
            'default_sale_order_id': self.sale_order.id,
            'default_stock_reservation_ids': [
                (0, 0, {
                    'order_line_name': f"{self.sale_order.name}-Line1",
                    'product_id': self.product.id,
                    'quantity': 10.0,
                    'unit_of_measure_id': self.product.uom_id.id,
                    'reserve_quantity': '10.0'
                })
            ]
        }
        
        # Create wizard instance
        wizard = self.env['sale.stock.reservation'].with_context(context).create({
            'mail_notification_ids': [(6, 0, self.test_user.ids)]
        })
        
        self.assertEqual(wizard.sale_order_id, self.sale_order)
        self.assertEqual(len(wizard.stock_reservation_ids), 1)
        
        # Run action_reserve_stock under mock request context
        from odoo.addons.sales_stock_reservation.wizard import sale_stock_reservation as wizard_mod
        class MockRequest:
            def __init__(self, env):
                self.env = env
        mock_req = MockRequest(self.env)
        old_req = getattr(wizard_mod, 'request', None)
        wizard_mod.request = mock_req
        try:
            wizard.action_reserve_stock()
        finally:
            wizard_mod.request = old_req
        
        # Verify SO state is updated
        self.assertEqual(self.sale_order.state_reservation, 'reserved')
        
        # Verify reserved stock record is created
        self.assertEqual(len(self.sale_order.reserved_stock_ids), 1)
        res_stock = self.sale_order.reserved_stock_ids[0]
        self.assertEqual(res_stock.product_id, self.product)
        self.assertEqual(res_stock.reserved_quantity, 10.0)
        self.assertEqual(res_stock.status, 'reserved')
        
        # Verify stock move creation
        self.assertTrue(res_stock.move_id)
        self.assertEqual(res_stock.move_id.product_id, self.product)
        self.assertEqual(res_stock.move_id.location_id, self.source_location)
        self.assertEqual(res_stock.move_id.location_dest_id, self.dest_location)
        self.assertEqual(res_stock.move_id.product_uom_qty, 10.0)
        
        # Verify mail is created
        mail = self.env['mail.mail'].search([
            ('subject', '=', f"Stock Reservation: {self.sale_order.name}")
        ])
        self.assertTrue(mail)
        self.assertIn(self.test_user.email, mail.email_to)

    def test_res_config_settings_locations(self):
        """Test that settings save locations correctly into system parameters."""
        config = self.env['res.config.settings'].create({
            'source_location_id': self.source_location.id,
            'destination_location_id': self.dest_location.id,
        })
        config.execute()
        
        # Verify parameter values
        src_param = int(self.env['ir.config_parameter'].sudo().get_param(
            'sales_stock_reservation.source_location_id'
        ))
        dest_param = int(self.env['ir.config_parameter'].sudo().get_param(
            'sales_stock_reservation.destination_location_id'
        ))
        self.assertEqual(src_param, self.source_location.id)
        self.assertEqual(dest_param, self.dest_location.id)
