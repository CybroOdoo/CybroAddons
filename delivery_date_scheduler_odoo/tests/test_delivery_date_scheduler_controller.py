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
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo
from odoo import fields
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase

from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.delivery_date_scheduler_odoo.controllers.delivery_date_scheduler_odoo import (
    DeliveryDateScheduler,
)


@tagged('post_install', '-at_install')
class TestDeliveryDateSchedulerController(TransactionCase):
    """Unit test cases for DeliveryDateScheduler controller methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_parameter = cls.env['ir.config_parameter'].sudo()
        cls.Controller = DeliveryDateScheduler()

        cls.portal_group = cls.env.ref('base.group_portal')

        # Create Portal User A and associated partner
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Portal Customer A',
            'email': 'portal_a@test.com',
        })
        cls.user_portal_a = cls.env['res.users'].create({
            'name': 'Portal User A',
            'login': 'portal_user_a',
            'email': 'portal_a@test.com',
            'partner_id': cls.partner_a.id,
            'group_ids': [Command.set([cls.portal_group.id])],
        })

        # Create Portal User B and associated partner (for IDOR tests)
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'Portal Customer B',
            'email': 'portal_b@test.com',
        })
        cls.user_portal_b = cls.env['res.users'].create({
            'name': 'Portal User B',
            'login': 'portal_user_b',
            'email': 'portal_b@test.com',
            'partner_id': cls.partner_b.id,
            'group_ids': [Command.set([cls.portal_group.id])],
        })

        # Create product for quotations
        cls.product = cls.env['product.product'].create({
            'name': 'Test Delivery Scheduler Product',
            'type': 'consu',
            'list_price': 100.0,
        })

    def setUp(self):
        super().setUp()
        self.config_parameter.search([
            ('key', 'like', 'delivery_date_scheduler_odoo.%')
        ]).unlink()

    def _create_sale_order(self, partner=None, state='sent'):
        """Helper to create a sale order in the given state."""
        partner = partner or self.partner_a
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'require_signature': False,
            'prepayment_percent': 0.0,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
            })],
        })
        if state == 'sent':
            order.action_quotation_sent()
        elif state == 'sale':
            order.action_quotation_sent()
            order.action_confirm()
        elif state == 'cancel':
            order._action_cancel()
        order._portal_ensure_token()
        return order

    # -------------------------------------------------------------------------
    # Tests for _get_delivery_date_range()
    # -------------------------------------------------------------------------

    def test_get_delivery_date_range_warning_disabled(self):
        """Test _get_delivery_date_range when warning_date is False."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', '')

        with MockRequest(self.env):
            warning_date, min_date, max_date = self.Controller._get_delivery_date_range()
            self.assertFalse(warning_date)
            self.assertFalse(min_date)
            self.assertFalse(max_date)

    def test_get_delivery_date_range_warning_enabled(self):
        """Test _get_delivery_date_range when warning_date is True with valid date ranges."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', '5')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '10')

        today = fields.Date.today()
        with MockRequest(self.env):
            warning_date, min_date, max_date = self.Controller._get_delivery_date_range()
            self.assertTrue(warning_date)
            self.assertEqual(min_date, today + timedelta(days=5))
            self.assertEqual(max_date, today + timedelta(days=10))

    def test_get_delivery_date_range_invalid_parameters(self):
        """Test _get_delivery_date_range falls back gracefully when config parameters are non-integer."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', 'invalid_num')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '')

        today = fields.Date.today()
        with MockRequest(self.env):
            warning_date, min_date, max_date = self.Controller._get_delivery_date_range()
            self.assertTrue(warning_date)
            self.assertEqual(min_date, today)
            self.assertEqual(max_date, today)

    # -------------------------------------------------------------------------
    # Tests for delivery_date_schedule()
    # -------------------------------------------------------------------------

    def test_delivery_date_schedule_warning_disabled(self):
        """Test delivery_date_schedule returns error_value 3 when warning_date is disabled."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', '')

        with MockRequest(self.env):
            res = self.Controller.delivery_date_schedule(date='2026-10-25')
            self.assertEqual(res['error_value'], 3)
            self.assertFalse(res['min_date'])
            self.assertFalse(res['max_date'])

    def test_delivery_date_schedule_valid_date_in_range(self):
        """Test delivery_date_schedule returns error_value 1 when date is strictly inside range."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', '3')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '7')

        today = fields.Date.today()
        valid_date_str = (today + timedelta(days=5)).strftime('%Y-%m-%d')
        with MockRequest(self.env):
            res = self.Controller.delivery_date_schedule(date=valid_date_str)
            self.assertEqual(res['error_value'], 1)
            self.assertEqual(res['min_date'], (today + timedelta(days=3)).strftime('%d-%m-%Y'))
            self.assertEqual(res['max_date'], (today + timedelta(days=7)).strftime('%d-%m-%Y'))

    def test_delivery_date_schedule_boundary_dates(self):
        """Test delivery_date_schedule on exact boundary dates (minimum_date and maximum_date)."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', '3')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '7')

        today = fields.Date.today()
        min_date_str = (today + timedelta(days=3)).strftime('%Y-%m-%d')
        max_date_str = (today + timedelta(days=7)).strftime('%Y-%m-%d')

        with MockRequest(self.env):
            # Check minimum date boundary
            res_min = self.Controller.delivery_date_schedule(date=min_date_str)
            self.assertEqual(res_min['error_value'], 1)

            # Check maximum date boundary
            res_max = self.Controller.delivery_date_schedule(date=max_date_str)
            self.assertEqual(res_max['error_value'], 1)

    def test_delivery_date_schedule_date_too_early(self):
        """Test delivery_date_schedule returns error_value 2 when date is earlier than min_date."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', '3')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '7')

        today = fields.Date.today()
        early_date_str = (today + timedelta(days=1)).strftime('%Y-%m-%d')

        with MockRequest(self.env):
            res = self.Controller.delivery_date_schedule(date=early_date_str)
            self.assertEqual(res['error_value'], 2)

    def test_delivery_date_schedule_date_too_late(self):
        """Test delivery_date_schedule returns error_value 2 when date is later than max_date."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', '3')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '7')

        today = fields.Date.today()
        late_date_str = (today + timedelta(days=10)).strftime('%Y-%m-%d')

        with MockRequest(self.env):
            res = self.Controller.delivery_date_schedule(date=late_date_str)
            self.assertEqual(res['error_value'], 2)

    def test_delivery_date_schedule_missing_or_invalid_date(self):
        """Test delivery_date_schedule returns error_value 2 for missing or invalid dates."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', '3')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '7')

        with MockRequest(self.env):
            # Missing date
            res_empty = self.Controller.delivery_date_schedule()
            self.assertEqual(res_empty['error_value'], 2)

            # Invalid date string
            res_invalid = self.Controller.delivery_date_schedule(date='invalid-date-string')
            self.assertEqual(res_invalid['error_value'], 2)

    # -------------------------------------------------------------------------
    # Tests for confirm_delivery_date_schedule()
    # -------------------------------------------------------------------------

    def test_confirm_missing_order_id(self):
        """Test confirm_delivery_date_schedule raises ValidationError when order ID is missing."""
        with MockRequest(self.env(user=self.user_portal_a)):
            with self.assertRaises(ValidationError) as cm:
                self.Controller.confirm_delivery_date_schedule()
            self.assertIn("Order ID is required.", str(cm.exception))

    def test_confirm_invalid_order_id(self):
        """Test confirm_delivery_date_schedule raises ValidationError when order ID is not an integer."""
        with MockRequest(self.env(user=self.user_portal_a)):
            with self.assertRaises(ValidationError) as cm:
                self.Controller.confirm_delivery_date_schedule(id='not_an_id')
            self.assertIn("Invalid order ID.", str(cm.exception))

    def test_confirm_nonexistent_order_id(self):
        """Test confirm_delivery_date_schedule raises MissingError for a nonexistent order ID."""
        with MockRequest(self.env(user=self.user_portal_a)):
            with self.assertRaises(MissingError):
                self.Controller.confirm_delivery_date_schedule(id=99999999)

    def test_confirm_idor_unauthorized_user(self):
        """Test IDOR protection: portal user B cannot confirm portal user A's quotation without access token."""
        order_a = self._create_sale_order(partner=self.partner_a, state='sent')
        today = fields.Date.today()
        date_str = (today + timedelta(days=5)).strftime('%Y-%m-%d')

        with MockRequest(self.env(user=self.user_portal_b)):
            with self.assertRaises(AccessError):
                self.Controller.confirm_delivery_date_schedule(
                    id=order_a.id,
                    date=date_str,
                )

    def test_confirm_with_valid_access_token(self):
        """Test confirming quotation with valid access_token succeeds even across users."""
        order_a = self._create_sale_order(partner=self.partner_a, state='sent')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', '')

        today = fields.Date.today()
        delivery_date = today + timedelta(days=4)
        date_str = delivery_date.strftime('%Y-%m-%d')

        with MockRequest(self.env(user=self.user_portal_b)):
            res = self.Controller.confirm_delivery_date_schedule(
                id=order_a.id,
                access_token=order_a.access_token,
                date=date_str,
                description='Customer note via token',
            )
            self.assertTrue(res)
            self.assertEqual(order_a.state, 'sale')
            self.assertEqual(order_a.commitment_date.date(), delivery_date)
            self.assertEqual(order_a.user_description, 'Customer note via token')

    def test_confirm_order_not_in_sent_state(self):
        """Test confirm_delivery_date_schedule rejects orders that are not in 'sent' state."""
        today = fields.Date.today()
        date_str = (today + timedelta(days=5)).strftime('%Y-%m-%d')

        # Draft quotation
        order_draft = self._create_sale_order(partner=self.partner_a, state='draft')
        with MockRequest(self.env(user=self.user_portal_a)):
            with self.assertRaises(ValidationError) as cm:
                self.Controller.confirm_delivery_date_schedule(id=order_draft.id, date=date_str)
            self.assertIn("Only sent quotations can be confirmed.", str(cm.exception))

        # Already confirmed order
        order_sale = self._create_sale_order(partner=self.partner_a, state='sale')
        with MockRequest(self.env(user=self.user_portal_a)):
            with self.assertRaises(ValidationError) as cm:
                self.Controller.confirm_delivery_date_schedule(id=order_sale.id, date=date_str)
            self.assertIn("Only sent quotations can be confirmed.", str(cm.exception))

    def test_confirm_missing_or_invalid_delivery_date(self):
        """Test confirm_delivery_date_schedule rejects missing or malformed delivery dates."""
        order = self._create_sale_order(partner=self.partner_a, state='sent')

        with MockRequest(self.env(user=self.user_portal_a)):
            # Missing date
            with self.assertRaises(ValidationError) as cm_missing:
                self.Controller.confirm_delivery_date_schedule(id=order.id)
            self.assertIn("Please provide a delivery date.", str(cm_missing.exception))

            # Invalid date format
            with self.assertRaises(ValidationError) as cm_invalid:
                self.Controller.confirm_delivery_date_schedule(id=order.id, date='bad-date-format')
            self.assertIn("Invalid delivery date format.", str(cm_invalid.exception))

    def test_confirm_date_out_of_range(self):
        """Test confirm_delivery_date_schedule rejects dates outside configured min/max range."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', '3')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '7')

        today = fields.Date.today()
        order = self._create_sale_order(partner=self.partner_a, state='sent')

        with MockRequest(self.env(user=self.user_portal_a)):
            # Date before minimum
            early_date_str = (today + timedelta(days=1)).strftime('%Y-%m-%d')
            with self.assertRaises(ValidationError) as cm_early:
                self.Controller.confirm_delivery_date_schedule(id=order.id, date=early_date_str)
            self.assertIn("The delivery date must be within", str(cm_early.exception))

            # Date after maximum
            late_date_str = (today + timedelta(days=10)).strftime('%Y-%m-%d')
            with self.assertRaises(ValidationError) as cm_late:
                self.Controller.confirm_delivery_date_schedule(id=order.id, date=late_date_str)
            self.assertIn("The delivery date must be within", str(cm_late.exception))

    def test_confirm_success_warning_enabled(self):
        """Test successful confirmation when warning_date is enabled and valid date is supplied."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', '3')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '7')

        today = fields.Date.today()
        delivery_date = today + timedelta(days=5)
        date_str = delivery_date.strftime('%Y-%m-%d')
        order = self._create_sale_order(partner=self.partner_a, state='sent')

        with MockRequest(self.env(user=self.user_portal_a)):
            res = self.Controller.confirm_delivery_date_schedule(
                id=order.id,
                date=date_str,
                description='Ring doorbell on arrival',
            )
            self.assertTrue(res)
            self.assertEqual(order.state, 'sale')
            self.assertEqual(order.commitment_date.date(), delivery_date)
            self.assertEqual(order.user_description, 'Ring doorbell on arrival')

    def test_confirm_success_warning_disabled(self):
        """Test successful confirmation when warning_date is disabled (any valid date accepted)."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', '')

        today = fields.Date.today()
        delivery_date = today + timedelta(days=30)
        date_str = delivery_date.strftime('%Y-%m-%d')
        order = self._create_sale_order(partner=self.partner_a, state='sent')

        with MockRequest(self.env(user=self.user_portal_a)):
            res = self.Controller.confirm_delivery_date_schedule(
                id=order.id,
                date=date_str,
                description='Long-term future delivery',
            )
            self.assertTrue(res)
            self.assertEqual(order.state, 'sale')
            self.assertEqual(order.commitment_date.date(), delivery_date)
            self.assertEqual(order.user_description, 'Long-term future delivery')

    def test_confirm_order_expired(self):
        """Test confirm_delivery_date_schedule rejects expired quotations."""
        order = self._create_sale_order(partner=self.partner_a, state='sent')
        order.write({'validity_date': fields.Date.today() - timedelta(days=1)})
        self.assertTrue(order.is_expired, "Order must be expired")
        today = fields.Date.today()
        date_str = (today + timedelta(days=5)).strftime('%Y-%m-%d')

        with MockRequest(self.env(user=self.user_portal_a)):
            with self.assertRaises(ValidationError) as cm:
                self.Controller.confirm_delivery_date_schedule(id=order.id, date=date_str)
            self.assertIn("This quotation has expired and cannot be confirmed.", str(cm.exception))

    def test_confirm_order_requires_signature(self):
        """Test confirm_delivery_date_schedule rejects quotations requiring online signature."""
        order = self._create_sale_order(partner=self.partner_a, state='sent')
        order.write({'require_signature': True, 'signature': False})
        self.assertTrue(order._has_to_be_signed(), "Order must require signature")
        today = fields.Date.today()
        date_str = (today + timedelta(days=5)).strftime('%Y-%m-%d')

        with MockRequest(self.env(user=self.user_portal_a)):
            with self.assertRaises(ValidationError) as cm:
                self.Controller.confirm_delivery_date_schedule(id=order.id, date=date_str)
            self.assertIn("requires a signature before confirmation.", str(cm.exception))

    def test_confirm_order_requires_payment(self):
        """Test confirm_delivery_date_schedule rejects quotations requiring online payment."""
        # Case 1: Order with require_signature=False and prepayment required
        order = self._create_sale_order(partner=self.partner_a, state='sent')
        order.write({'prepayment_percent': 1.0})
        self.assertFalse(order._has_to_be_signed(), "Order should not require signature")
        self.assertTrue(order._has_to_be_paid(), "Order must trigger _has_to_be_paid")

        today = fields.Date.today()
        date_str = (today + timedelta(days=5)).strftime('%Y-%m-%d')

        with MockRequest(self.env(user=self.user_portal_a)):
            with self.assertRaises(ValidationError) as cm:
                self.Controller.confirm_delivery_date_schedule(id=order.id, date=date_str)
            self.assertIn("requires payment before confirmation.", str(cm.exception))

        # Case 2: Order under default online signature setting that is signed but prepayment is unpaid
        order_signed = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'require_signature': True,
            'signature': 'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAF0lEQVR4nGJxKFrEwMDAxAAGgAAAAP//D+IBWx9K7TUAAAAASUVORK5CYII=',
            'signed_by': 'Portal Customer A',
            'prepayment_percent': 1.0,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
            })],
        })
        order_signed.action_quotation_sent()
        self.assertFalse(order_signed._has_to_be_signed(), "Signed order must not require signature")
        self.assertTrue(order_signed._has_to_be_paid(), "Signed order with prepayment must trigger _has_to_be_paid")

        with MockRequest(self.env(user=self.user_portal_a)):
            with self.assertRaises(ValidationError) as cm_signed:
                self.Controller.confirm_delivery_date_schedule(id=order_signed.id, date=date_str)
            self.assertIn("requires payment before confirmation.", str(cm_signed.exception))

    def test_confirm_commitment_date_timezone_conversion(self):
        """Test that commitment_date is converted from the user's timezone to UTC rather than naive midnight UTC."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', '')
        self.user_portal_a.write({'tz': 'America/New_York'})

        order = self._create_sale_order(partner=self.partner_a, state='sent')
        today = fields.Date.today()
        delivery_date = today + timedelta(days=5)
        date_str = delivery_date.strftime('%Y-%m-%d')

        with MockRequest(self.env(user=self.user_portal_a)):
            res = self.Controller.confirm_delivery_date_schedule(
                id=order.id,
                date=date_str,
            )
            self.assertTrue(res)
            # In America/New_York (EDT UTC-4), midnight 00:00 local time corresponds to 04:00:00 UTC
            expected_utc = datetime.combine(
                delivery_date, time.min, tzinfo=ZoneInfo('America/New_York')
            ).astimezone(UTC).replace(tzinfo=None)
            self.assertEqual(order.commitment_date, expected_utc)


@tagged('post_install', '-at_install')
class TestDeliveryDateSchedulerHttp(HttpCase):
    """Integration test cases for delivery date scheduler HTTP JSON-RPC endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_parameter = cls.env['ir.config_parameter'].sudo()

        cls.portal_group = cls.env.ref('base.group_portal')
        cls.portal_partner = cls.env['res.partner'].create({
            'name': 'HTTP Portal Customer',
            'email': 'http_portal@test.com',
        })
        cls.portal_user = cls.env['res.users'].create({
            'name': 'HTTP Portal User',
            'login': 'http_portal_user',
            'password': 'portal_password',
            'email': 'http_portal@test.com',
            'partner_id': cls.portal_partner.id,
            'group_ids': [Command.set([cls.portal_group.id])],
        })

        cls.product = cls.env['product.product'].create({
            'name': 'HTTP Delivery Product',
            'type': 'consu',
            'list_price': 50.0,
        })

    def test_http_delivery_date_schedule(self):
        """Test /delivery_date_schedule JSON-RPC endpoint over HTTP."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', '2')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '8')

        self.authenticate('http_portal_user', 'portal_password')
        today = fields.Date.today()
        valid_date_str = (today + timedelta(days=4)).strftime('%Y-%m-%d')

        response = self.make_jsonrpc_request(
            '/delivery_date_schedule',
            params={'date': valid_date_str},
        )
        self.assertEqual(response['error_value'], 1)
        self.assertEqual(response['min_date'], (today + timedelta(days=2)).strftime('%d-%m-%Y'))
        self.assertEqual(response['max_date'], (today + timedelta(days=8)).strftime('%d-%m-%Y'))

    def test_http_confirm_delivery_date_schedule(self):
        """Test /confirm_delivery_date_schedule JSON-RPC endpoint over HTTP."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', '')

        order = self.env['sale.order'].create({
            'partner_id': self.portal_partner.id,
            'require_signature': False,
            'prepayment_percent': 0.0,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
            })],
        })
        order.action_quotation_sent()

        self.authenticate('http_portal_user', 'portal_password')
        today = fields.Date.today()
        delivery_date = today + timedelta(days=6)
        date_str = delivery_date.strftime('%Y-%m-%d')

        response = self.make_jsonrpc_request(
            '/confirm_delivery_date_schedule',
            params={
                'id': order.id,
                'date': date_str,
                'description': 'HTTP confirmed delivery',
            },
        )
        self.assertTrue(response)
        self.assertEqual(order.state, 'sale')
        self.assertEqual(order.commitment_date.date(), delivery_date)
        self.assertEqual(order.user_description, 'HTTP confirmed delivery')

    def test_http_delivery_date_schedule_public_visitor(self):
        """Test /delivery_date_schedule JSON-RPC endpoint for unauthenticated public visitor."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', 'True')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.min_date_range', '1')
        self.config_parameter.set_str('delivery_date_scheduler_odoo.max_date_range', '5')

        today = fields.Date.today()
        valid_date_str = (today + timedelta(days=2)).strftime('%Y-%m-%d')

        response = self.make_jsonrpc_request(
            '/delivery_date_schedule',
            params={'date': valid_date_str},
        )
        self.assertEqual(response['error_value'], 1)
        self.assertEqual(response['min_date'], (today + timedelta(days=1)).strftime('%d-%m-%Y'))
        self.assertEqual(response['max_date'], (today + timedelta(days=5)).strftime('%d-%m-%Y'))

    def test_http_confirm_delivery_date_schedule_public_token_visitor(self):
        """Test /confirm_delivery_date_schedule JSON-RPC endpoint for unauthenticated token visitor."""
        self.config_parameter.set_str('delivery_date_scheduler_odoo.warning_date', '')

        order = self.env['sale.order'].create({
            'partner_id': self.portal_partner.id,
            'require_signature': False,
            'prepayment_percent': 0.0,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
            })],
        })
        order.action_quotation_sent()
        order._portal_ensure_token()
        today = fields.Date.today()
        delivery_date = today + timedelta(days=3)
        date_str = delivery_date.strftime('%Y-%m-%d')

        response = self.make_jsonrpc_request(
            '/confirm_delivery_date_schedule',
            params={
                'id': order.id,
                'access_token': order.access_token,
                'date': date_str,
                'description': 'Public token visitor confirmation',
            },
        )
        self.assertTrue(response)
        self.assertEqual(order.state, 'sale')
        self.assertEqual(order.commitment_date.date(), delivery_date)
        self.assertEqual(order.user_description, 'Public token visitor confirmation')

