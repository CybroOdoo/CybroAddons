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
"""Test suite for Sale Recurring module."""
from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleRecurring(TransactionCase):
    """Unit tests for recurring sale order management."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Recurring Customer',
            'email': 'recurring_customer@example.com',
        })
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Recurring Service Item',
            'type': 'service',
            'list_price': 100.0,
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Recurring Consumable Item',
            'type': 'consu',
            'list_price': 50.0,
        })
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Test Recurring Sales User',
            'login': 'test_recurring_user',
            'email': 'test_recurring_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_01_recurring_order_creation_and_sequence(self):
        """Test sequence generation and default field values upon creation."""
        today = fields.Date.today()
        recurring_order = self.env['sale.recurring'].create({
            'title': 'Monthly Maintenance Contract',
            'partner_id': self.partner.id,
            'start_date': today,
        })

        self.assertTrue(recurring_order.name, "Recurring order must receive a sequence name.")
        self.assertNotEqual(recurring_order.name, 'New', "Sequence code should replace 'New'.")
        self.assertTrue(recurring_order.name.startswith('SR'), "Sequence should use prefix 'SR'.")
        self.assertEqual(recurring_order.state, 'running', "Default state should be 'running'.")
        self.assertTrue(recurring_order.active, "Default active status should be True.")
        self.assertEqual(recurring_order.title, 'Monthly Maintenance Contract')
        self.assertEqual(recurring_order.partner_id, self.partner)
        self.assertEqual(recurring_order.start_date, today)
        self.assertFalse(recurring_order.end_date, "End date should default to False when stop_after is 0.")

    def test_02_onchange_start_date_and_stop_after(self):
        """Test _onchange_start_date calculation of end_date."""
        start_date = fields.Date.today()
        recurring = self.env['sale.recurring'].new({
            'start_date': start_date,
            'stop_after': 30,
        })
        recurring._onchange_start_date()
        expected_end_date = start_date + timedelta(days=30)
        self.assertEqual(recurring.end_date, expected_end_date,
                         "End date should equal start_date + stop_after days.")

        # Test when stop_after is reset to 0 or negative
        recurring.stop_after = 0
        recurring._onchange_start_date()
        self.assertFalse(recurring.end_date, "End date should be False when stop_after is 0.")

        recurring.stop_after = -5
        recurring._onchange_start_date()
        self.assertFalse(recurring.end_date, "End date should be False when stop_after is negative.")

    def test_03_recurring_order_lines_and_related_fields(self):
        """Test order lines creation and related field resolution."""
        recurring = self.env['sale.recurring'].create({
            'title': 'Weekly Supplies',
            'partner_id': self.partner.id,
            'start_date': fields.Date.today(),
            'order_line_ids': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 2.0,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 5.0,
                }),
            ],
        })

        self.assertEqual(len(recurring.order_line_ids), 2)
        line_1 = recurring.order_line_ids[0]
        self.assertEqual(line_1.product_id, self.product_1)
        self.assertEqual(line_1.name, self.product_1.name)
        self.assertEqual(line_1.price_unit, self.product_1.list_price)
        self.assertEqual(line_1.product_uom_qty, 2.0)
        self.assertEqual(line_1.order_id, recurring)

        line_2 = recurring.order_line_ids[1]
        self.assertEqual(line_2.product_id, self.product_2)
        self.assertEqual(line_2.name, self.product_2.name)
        self.assertEqual(line_2.price_unit, self.product_2.list_price)
        self.assertEqual(line_2.product_uom_qty, 5.0)

    def test_04_action_create_sale_order_with_lines(self):
        """Test manual creation of sale order from recurring order."""
        recurring = self.env['sale.recurring'].create({
            'title': 'Bi-weekly Cleaning',
            'partner_id': self.partner.id,
            'start_date': fields.Date.today(),
            'order_line_ids': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 3.0,
                }),
            ],
        })

        initial_so_count = self.env['sale.order'].search_count([
            ('recurring_order_id', '=', recurring.id),
        ])
        self.assertEqual(initial_so_count, 0)

        recurring.action_create_sale_order()

        so = self.env['sale.order'].search([
            ('recurring_order_id', '=', recurring.id),
        ])
        self.assertEqual(len(so), 1, "One sale order should have been created.")
        self.assertEqual(so.partner_id, self.partner)
        self.assertEqual(so.recurring_order_id, recurring)
        self.assertEqual(so.state, 'draft')
        self.assertEqual(len(so.order_line), 1)
        self.assertEqual(so.order_line.product_id, self.product_1)
        self.assertEqual(so.order_line.product_uom_qty, 3.0)
        self.assertEqual(so.order_line.price_unit, self.product_1.list_price)
        self.assertEqual(so.order_line.name, self.product_1.name)

    def test_05_action_create_sale_order_without_lines(self):
        """Test that action_create_sale_order does not create an order if lines are empty."""
        recurring = self.env['sale.recurring'].create({
            'title': 'Empty Recurring Order',
            'partner_id': self.partner.id,
            'start_date': fields.Date.today(),
        })

        recurring.action_create_sale_order()
        so_count = self.env['sale.order'].search_count([
            ('recurring_order_id', '=', recurring.id),
        ])
        self.assertEqual(so_count, 0, "No sale order should be created when recurring lines are empty.")

    def test_06_state_transitions_cancel_and_renew(self):
        """Test cancelling and renewing a recurring order."""
        recurring = self.env['sale.recurring'].create({
            'title': 'State Transition Test',
            'partner_id': self.partner.id,
            'start_date': fields.Date.today(),
        })
        self.assertEqual(recurring.state, 'running')

        recurring.action_cancel_recurring_order()
        self.assertEqual(recurring.state, 'cancelled')

        recurring.action_renew()
        self.assertEqual(recurring.state, 'running')

    def test_07_archive_and_unarchive_orders(self):
        """Test archiving and unarchiving a recurring order."""
        recurring = self.env['sale.recurring'].create({
            'title': 'Archive Test',
            'partner_id': self.partner.id,
            'start_date': fields.Date.today(),
        })
        self.assertTrue(recurring.active)

        recurring.action_archive_orders()
        self.assertFalse(recurring.active)

        recurring.action_unarchive_orders()
        self.assertTrue(recurring.active)

    def test_08_smart_buttons_and_counts(self):
        """Test computed totals for quotations and confirmed orders, as well as window actions."""
        recurring = self.env['sale.recurring'].create({
            'title': 'Smart Button Test',
            'partner_id': self.partner.id,
            'start_date': fields.Date.today(),
            'order_line_ids': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1.0,
                }),
            ],
        })

        recurring.action_create_sale_order()
        recurring._compute_total_sale_quotation()
        recurring._compute_total_sale_order()
        self.assertEqual(recurring.total_sale_quotation, 1)
        self.assertEqual(recurring.total_sale_order, 0)

        # Confirm the quotation
        so = self.env['sale.order'].search([
            ('recurring_order_id', '=', recurring.id),
        ], limit=1)
        so.action_confirm()

        recurring._compute_total_sale_quotation()
        recurring._compute_total_sale_order()
        self.assertEqual(recurring.total_sale_quotation, 0)
        self.assertEqual(recurring.total_sale_order, 1)

        # Check action_get_sale_orders
        orders_action = recurring.action_get_sale_orders()
        self.assertEqual(orders_action.get('type'), 'ir.actions.act_window')
        self.assertEqual(orders_action.get('res_model'), 'sale.order')
        self.assertIn(('recurring_order_id', '=', recurring.id), orders_action.get('domain', []))
        self.assertIn(('state', '=', 'sale'), orders_action.get('domain', []))

        # Check action_get_sale_quotations
        quotations_action = recurring.action_get_sale_quotations()
        self.assertEqual(quotations_action.get('type'), 'ir.actions.act_window')
        self.assertEqual(quotations_action.get('res_model'), 'sale.order')
        self.assertIn(('recurring_order_id', '=', recurring.id), quotations_action.get('domain', []))
        self.assertIn(('state', 'in', ['draft', 'sent']), quotations_action.get('domain', []))

    def test_09_cron_sale_order_creation(self):
        """Test automated sale order creation cron under multiple conditions."""
        today = fields.Date.today()

        # Case 1: Running order with start_date <= today and end_date in future -> creates SO
        order_valid = self.env['sale.recurring'].create({
            'title': 'Valid Active Recurring',
            'partner_id': self.partner.id,
            'start_date': today - timedelta(days=5),
            'stop_after': 20,
            'end_date': today + timedelta(days=15),
            'order_line_ids': [(0, 0, {'product_id': self.product_1.id, 'product_uom_qty': 1})],
        })

        # Case 2: Running order with no end_date and start_date <= today -> creates SO
        order_no_end = self.env['sale.recurring'].create({
            'title': 'No End Date Recurring',
            'partner_id': self.partner.id,
            'start_date': today - timedelta(days=2),
            'stop_after': 0,
            'end_date': False,
            'order_line_ids': [(0, 0, {'product_id': self.product_2.id, 'product_uom_qty': 2})],
        })

        # Case 3: Expired order (end_date < today) -> transitions state to 'expired', no SO created
        order_expired = self.env['sale.recurring'].create({
            'title': 'Past End Date Recurring',
            'partner_id': self.partner.id,
            'start_date': today - timedelta(days=20),
            'stop_after': 10,
            'end_date': today - timedelta(days=10),
            'order_line_ids': [(0, 0, {'product_id': self.product_1.id, 'product_uom_qty': 1})],
        })

        # Case 4: Future order (start_date > today) -> no SO created
        order_future = self.env['sale.recurring'].create({
            'title': 'Future Recurring',
            'partner_id': self.partner.id,
            'start_date': today + timedelta(days=5),
            'stop_after': 15,
            'end_date': today + timedelta(days=20),
            'order_line_ids': [(0, 0, {'product_id': self.product_1.id, 'product_uom_qty': 1})],
        })

        # Case 5: Cancelled order -> no SO created
        order_cancelled = self.env['sale.recurring'].create({
            'title': 'Cancelled Recurring',
            'partner_id': self.partner.id,
            'start_date': today - timedelta(days=1),
            'state': 'cancelled',
            'order_line_ids': [(0, 0, {'product_id': self.product_1.id, 'product_uom_qty': 1})],
        })

        # Execute the cron job method
        self.env['sale.recurring'].cron_sale_order_creation()

        # Check results
        so_valid = self.env['sale.order'].search([('recurring_order_id', '=', order_valid.id)])
        self.assertEqual(len(so_valid), 1, "Valid active order should have created 1 sale order.")

        so_no_end = self.env['sale.order'].search([('recurring_order_id', '=', order_no_end.id)])
        self.assertEqual(len(so_no_end), 1, "Order without end date should have created 1 sale order.")

        so_expired = self.env['sale.order'].search([('recurring_order_id', '=', order_expired.id)])
        self.assertEqual(len(so_expired), 0, "Expired order should not create sale order.")
        self.assertEqual(order_expired.state, 'expired', "State should have been transitioned to 'expired'.")

        so_future = self.env['sale.order'].search([('recurring_order_id', '=', order_future.id)])
        self.assertEqual(len(so_future), 0, "Future order should not create sale order.")

        so_cancelled = self.env['sale.order'].search([('recurring_order_id', '=', order_cancelled.id)])
        self.assertEqual(len(so_cancelled), 0, "Cancelled order should not create sale order.")

    def test_10_security_access_rights(self):
        """Test CRUD operations for internal users."""
        rec_as_user = self.env['sale.recurring'].with_user(self.internal_user)

        # Create
        new_order = rec_as_user.create({
            'title': 'Internal User Recurring',
            'partner_id': self.partner.id,
            'start_date': fields.Date.today(),
            'order_line_ids': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1.0,
                }),
            ],
        })
        self.assertTrue(new_order.id)

        # Read
        read_data = new_order.read(['title', 'partner_id', 'state'])
        self.assertEqual(read_data[0]['title'], 'Internal User Recurring')

        # Write
        new_order.write({'title': 'Updated Title'})
        self.assertEqual(new_order.title, 'Updated Title')

        # Delete
        order_line = new_order.order_line_ids
        order_line.unlink()
        self.assertFalse(new_order.order_line_ids)

        new_order.unlink()
        self.assertFalse(rec_as_user.search([('id', '=', new_order.id)]))
