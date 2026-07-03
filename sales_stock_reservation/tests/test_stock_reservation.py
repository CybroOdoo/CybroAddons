# -*- coding: utf-8 -*-
# ############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################
from odoo.tests import common
from odoo import fields


class TestStockReservation(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestStockReservation, cls).setUpClass()

        # 1. Retrieve or setup standard stock locations
        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        if not cls.warehouse:
            cls.warehouse = cls.env['stock.warehouse'].create({
                'name': 'Test Warehouse',
                'code': 'TWH',
            })

        cls.source_location = cls.warehouse.lot_stock_id
        cls.dest_location = cls.env.ref('sales_stock_reservation.sale_stock_reservation')

        if not cls.dest_location:
            cls.dest_location = cls.env['stock.location'].create({
                'name': 'Test Stock Reservation Location',
                'location_id': cls.env.ref('stock.stock_location_locations').id,
            })

        # Set the location parameters in system parameters
        cls.env['ir.config_parameter'].sudo().set_param(
            'sales_stock_reservation.source_location_id', cls.source_location.id
        )
        cls.env['ir.config_parameter'].sudo().set_param(
            'sales_stock_reservation.destination_location_id', cls.dest_location.id
        )

        # 2. Create products and partners for testing
        cls.product = cls.env['product.product'].create({
            'name': 'Test Reservation Product',
            'type': 'consu',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'lst_price': 100.0,
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Reservation Customer',
        })

        # Create a user for receiving email notifications
        cls.notify_user = cls.env['res.users'].create({
            'name': 'Notify User',
            'login': 'notify_user@example.com',
            'email': 'notify_user@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_stock_reservation_flow(self):
        """Test the full stock reservation flow: creation, reservation, cancellation, and confirmation."""
        # 1. Create Sale Order in Draft State
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'apply_stock_reservation': True,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 10.0,
                    'price_unit': 100.0,
                })
            ]
        })

        # Verify action_create_stock_reservation returns correct action info
        action = sale_order.action_create_stock_reservation()
        self.assertEqual(action['res_model'], 'sale.stock.reservation')
        self.assertEqual(action['context']['default_sale_order_id'], sale_order.id)
        self.assertTrue(len(action['context']['default_stock_reservation_ids']) > 0)

        # 2. Create and run the Stock Reservation wizard
        wizard_vals = {
            'sale_order_id': sale_order.id,
            'mail_notification_ids': [(6, 0, [self.notify_user.id])],
            'stock_reservation_ids': [
                (0, 0, {
                    'order_line_name': action['context']['default_stock_reservation_ids'][0][2]['order_line_name'],
                    'product_id': self.product.id,
                    'quantity': 10.0,
                    'unit_of_measure_id': self.product.uom_id.id,
                    'reserve_quantity': '10.0',
                })
            ]
        }
        wizard = self.env['sale.stock.reservation'].create(wizard_vals)

        # Confirm wizard action to reserve stock
        wizard.action_reserve_stock()

        # Check sale order state reservation
        self.assertEqual(sale_order.state_reservation, 'reserved')

        # Check reserved stock details
        self.assertEqual(len(sale_order.reserved_stock_ids), 1)
        reserved_stock = sale_order.reserved_stock_ids[0]
        self.assertEqual(reserved_stock.product_id, self.product)
        self.assertEqual(reserved_stock.reserved_quantity, 10.0)
        self.assertEqual(reserved_stock.status, 'reserved')
        self.assertTrue(reserved_stock.name.startswith('STOCK/RES/'))

        # Check stock move details
        move = reserved_stock.move_id
        self.assertTrue(move)
        self.assertEqual(move.product_id, self.product)
        self.assertEqual(move.product_uom_qty, 10.0)
        self.assertEqual(move.location_id.id, self.source_location.id)
        self.assertEqual(move.location_dest_id.id, self.dest_location.id)
        self.assertIn(move.state, ['confirmed', 'assigned', 'waiting'])

        # Check that the email notification was generated and sent
        mails = self.env['mail.mail'].search([('subject', 'like', f'Stock Reservation: {sale_order.name}')])
        self.assertTrue(mails)
        self.assertIn(self.notify_user.login, mails[0].email_to)

        # 3. Test action_cancel_reservation
        sale_order.action_cancel_reservation()
        self.assertEqual(sale_order.state_reservation, 'cancel')
        self.assertEqual(reserved_stock.status, 'cancelled')
        self.assertEqual(move.state, 'cancel')

    def test_stock_reservation_confirm_order(self):
        """Test that confirming the sale order automatically cancels any active reservation."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'apply_stock_reservation': True,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 5.0,
                    'price_unit': 100.0,
                })
            ]
        })

        action = sale_order.action_create_stock_reservation()
        wizard_vals = {
            'sale_order_id': sale_order.id,
            'stock_reservation_ids': [
                (0, 0, {
                    'order_line_name': action['context']['default_stock_reservation_ids'][0][2]['order_line_name'],
                    'product_id': self.product.id,
                    'quantity': 5.0,
                    'unit_of_measure_id': self.product.uom_id.id,
                    'reserve_quantity': '5.0',
                })
            ]
        }
        wizard = self.env['sale.stock.reservation'].create(wizard_vals)
        wizard.action_reserve_stock()

        reserved_stock = sale_order.reserved_stock_ids[0]
        self.assertEqual(reserved_stock.status, 'reserved')
        move = reserved_stock.move_id
        self.assertIn(move.state, ['confirmed', 'assigned', 'waiting'])

        # Confirm the Sale Order
        sale_order.action_confirm()

        # State should now be 'sale' and the reservation cancelled
        self.assertEqual(sale_order.state, 'sale')
        self.assertEqual(sale_order.state_reservation, 'cancel')
        self.assertEqual(reserved_stock.status, 'cancelled')
        self.assertEqual(move.state, 'cancel')

    def test_res_config_settings_fields(self):
        """Test that config settings fields are defined on res.config.settings."""
        fields_info = self.env['res.config.settings'].fields_get(['source_location_id', 'destination_location_id'])
        self.assertIn('source_location_id', fields_info)
        self.assertIn('destination_location_id', fields_info)

        # Set the location parameters in system parameters
        self.env['ir.config_parameter'].sudo().set_param(
            'sales_stock_reservation.source_location_id', self.source_location.id
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'sales_stock_reservation.destination_location_id', self.dest_location.id
        )

        src_param = self.env['ir.config_parameter'].sudo().get_param('sales_stock_reservation.source_location_id')
        dest_param = self.env['ir.config_parameter'].sudo().get_param('sales_stock_reservation.destination_location_id')

        self.assertEqual(int(src_param), self.source_location.id)
        self.assertEqual(int(dest_param), self.dest_location.id)
