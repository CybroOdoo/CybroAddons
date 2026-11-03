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
from odoo.exceptions import UserError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestStockReservation(common.TransactionCase):
    """Test cases for checking the product stock reservation lifecycle."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'customer@example.com',
        })

        cls.partner_no_email = cls.env['res.partner'].create({
            'name': 'Partner Without Email',
            'email': False,
        })

        cls.internal_user = cls.env['res.users'].create({
            'name': 'Stock Notified User',
            'login': 'stock_user@example.com',
            'email': 'stock_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Reserved Product',
            'type': 'consu',
            'is_storable': True,
        })

        cls.service_product = cls.env['product.product'].create({
            'name': 'Service Product',
            'type': 'service',
        })

        cls.warehouse = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.env.company.id),
        ], limit=1)

        cls.env['stock.quant']._update_available_quantity(
            cls.product, cls.warehouse.lot_stock_id, 100
        )

    def test_01_reservation_lifecycle(self):
        """Test creating a reservation, verifying it, and then cancelling it."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id,
            'apply_stock_reservation': True,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10.0,
            })],
        })

        wizard_action = sale_order.action_create_stock_reservation()
        wizard = self.env['sale.stock.reservation'].with_context(
            **wizard_action['context']
        ).create({})

        wizard.action_reserve_stock()

        self.assertEqual(sale_order.state_reservation, 'reserved',
                         "Sale Order reservation state should be 'reserved'.")
        self.assertTrue(sale_order.reserved_stock_ids,
                        "Reserved stock records should be created.")

        reserved_line = sale_order.reserved_stock_ids[0]
        self.assertEqual(reserved_line.reserved_quantity, 10.0,
                         "Reserved quantity should match the order line.")
        self.assertEqual(reserved_line.status, 'reserved',
                         "Status of reserved line should be 'reserved'.")
        self.assertTrue(reserved_line.name.startswith("STOCK/RES/"),
                        "Reserved stock sequence name should follow prefix.")

        move = reserved_line.move_id
        self.assertTrue(move, "A stock move should be linked to the reservation.")
        self.assertIn(move.state, ['confirmed', 'assigned'],
                      "The stock move should be in 'confirmed' or 'assigned' state.")

        customer_mail = self.env['mail.mail'].search([
            ('email_to', '=', self.partner.email),
        ])
        self.assertTrue(customer_mail, "An email should be sent to customer.")

        chatter_msg = sale_order.message_ids.filtered(
            lambda m: "Stock Reservation Confirmed" in (m.body or '')
        )
        self.assertTrue(chatter_msg, "A confirmation note should be posted in chatter.")

        sale_order.action_cancel_reservation()

        self.assertEqual(sale_order.state_reservation, 'cancel',
                         "Sale Order reservation state should be 'cancel'.")
        self.assertEqual(reserved_line.status, 'cancelled',
                         "Status of reserved line should be 'cancelled'.")
        self.assertEqual(move.state, 'cancel',
                         "The stock move should be in 'cancel' state.")

    def test_02_auto_cancel_on_confirm(self):
        """Test that confirming a Sale Order automatically cancels its reservation if reserved."""
        # Case A: Sale order without reservation confirmed
        unreserved_so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2.0,
            })],
        })
        unreserved_so.action_confirm()
        self.assertFalse(unreserved_so.state_reservation,
                         "Unreserved SO should not have state_reservation set to cancel upon confirmation.")

        # Case B: Sale order with reservation confirmed
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id,
            'apply_stock_reservation': True,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5.0,
            })],
        })

        wizard_action = sale_order.action_create_stock_reservation()
        wizard = self.env['sale.stock.reservation'].with_context(
            **wizard_action['context']
        ).create({})
        wizard.action_reserve_stock()

        sale_order.action_confirm()

        self.assertEqual(sale_order.state_reservation, 'cancel',
                         "Reservation should be automatically cancelled on SO confirmation.")
        self.assertEqual(sale_order.reserved_stock_ids[0].status, 'cancelled',
                         "Reserved stock status should be 'cancelled'.")
        self.assertEqual(sale_order.reserved_stock_ids[0].move_id.state, 'cancel',
                         "Associated stock move should be cancelled.")

    def test_03_res_config_settings_and_custom_locations(self):
        """Test configuring custom stock locations in settings and reserving stock through them."""
        custom_source = self.env['stock.location'].create({
            'name': 'Custom Source Location',
            'usage': 'internal',
            'location_id': self.warehouse.view_location_id.id,
        })
        custom_dest = self.env['stock.location'].create({
            'name': 'Custom Destination Location',
            'usage': 'customer',
            'location_id': self.env.ref('stock.stock_location_customers').id,
        })

        settings = self.env['res.config.settings'].create({
            'source_location_id': custom_source.id,
            'destination_location_id': custom_dest.id,
        })
        settings.execute()

        get_source = self.env['ir.config_parameter'].sudo().get_param(
            'sales_stock_reservation.source_location_id'
        )
        self.assertEqual(int(get_source), custom_source.id)

        self.env['stock.quant']._update_available_quantity(
            self.product, custom_source, 50
        )

        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id,
            'apply_stock_reservation': True,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 8.0,
            })],
        })

        wizard_action = sale_order.action_create_stock_reservation()
        wizard = self.env['sale.stock.reservation'].with_context(
            **wizard_action['context']
        ).create({
            'mail_notification_ids': [(6, 0, [self.internal_user.id])],
        })
        wizard.action_reserve_stock()

        reserved_line = sale_order.reserved_stock_ids[0]
        self.assertEqual(reserved_line.move_id.location_id.id, custom_source.id,
                         "Move source location should match configured location.")
        self.assertEqual(reserved_line.move_id.location_dest_id.id, custom_dest.id,
                         "Move destination location should match configured location.")

        user_mail = self.env['mail.mail'].search([
            ('email_to', 'ilike', self.internal_user.email),
        ])
        self.assertTrue(user_mail, "An email should be sent to notified users.")

    def test_04_partial_reservation_and_validations(self):
        """Test partial reservation quantities, available stock validation, and partner without email."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_no_email.id,
            'warehouse_id': self.warehouse.id,
            'apply_stock_reservation': True,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 10.0,
                }),
                (0, 0, {
                    'product_id': self.service_product.id,
                    'product_uom_qty': 2.0,
                }),
            ],
        })

        wizard_action = sale_order.action_create_stock_reservation()
        wizard_lines = wizard_action['context']['default_stock_reservation_ids']
        self.assertEqual(len(wizard_lines), 1,
                         "Service product lines should be excluded from stock reservation.")

        wizard = self.env['sale.stock.reservation'].with_context(
            **wizard_action['context']
        ).create({})

        # Test partial reservation
        wizard.stock_reservation_ids[0].reserve_quantity = 4.0
        wizard.action_reserve_stock()

        reserved_line = sale_order.reserved_stock_ids[0]
        self.assertEqual(reserved_line.reserved_quantity, 4.0,
                         "Reserved quantity should reflect partial reservation entered.")

        warning_chatter = sale_order.message_ids.filtered(
            lambda m: "no email address configured" in (m.body or '')
        )
        self.assertTrue(warning_chatter,
                        "A chatter warning should be posted when partner has no email.")

        # Test available quantity check (exceeding available stock)
        so_excess = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id,
            'apply_stock_reservation': True,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 500.0,
            })],
        })
        excess_action = so_excess.action_create_stock_reservation()
        excess_wizard = self.env['sale.stock.reservation'].with_context(
            **excess_action['context']
        ).create({})
        with self.assertRaises(UserError):
            excess_wizard.action_reserve_stock()

        # Test wizard without linked sale order
        empty_wizard = self.env['sale.stock.reservation'].create({})
        with self.assertRaises(UserError):
            empty_wizard.action_reserve_stock()
